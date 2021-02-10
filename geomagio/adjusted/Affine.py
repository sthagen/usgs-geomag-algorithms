from functools import reduce
import numpy as np
from obspy import UTCDateTime
from pydantic import BaseModel
from typing import List, Optional, Tuple

from .. import pydantic_utcdatetime
from ..residual.Reading import (
    Reading,
    get_absolutes_xyz,
    get_baselines,
    get_ordinates,
)
from .AdjustedMatrix import AdjustedMatrix

from .transform import RotationTranslationXY, TranslateOrigins, Transform


class Affine(BaseModel):
    """Creates AdjustedMatrix objects from readings

    Attributes
    ----------
    observatory: 3-letter observatory code
    starttime: beginning time for matrix creation
    endtime: end time for matrix creation
    acausal: when True, utilizes readings from after set endtime
    update_interval: window of time a matrix is representative of
    transforms: list of methods for matrix calculations
    """

    observatory: str = None
    starttime: UTCDateTime = UTCDateTime() - (86400 * 7)
    endtime: UTCDateTime = UTCDateTime()
    update_interval: Optional[int] = 86400 * 7
    transforms: List[Transform] = [
        RotationTranslationXY(memory=(86400 * 100), acausal=True),
        TranslateOrigins(memory=(86400 * 10), acausal=True),
    ]

    class Config:
        arbitrary_types_allowed = True

    def calculate(
        self, readings: List[Reading], epochs: Optional[List[UTCDateTime]] = None
    ) -> List[AdjustedMatrix]:
        """Calculates affine matrices for a range of times

        Attributes
        ----------
        readings: list of readings containing absolutes

        Outputs
        -------
        Ms: list of AdjustedMatrix objects created from calculations
        """
        # default set to create one matrix between starttime and endtime
        update_interval = self.update_interval or (self.endtime - self.starttime)
        all_readings = [r for r in readings if r.valid]
        Ms = []
        time = self.starttime
        # search for "bad" H values
        epochs = epochs or [
            r.time for r in all_readings if r.get_absolute("H").absolute == 0
        ]
        while time < self.endtime:
            # update epochs for current time
            epoch_start, epoch_end = get_epochs(epochs=epochs, time=time)
            # utilize readings that occur after or before a bad reading
            readings = [
                r
                for r in all_readings
                if (epoch_start is None or r.time > epoch_start)
                or (epoch_end is None or r.time < epoch_end)
            ]
            M = self.calculate_matrix(time, readings)
            # if readings are trimmed by bad data, mark the vakid interval
            if M:
                M.starttime = epoch_start
                M.endtime = epoch_end
            time += update_interval

            Ms.append(M)

        return Ms

    def calculate_matrix(
        self, time: UTCDateTime, readings: List[Reading]
    ) -> AdjustedMatrix:
        """Calculates affine matrix for a given time

        Attributes
        ----------
        time: time within calculation interval
        readings: list of valid readings

        Outputs
        -------
        AdjustedMatrix object containing result
        """
        absolutes = get_absolutes_xyz(readings)
        baselines = get_baselines(readings)
        ordinates = get_ordinates(readings)
        times = get_times(readings)
        Ms = []
        weights = []
        inputs = ordinates

        for transform in self.transforms:
            weights = transform.get_weights(
                time=time.timestamp,
                times=times,
            )
            # zero out statistically 'bad' baselines
            weights = filter_iqrs(multiseries=baselines, weights=weights)
            # return None if no valid observations
            if np.sum(weights) == 0:
                return AdjustedMatrix(time=time)

            M = transform.calculate(
                ordinates=inputs, absolutes=absolutes, weights=weights
            )

            # apply latest M matrix to inputs to get intermediate inputs
            inputs = np.dot(
                M, np.vstack([inputs[0], inputs[1], inputs[2], np.ones_like(inputs[0])])
            )[0:3]
            Ms.append(M)

        # compose affine transform matrices using reverse ordered matrices
        M_composed = reduce(np.dot, np.flipud(Ms))
        pier_correction = np.average(
            [reading.pier_correction for reading in readings], weights=weights
        )
        matrix = AdjustedMatrix(
            matrix=M_composed,
            pier_correction=pier_correction,
        )
        matrix.metrics = matrix.get_metrics(readings=readings)
        return matrix


