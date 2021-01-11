from functools import reduce
import numpy as np
from typing import List, Tuple

from obspy.core.utcdatetime import UTCDateTime

from ..residual import Reading, MeasurementType
from .Affine import Affine, create_states


def get_good_readings(
    readings: List[Reading],
) -> List[Reading]:
    starttime = readings[0][MeasurementType.WEST_DOWN][0].time
    last_epoch = starttime.timestamp
    filtered_readings = []
    for reading in readings:
        # extract only complete and validated baseline sets; also,
        # filter on reading 'end' times to partially address issues
        # with database time stamps
        if (
            reading.absolutes[1].valid == True
            and reading.get_absolute("H").valid == True
            and reading.absolutes[2].valid
            and (reading.absolutes[0].endtime > last_epoch)
            and (reading.absolutes[1].endtime > last_epoch)
            and (reading.absolutes[2].endtime > last_epoch)
        ):
            if reading.absolutes[1].absolute == 0:
                last_epoch = max(reading.absolutes[1].endtime, last_epoch)
            filtered_readings.append(reading)

    # return data arrays
    return filtered_readings


def time_weights_exponential(
    times: UTCDateTime, memory: float, epoch: int = None
) -> List[float]:
    """
    Calculate time-dependent weights according to exponential decay.

    Inputs:
    times     - 1D array of times, or any time-like index whose
                relative values represent spacing between events
    memory    - exp(-1) time scale; weights will be ~37% of max
                weight when time difference equals memory, and ~5%
                of max weight when time difference is 3X memory

    Options:
    epoch     - time at which weights maximize
                (default = max(times))

    Outout:
    weights - an M element array of vector distances/metrics

    NOTE:  ObsPy UTCDateTime objects can be passed in times, but
           memory must then be specified in seconds
    FIXME: Python datetime objects not supported yet

    """

    # convert to array of floats
    # (allows UTCDateTimes, but not datetime.datetimes)
    times = np.asarray(times).astype(float)

    if epoch is None:
        epoch = float(max(times))

    # if memory is actually infinite, return equal weights
    if np.isinf(memory):
        return np.ones(times.shape)

    # initialize weights
    weights = np.zeros(times.shape)

    # calculate exponential decay time-dependent weights
    weights[times <= epoch] = np.exp((times[times <= epoch] - epoch) / memory)
    weights[times >= epoch] = np.exp((epoch - times[times >= epoch]) / memory)

    return weights


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


