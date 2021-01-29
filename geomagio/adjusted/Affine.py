from functools import reduce
import numpy as np
from obspy import UTCDateTime
from pydantic import BaseModel
from typing import List, Optional, Tuple

from .AdjustedMatrix import AdjustedMatrix
from .. import ChannelConverter
from .. import pydantic_utcdatetime
from .Metric import Metric
from ..residual import Reading
from .Transform import Transform, TranslateOrigins, RotationTranslationXY


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
    acausal: bool = False
    update_interval: Optional[int] = 86400 * 7
    transforms: List[Transform] = [
        RotationTranslationXY(memory=(86400 * 100)),
        TranslateOrigins(memory=(86400 * 10)),
    ]

    class Config:
        arbitrary_types_allowed = True

    def calculate(self, readings: List[Reading]) -> List[AdjustedMatrix]:
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
        epoch_start = None
        epoch_end = None
        # search for "bad" H values
        epochs = [r.time for r in all_readings if r.get_absolute("H").absolute == 0]
        while time < self.endtime:
            # update epochs for current time
            epoch_start, epoch_end = self.get_epochs(
                epoch_start=epoch_start, epoch_end=epoch_end, epochs=epochs, time=time
            )
            # utilize readings that occur after or before a bad reading
            readings = [
                r
                for r in all_readings
                if (epoch_start is None or r.time > epoch_start)
                or (epoch_end is None or r.time < epoch_end)
            ]
            M = self.calculate_matrix(time, readings)
            # if readings are trimmed by bad data, mark the vakid interval
            M.starttime = epoch_start
            M.endtime = epoch_end
            time += update_interval

            Ms.append(M)

        return Ms

    def get_epochs(
        self,
        epoch_start: float,
        epoch_end: float,
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

    def get_ordinates(
        self, readings: List[Reading]
    ) -> Tuple[List[float], List[float], List[float]]:
        """Calculates ordinates from absolutes and baselines"""
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

    def get_baselines(
        self, readings: List[Reading]
    ) -> Tuple[List[float], List[float], List[float]]:
        """Get H, D and Z baselines"""
        h_bas = np.array([reading.get_absolute("H").baseline for reading in readings])
        d_bas = np.array([reading.get_absolute("D").baseline for reading in readings])
        z_bas = np.array([reading.get_absolute("Z").baseline for reading in readings])
        return (h_bas, d_bas, z_bas)

    def get_absolutes(
        self, readings: List[Reading]
    ) -> Tuple[List[float], List[float], List[float]]:
        """Get H, D and Z absolutes"""
        h_abs = np.array([reading.get_absolute("H").absolute for reading in readings])
        d_abs = np.array([reading.get_absolute("D").absolute for reading in readings])
        z_abs = np.array([reading.get_absolute("Z").absolute for reading in readings])

        return (h_abs, d_abs, z_abs)

    def get_absolutes_xyz(
        self, readings: List[Reading]
    ) -> Tuple[List[float], List[float], List[float]]:
        """Get X, Y and Z absolutes from H, D and Z baselines"""
        h_abs, d_abs, z_abs = self.get_absolutes(readings)

        # convert from cylindrical to Cartesian coordinates
        x_a = h_abs * np.cos(d_abs * np.pi / 180)
        y_a = h_abs * np.sin(d_abs * np.pi / 180)
        z_a = z_abs
        return (x_a, y_a, z_a)

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
        absolutes = self.get_absolutes_xyz(readings)
        baselines = self.get_baselines(readings)
        ordinates = self.get_ordinates(readings)
        times = self.get_times(readings)
        Ms = []
        weights = []
        metrics = []
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
            # zero out statistically 'bad' baselines
            weights = self.weight_baselines(baselines=baselines, weights=weights)

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
        absolutes = np.vstack((absolutes, np.ones_like(absolutes[0])))
        ordinates = np.vstack((ordinates, np.ones_like(ordinates[0])))
        pier_correction = np.average(
            [reading.pier_correction for reading in readings], weights=weights
        )
        std, mae, mae_df, std_df = self.compute_metrics(
            absolutes=absolutes, ordinates=ordinates, matrix=M_composed
        )

        return AdjustedMatrix(
            matrix=M_composed,
            pier_correction=pier_correction,
            metrics=[
                Metric(element="X", mae=mae[0], std=std[0]),
                Metric(element="Y", mae=mae[1], std=std[1]),
                Metric(element="Z", mae=mae[2], std=std[2]),
                Metric(element="dF", mae=mae_df, std=std_df),
            ],
        )

    def compute_metrics(
        self, absolutes: List[float], ordinates: List[float], matrix: List[float]
    ) -> Tuple[List[float], List[float], float, float]:
        """Computes mean absolute error and standard deviation for X, Y, Z, and dF between expected and predicted values.

        Attributes
        ----------
        absolutes: X, Y and Z absolutes
        ordinates: H, E and Z ordinates
        matrix: composed matrix

        Outputs
        -------
        std: standard deviation between expected and predicted XYZ values
        mae: mean absolute error between expected and predicted XYZ values
        std_df: standard deviation of dF computed from expected and predicted XYZ values
        mae_df: mean absolute error of dF computed from expected and predicted XYZ values
        """
        # expected values are absolutes
        predicted = matrix @ ordinates
        # mean absolute erros and standard deviations ignore the 4th row comprison, which is trivial
        std = np.nanstd(predicted - absolutes, axis=1)[0:3]
        mae = abs(np.nanmean(predicted - absolutes, axis=1))[0:3]
        expected_f = ChannelConverter.get_computed_f_using_squares(
            absolutes[0], absolutes[1], absolutes[2]
        )
        predicted_f = ChannelConverter.get_computed_f_using_squares(
            predicted[0], predicted[1], predicted[2]
        )
        df = ChannelConverter.get_deltaf(expected_f, predicted_f)
        std_df = abs(np.nanstd(df))
        mae_df = abs(np.nanmean(df))
        return list(std), list(mae), std_df, mae_df

    def get_weights(
        self,
        time: UTCDateTime,
        times: List[UTCDateTime],
        transform: Transform,
    ) -> np.array:
        """

        Attributes
        ----------
        time: time within calculation interval
        times: times of valid readings
        transform: matrix calculation method

        Outputs
        -------
        weights: array of weights to apply to absolutes/ordinates within calculations
        """

        weights = transform.get_weights(time=time.timestamp, times=times)
        # set weights for future observations to zero if not acausal
        if not self.acausal:
            weights[times > time.timestamp] = 0.0
        return weights

    def weight_baselines(
        self,
        baselines: List[float],
        weights: List[float],
        threshold=3,
    ) -> List[float]:
        """Filters "bad" weights generated by unreliable readings"""
        good = (
            filter_iqr(baselines[0], threshold=threshold, weights=weights)
            & filter_iqr(baselines[1], threshold=threshold, weights=weights)
            & filter_iqr(baselines[2], threshold=threshold, weights=weights)
        )
        return weights * good