def filter_iqr(
    series: List[float], threshold: int = 3.0, weights: List[int] = None
) -> List[int]:
    """
    Identify "good" elements in series by calculating potentially weighted
    25%, 50% (median), and 75% quantiles of series, the number of 25%-50%
    quantile ranges below, or 50%-75% quantile ranges above each value of
    series falls from the median, and finally, setting elements of good to
    True that fall within these multiples of quantile ranges.

    NOTE: NumPy has a percentile function, but it does not yet handle
          weights. This algorithm was adapted from the PyPI
          package wquantiles (https://pypi.org/project/wquantiles/)

    Inputs:
    series: array of observations to filter

    Options:
    threshold: threshold in fractional number of 25%-50% (50%-75%)
                quantile ranges below (above) the median each element of
                series may fall and still be considered "good"
                Default set to 6.
    weights: weights to assign to each element of series. Default set to 1.

    Output:
    good: Boolean array where True values correspond to "good" data

    """

    if weights is None:
        weights = np.ones_like(series)

    # initialize good as all True for weights greater than 0
    good = (weights > 0).astype(bool)
    if np.size(good) <= 1:
        # if a singleton is passed, assume it is "good"
        return good

    good_old = ~good
    while not (good_old == good).all():
        good_old = good

        wq25 = weighted_quartile(series[good], weights[good], 0.25)
        wq50 = weighted_quartile(series[good], weights[good], 0.50)
        wq75 = weighted_quartile(series[good], weights[good], 0.75)

        # NOTE: it is necessary to include good on the RHS here
        #       to prevent oscillation between two equally likely
        #       "optimal" solutions; this is a common problem with
        #       expectation maximization algorithms
        good = (
            good
            & (series >= (wq50 - threshold * (wq50 - wq25)))
            & (series <= (wq50 + threshold * (wq75 - wq50)))
        )

    return good


def filter_iqrs(
    multiseries: List[List[float]],
    weights: List[float],
    threshold: float = 3.0,
) -> List[float]:
    """Filters "bad" weights generated by unreliable readings"""
    good = None
    for series in multiseries:
        filtered = filter_iqr(series, threshold=threshold, weights=weights)
        if good is None:
            good = filtered
        else:
            good = good & filtered

    return weights * good


def get_epochs(
    epochs: List[float],
    time: UTCDateTime,
) -> Tuple[float, float]:
    """Updates valid start/end time for a given interval

    Attributes
    ----------
    epoch_start: float value signifying start of last valid interval
    epoch_end: float value signifying end of last valid interval
    epochs: list of floats signifying bad data times
    time: current time epoch is being evaluated at

    Outputs
    -------
    epoch_start: float value signifying start of current valid interval
    epoch_end: float value signifying end of current valid interval
    """
    epoch_start = None
    epoch_end = None
    for e in epochs:
        if e > time:
            if epoch_end is None or e < epoch_end:
                epoch_end = e
        if e < time:
            if epoch_start is None or e > epoch_start:
                epoch_start = e
    return epoch_start, epoch_end


def get_times(readings: List[UTCDateTime]):
    return np.array([reading.get_absolute("H").endtime for reading in readings])


def weighted_quartile(data: List[float], weights: List[float], quant: float) -> float:
    """Get weighted quartile to determine statistically good/bad data

    Attributes
    ----------
    data: filtered array of observations
    weights: array of vector distances/metrics
    quant: statistical percentile of input data
    """
    # sort data and weights
    ind_sorted = np.argsort(data)
    sorted_data = data[ind_sorted]
    sorted_weights = weights[ind_sorted]
    # compute auxiliary arrays
    Sn = np.cumsum(sorted_weights)
    Pn = (Sn - 0.5 * sorted_weights) / Sn[-1]
    # interpolate to weighted quantile
    return np.interp(quant, Pn, sorted_data)