def calculate(
    affine: Affine,
    readings: List[Reading],
):
    """
    This function will do the following for a specified obs_code between
    start_UTC and end_UTC, incrementing by update_interval:

    - Read in absolute and baseline data, removing outliers
    - Convert absolutes+baselines back to fluxgate measurements
    - Convert all cylindrical to Cartesian coordinates
    - Estimate memory-weighted Adjusted Data transform matrice(s)
    - Estimate memory-weighted average pier corrections
    - If validate is True, also:
        - Apply Adjusted Data transforms to raw HEZF data
        - Retrieve (quasi-)definitive data for comparisons
        - Generate common time stamps for each update_interval


    INPUTS:
    obs_code        - 3-character IAGA code for observatory
    start_UTC       - beginning date to do stuff (UTCDatetime)
    end_UTC         - final date to do stuff (UTCDatetime)

    OPTIONS:
    update_interval - how often (in seconds) to update the Adjusted matrices
                      (default = end_UTC - start_UTC)
    acausal         - use absolute/ordinate pairs from the future if True
                      (default = False)
                      (default = False)
    first_UTC       - earliest observation date to retrieve
                      (default = start_UTC)
    last_UTC        - latest observation date to retrieve
                      (default = end_UTC)
    M_funcs         - list of function objects used to generate affine matrices
                      given 3D Cartesian vector inputs; compose final Adjusted
                      affine matrix by:
                      1) calculate 1st matrix from inputs->outputs;
                      2) transform initial inputs to intermediate inputs;
                      3) calculate 2nd matrix from intermediate inputs to outputs;
                      4) repeat until all M_funcs used;
                      5) final Adjusted matrix is composition of all in reverse
                      (default = [generate_affine_0])
    memories        - time constant(s) used to calculate weights; memories may be
                      a scalar, or a list with same length as M_funcs
                      (default = np.inf)
    path_or_url     - url for absolutes web service, or path to summary xlsm files
                      (default = 'https://geomag.usgs.gov/')

    OUTPUTS:
    utc_list        - list of first UTCDateTimes for each update_interval
    M_composed_list - list of composed Adjusted Data matrices for each update_interval
    pc_list         - list of pier corrections for each update_interval

    """

    # default update_interval
    if affine.update_interval is None:
        # only one interval from start_UTC to end_UTC
        affine.update_interval = affine.endtime - affine.starttime

    readings = get_good_readings(readings)
    # convert lists to NumPy arrays
    d_abs, d_bas = get_absolutes(readings, "D")
    h_abs, h_bas = get_absolutes(readings, "H")
    z_abs, z_bas = get_absolutes(readings, "Z")
    utc = np.array([reading.absolutes[1].endtime for reading in readings])

    # recreate ordinate variometer measurements from absolutes and baselines
    h_ord = h_abs - h_bas
    d_ord = d_abs - d_bas
    z_ord = z_abs - z_bas

    # WebAbsolutes defines/generates h differently than USGS residual
    # method spreadsheets. The following should ensure that ordinate
    # values are converted back to their original raw measurements:
    e_o = h_abs * d_ord * 60 / 3437.7468
    if affine.observatory in ["DED", "CMO"]:
        h_o = np.sqrt(h_ord ** 2 - e_o ** 2)
    else:
        h_o = h_ord
    z_o = z_ord

    # convert from cylindrical to Cartesian coordinates
    x_a = h_abs * np.cos(d_abs * np.pi / 180)
    y_a = h_abs * np.sin(d_abs * np.pi / 180)
    z_a = z_abs

    M_composed_list = []

    start_UTC = affine.starttime

    # process each update_interval from start_UTC to end_UTC
    while start_UTC < affine.endtime:

        # reset intermediate input values
        h_tmp = h_o
        e_tmp = e_o
        z_tmp = z_o
        Ms = []

        # loop over M_funcs and memories to compose affine matrix
        for generator in affine.generators:
            # Calculate time-dependent weights using utc
            weights = time_weights_exponential(
                utc, generator.memory, start_UTC.timestamp
            )

            # set weights for future observations to zero if not acausal
            if not affine.acausal:
                weights[utc > start_UTC] = 0.0

            # return NaNs if no valid observations
            if np.sum(weights) == 0:
                Ms.append(np.nan * np.zeros((4, 4)))
                print("No valid observations for interval")
                continue
            # identify 'good' data indices based on baseline stats
            good = (
                filter_iqr(h_bas, threshold=3, weights=weights)
                & filter_iqr(d_bas, threshold=3, weights=weights)
                & filter_iqr(z_bas, threshold=3, weights=weights)
            )

            # zero out any 'bad' weights
            weights = good * weights

            M = generator.type.calculate_matrix(
                (h_tmp, e_tmp, z_tmp), (x_a, y_a, z_a), weights=weights
            )

            # apply latest M matrix to inputs to get intermediate inputs
            h_tmp, e_tmp, z_tmp, __ = np.dot(
                M, np.vstack([h_tmp, e_tmp, z_tmp, np.ones_like(h_tmp)])
            )

            # generate affine transform matrix
            Ms.append(M)

        affine.pier_correction = np.average(
            [reading.pier_correction for reading in readings], weights=weights
        )

        # compose affine transform matrices using reverse ordered matrices
        M_composed = reduce(np.dot, np.flipud(Ms))

        # append to list of outputs for each update_interval
        M_composed_list.append(M_composed)

        # increment start_UTC
        start_UTC += affine.update_interval

    affine.matrices = M_composed_list
    affine.states = create_states(affine.matrices, affine.pier_correction)
