from datetime import datetime
from functools import reduce
import numpy as np
from obspy.core import UTCDateTime
import scipy.linalg as spl
from typing import List

from ..residual import WebAbsolutesFactory, Reading, MeasurementType
from .Affine import Affine
from .GeneratorType import generate_affine_0


def calculate(
    affine: Affine,
    readings: List[Reading],
):
    utc_list, M_composed_list, pcwa_list = do_it_all(
        affine=affine,
        readings=readings,
    )

    return (utc_list, M_composed_list, pcwa_list)


def retrieve_baselines_webasolutes(
    readings: List[Reading],
):
    starttime = readings[0][MeasurementType.WEST_DOWN][0].time
    last_epoch = starttime.timestamp

    # initialize observation lists
    h_abs = []
    d_abs = []
    z_abs = []
    h_bas = []
    d_bas = []
    z_bas = []
    h_t = []
    d_t = []
    z_t = []
    pc = []
    for reading in readings:
        # extract only complete and validated baseline sets; also,
        # filter on reading 'end' times to partially address issues
        # with database time stamps
        if (
            reading.__getabsolute__("H").valid == True
            and reading.__getabsolute__("D").valid == True
            and reading.__getabsolute__("Z").valid == True
        ):

            h_abs.append(reading.__getabsolute__("H").absolute)
            d_abs.append(reading.__getabsolute__("D").absolute)
            z_abs.append(reading.__getabsolute__("Z").absolute)

            h_bas.append(reading.__getabsolute__("H").baseline)
            d_bas.append(reading.__getabsolute__("D").baseline)
            z_bas.append(reading.__getabsolute__("Z").baseline)

            h_t.append(reading.__getabsolute__("H").endtime)
            d_t.append(reading.__getabsolute__("D").endtime)
            z_t.append(reading.__getabsolute__("Z").endtime)

            pc.append(reading.metadata["pier_correction"])

        # the following is a kludge where zero-amplitude horizontal field
        # serves as a "flag" for when observatory change was significant
        # enough to discard all previous absolute measurements
        if reading.__getabsolute__("H").absolute == 0:
            last_epoch = max(reading.__getabsolute__("H").endtime, last_epoch)

    # print message about modified magnetometer
    if last_epoch != starttime.timestamp:
        print(
            "Magnetometer altered, discarding measurements prior to %s"
            % datetime.utcfromtimestamp(last_epoch)
        )

    # convert lists to NumPy arrays
    h_abs = np.array(h_abs)
    d_abs = np.array(d_abs)
    z_abs = np.array(z_abs)
    h_bas = np.array(h_bas)
    d_bas = np.array(d_bas)
    z_bas = np.array(z_bas)
    pc = np.array(pc)

    # convert epochs to UTCDateTimes
    h_utc = np.array([UTCDateTime(t) for t in h_t])
    d_utc = np.array([UTCDateTime(t) for t in d_t])
    z_utc = np.array([UTCDateTime(t) for t in z_t])

    # only return data more recent than last_epoch
    good = (h_utc > last_epoch) & (d_utc > last_epoch) & (z_utc > last_epoch)
    h_abs = h_abs[good]
    d_abs = d_abs[good]
    z_abs = z_abs[good]
    h_bas = h_bas[good]
    d_bas = d_bas[good]
    z_bas = z_bas[good]
    pc = pc[good]
    h_utc = h_utc[good]

    # return data arrays
    return ((h_abs, h_bas), (d_abs, d_bas), (z_abs, z_bas), pc, h_utc)


def time_weights_exponential(times, memory, epoch: int = None):
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
    dist - an M element array of vector distances/metrics

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


def weighted_quartile(data, weights, quant):
    # sort data and weights
    ind_sorted = np.argsort(data)
    sorted_data = data[ind_sorted]
    sorted_weights = weights[ind_sorted]
    # compute auxiliary arrays
    Sn = np.cumsum(sorted_weights)
    Pn = (Sn - 0.5 * sorted_weights) / Sn[-1]
    # interpolate to weighted quantile
    return np.interp(quant, Pn, sorted_data)


def filter_iqr(series: List[float], threshold=6, weights=None):
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


