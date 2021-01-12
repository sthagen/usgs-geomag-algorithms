import numpy as np
from functools import reduce
from obspy.core import UTCDateTime
from pydantic import BaseModel
from .. import pydantic_utcdatetime
from typing import List, Any, Optional, Type

from .Transform import Transform, TranslateOrigins, RotationTranslationXY
from .AdjustedMatrix import AdjustedMatrix
from ..residual import Reading


def weighted_quartile(data: List[float], weights: List[float], quant: float) -> float:
    # sort data and weights
    ind_sorted = np.argsort(data)
    sorted_data = data[ind_sorted]
    sorted_weights = weights[ind_sorted]
    # compute auxiliary arrays
    Sn = np.cumsum(sorted_weights)
    Pn = (Sn - 0.5 * sorted_weights) / Sn[-1]
    # interpolate to weighted quantile
    return np.interp(quant, Pn, sorted_data)


def filter_iqr(
    series: List[float], threshold: int = 6, weights: List[int] = None
) -> List[int]:
    """
    Identify "good" elements in series by calculating potentially weighted
    25%, 50% (median), and 75% quantiles of series, the number of 25%-50%
    quantile ranges below, or 50%-75% quantile ranges above each value of
    series falls from the median, and finally, setting elements of good to
    True that fall within these multiples of quantile ranges.

    NOTE: NumPy has a percentile function, but it does not yet handle
          weights. This algorithm was adapted shamelessly from the PyPI
          package wquantiles (https://pypi.org/project/wquantiles/). If
          NumPy should ever implement their own weighted algorithm, we
          should use it instead.

    Inputs:
    series      - 1D NumPy array of observations to filter

    Options:
    threshold   - threshold in fractional number of 25%-50% (50%-75%)
                  quantile ranges below (above) the median each element of
                  series may fall and still be considered "good"
                  (default = 6)
    weights     - weights to assign to each element of series
                  (default = 1)

    Output:
    good        - Boolean array where True values correspond to "good" data

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


def create_states(matrices: List[Any], pier_correction: float) -> List[dict]:
    if matrices is None:
        return []
    states = []
    for matrix in matrices:
        data = {"PC": pier_correction}
        length = len(matrix[0, :])
        for i in range(0, length):
            for j in range(0, length):
                key = "M" + str(i + 1) + str(j + 1)
                data[key] = matrix[i, j]
        states.append(data)
    return states


class Affine(BaseModel):
    observatory: str = None
    starttime: UTCDateTime = UTCDateTime() - (86400 * 7)
    endtime: UTCDateTime = UTCDateTime()
    acausal: bool = False
    update_interval: Optional[int] = 86400 * 7
    transforms: List[Type[Transform]] = [
        RotationTranslationXY(memory=(86400 * 100)),
        TranslateOrigins(memory=(86400 * 10)),
    ]

    def calculate(self, readings: List[Reading]) -> List[AdjustedMatrix]:
        update_interval = self.update_interval or (self.endtime - self.starttime)
        all_readings = [r for r in readings if r.valid]
        Ms = []
        time = self.starttime
        epoch_start = None
        epoch_end = None
        epochs = [r.time for r in all_readings if r.get_absolute("H").absolute == 0]
        while time < self.endtime:
            epoch_start, epoch_end = self.get_epochs(
                epoch_start=epoch_start, epoch_end=epoch_end, epochs=epochs, time=time
            )
            readings = [
                r
                for r in all_readings
                if (epoch_start is None or r.time > epoch_start)
                or (epoch_end is None or r.time < epoch_end)
            ]
            M = self.calculate_matrix(time, readings)
            M.starttime = epoch_start
            M.endtime = epoch_end

            # increment start_UTC
            time += update_interval

            Ms.append(M)

        return Ms

    def get_epochs(
        self,
        epoch_start: float,
        epoch_end: float,
        epochs: List[float],
        time: UTCDateTime,
    ):
        for e in epochs:
            if e > time:
                if epoch_end is None or e < epoch_end:
                    epoch_end = e
            if e < time:
                if epoch_start is None or e > epoch_start:
                    epoch_start = e
        return epoch_start, epoch_end

    def get_times(self, readings: List[UTCDateTime]):
        return np.array([reading.get_absolute("H").endtime for reading in readings])

    def get_ordinates(self, readings: List[Reading]):
        h_abs, d_abs, z_abs = self.get_absolutes(readings)
        h_bas, d_bas, z_bas = self.get_baselines(readings)

        # recreate ordinate variometer measurements from absolutes and baselines
        h_ord = h_abs - h_bas
        d_ord = d_abs - d_bas
        z_ord = z_abs - z_bas

        # WebAbsolutes defines/generates h differently than USGS residual
        # method spreadsheets. The following should ensure that ordinate
        # values are converted back to their original raw measurements:
        e_o = h_abs * d_ord * 60 / 3437.7468
        # TODO: is this handled in residual package?
        if self.observatory in ["DED", "CMO"]:
            h_o = np.sqrt(h_ord ** 2 - e_o ** 2)
        else:
            h_o = h_ord
        z_o = z_ord
        return (h_o, e_o, z_o)

    def get_baselines(self, readings: List[Reading]):
        h_bas = np.array([reading.get_absolute("H").baseline for reading in readings])
        d_bas = np.array([reading.get_absolute("D").baseline for reading in readings])
        z_bas = np.array([reading.get_absolute("Z").baseline for reading in readings])
        return (h_bas, d_bas, z_bas)

    def get_absolutes(self, readings: List[Reading]):
        h_abs = np.array([reading.get_absolute("H").absolute for reading in readings])
        d_abs = np.array([reading.get_absolute("D").absolute for reading in readings])
        z_abs = np.array([reading.get_absolute("Z").absolute for reading in readings])

        return (h_abs, d_abs, z_abs)

    def get_absolutes_xyz(self, readings: List[Reading]):
        h_abs, d_abs, z_abs = self.get_absolutes(readings)

        # convert from cylindrical to Cartesian coordinates
        x_a = h_abs * np.cos(d_abs * np.pi / 180)
        y_a = h_abs * np.sin(d_abs * np.pi / 180)
        z_a = z_abs
        return (x_a, y_a, z_a)

    def calculate_matrix(
        self, time: UTCDateTime, readings: List[Reading]
    ) -> AdjustedMatrix:
        absolutes = self.get_absolutes(readings)
        baselines = self.get_baselines(readings)
        ordinates = self.get_ordinates(readings)
        times = self.get_times(readings)
        Ms = []
        weights = []

        inputs = ordinates

        for transform in self.transforms:
            weights = self.get_weights(
                time=time,
                times=times,
                transform=transform,
            )
            # return NaNs if no valid observations
            if np.sum(weights) == 0:
                raise ValueError(f"No valid observations for {time}")
            # identify 'good' data indices based on baseline stats
            # TODO: return good from filter_iqr, which accepts a list
            good = (
                filter_iqr(baselines[0], threshold=3, weights=weights)
                & filter_iqr(baselines[1], threshold=3, weights=weights)
                & filter_iqr(baselines[2], threshold=3, weights=weights)
            )

            # zero out any 'bad' weights
            weights = good * weights

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
        # TODO: how should pier corrections be averaged?
        pier_correction = np.average(
            [reading.pier_correction for reading in readings], weights=weights
        )

        return AdjustedMatrix(matrix=M_composed, pier_correction=pier_correction)

    def get_weights(
        self,
        time: UTCDateTime,
        times: List[UTCDateTime],
        transform: Transform,
    ):
        times = [t.timestamp for t in times]
        weights = transform.get_weights(time=time.timestamp, times=times)
        # set weights for future observations to zero if not acausal
        if not self.acausal:
            weights[times > time] = 0.0
        return weights