def do_one(
    weights: List[float],
    Ms: List[List[float]],
    pcwa: List[float],
    h_bas: float,
    d_bas: float,
    z_bas: float,
    M_func,
    pc: float,
    h_tmp: float,
    e_tmp: float,
    z_tmp: float,
    x_a: float,
    y_a: float,
    z_a: float,
):

    # identify 'good' data indices based on baseline stats
    good = (
        filter_iqr(h_bas, threshold=3, weights=weights[-1])
        & filter_iqr(d_bas, threshold=3, weights=weights[-1])
        & filter_iqr(z_bas, threshold=3, weights=weights[-1])
    )

    # zero out any 'bad' weights
    weights[-1] = good * weights[-1]

    # generate affine transform matrix
    Ms.append(M_func((h_tmp, e_tmp, z_tmp), (x_a, y_a, z_a), weights=weights[-1]))

    # calculate weighted average of pier corrections
    pcwa.append(np.average(pc, weights=weights[-1]))

    # apply latest M matrix to inputs to get intermediate inputs
    h_tmp, e_tmp, z_tmp = np.dot(
        Ms[-1], np.vstack([h_tmp, e_tmp, z_tmp, np.ones_like(h_tmp)])
    )[:3]

    return h_tmp, e_tmp, z_tmp, pcwa, Ms, weights


def do_it_all(
    affine,
    readings,
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

    # use WebAbsolutes web service to retrieve baseline info
    (
        (h_abs, h_bas),
        (d_abs, d_bas),
        (z_abs, z_bas),
        pc,
        utc,
    ) = retrieve_baselines_webasolutes(readings=readings)

    # recreate ordinate variometer measurements from absolutes and baselines
    h_ord = h_abs - h_bas
    d_ord = d_abs - d_bas
    z_ord = z_abs - z_bas

    # convert from cylindrical to Cartesian coordinates
    x_a = h_abs * np.cos(d_abs * np.pi / 180)
    y_a = h_abs * np.sin(d_abs * np.pi / 180)
    z_a = z_abs

    # WebAbsolutes defines/generates h differently than USGS residual
    # method spreadsheets. The following should ensure that ordinate
    # values are converted back to their original raw measurements:
    e_o = h_abs * d_ord * 60 / 3437.7468
    if affine.observatory in ["DED", "CMO"]:
        h_o = np.sqrt(h_ord ** 2 - e_o ** 2)
    else:
        h_o = h_ord
    z_o = z_ord

    # initialize outputs
    utc_list = []
    M_composed_list = []
    pcwa_list = []

    start_UTC = affine.starttime

    # process each update_interval from start_UTC to end_UTC
    while start_UTC < affine.endtime:

        # reset intermediate input values
        h_tmp = h_o
        e_tmp = e_o
        z_tmp = z_o

        # reinitialize weights, Ms and pcwa lists
        weights = []
        Ms = []
        pcwa = []

        # loop over M_funcs and memories to compose affine matrix
        for generator in affine.generators:
            # Calculate time-dependent weights using utc
            weights.append(
                time_weights_exponential(utc, generator.memory, start_UTC.timestamp)
            )

            # set weights for future observations to zero if not acausal
            if not affine.acausal:
                weights[-1][utc > start_UTC] = 0.0

            # return NaNs if no valid observations
            if np.sum(weights[-1]) == 0:
                Ms.append(np.nan * np.zeros((4, 4)))
                pcwa.append(np.nan)
                print("No valid observations for interval")
                continue
            h_tmp, e_tmp, z_tmp, pcwa, Ms, weights = do_one(
                weights=weights,
                Ms=Ms,
                pcwa=pcwa,
                h_bas=h_bas,
                d_bas=d_bas,
                z_bas=z_bas,
                M_func=generator.type.calculate_matrix,
                pc=pc,
                h_tmp=h_tmp,
                e_tmp=e_tmp,
                z_tmp=z_tmp,
                x_a=x_a,
                y_a=y_a,
                z_a=z_a,
            )

        # append Ms, pcwa, and weights used to generate them to lists
        # of outputs for each update_interval
        pcwa_list.append(pcwa)

        # compose affine transform matrices
        M_composed = reduce(np.dot, Ms[::-1])

        # append to list of outputs for each update_interval
        M_composed_list.append(M_composed)

        # append to list of outputs for each update_interval
        utc_list.append(start_UTC)

        # increment start_UTC
        start_UTC += affine.update_interval

    return utc_list, M_composed_list, pcwa_list
