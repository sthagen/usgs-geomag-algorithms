from functools import reduce
import os

import fnmatch
from datetime import datetime
from datetime import timedelta
import json
import numpy as np
from numpy.testing import assert_equal
from obspy.core import UTCDateTime
from openpyxl import load_workbook
import pickle
from scipy.interpolate import interp1d
import scipy.linalg as spl
from scipy.spatial.transform import Rotation
from scipy.spatial.transform import Slerp
from typing import List
import urllib

from geomagio.edge import EdgeFactory
from geomagio.residual import WebAbsolutesFactory


def retrieve_baselines_resid_summary_xlsm(
    obs_code, start_date, end_date, path_or_url="./"
):
    """
    Retrieve baselines from USGS Geomag residual method summary Excel
    spreadsheets on local file system. This is a very simple data reader
    that assumes a fixed filename convention, and a fixed template for
    the summary spreadsheet.

    Inputs:
    obs_code    - 3-character IAGA code for observatory
    start_date  - UTCDatetime for start of interval
    end_date    - UTCDatetime for end of interval
    path_or_url - folder in which to find .xlsm files

    Outout:
    h_abs_bas_utc - array holding vectors of h_abs, h_bas, and h_utc
    d_abs_bas_utc - array holding vectors of d_abs, d_bas, and d_utc
    z_abs_bas_utc - array holding vectors of z_abs, z_bas, and z_utc
    pc            - array holding pier corrections
    """

    # some default inputs
    if end_date is None:
        end_date = UTCDateTime.now()

    if start_date is None:
        start_date = UTCDateTime(0)

    # initialize outputs
    h_abs = []
    h_bas = []
    h_dt = []

    d_abs = []
    d_bas = []
    d_dt = []

    z_abs = []
    z_bas = []
    z_dt = []

    pc = []

    # openpyxl uses Python datetime objects
    start_dt = start_date.datetime
    end_dt = end_date.datetime
    last_dt = start_dt

    # loop over all [obs_code]??????????.xlsm files in all folders under path_or_url
    for root, dirnames, filenames in os.walk(path_or_url + "/" + obs_code.upper()):
        for filename in fnmatch.filter(
            filenames, obs_code.upper() + "???????????.xlsm"
        ):

            # load workbook
            # (data_only=True forces openpyxl to read in data saved in
            #  a cell, even if the cell is actually a formula; if False,
            #  openpyxl would return the formuala; openpyxl NEVER evaluates
            #  a formula, it relies on values generated and cached by the
            #  spreadsheet program itself)
            wb = load_workbook(os.path.join(root, filename), data_only=True)

            # get worksheet 1
            ws1 = wb["Sheet1"]

            # get date (pyxl retrieves as datetime object)
            date = ws1["I1"].value

            # these spreadsheet files must have a particular layout; if there is
            # any problem reading in data, just skip the whole file
            try:

                # (re)initialize valid list
                valid = [True, True, True, True]

                # get and convert declination times
                d_time_str = [
                    "%04i" % ws1["B10"].value,
                    "%04i" % ws1["B11"].value,
                    "%04i" % ws1["B12"].value,
                    "%04i" % ws1["B13"].value,
                ]
                d_time_delta = [
                    timedelta(hours=int(s[0:2])) + timedelta(minutes=int(s[2:4]))
                    for s in d_time_str
                ]
                d_datetime = [date + td for td in d_time_delta]

                # get and convert declination absolute fractional angles
                d_absolute = [
                    [float(ws1["C10"].value), float(ws1["D10"].value)],
                    [float(ws1["C11"].value), float(ws1["D11"].value)],
                    [float(ws1["C12"].value), float(ws1["D12"].value)],
                    [float(ws1["C13"].value), float(ws1["D13"].value)],
                ]
                d_absolute = [d + m / 60 for d, m in d_absolute if m is not None]

                # get and convert declination baseline fractional angles
                d_baseline = [
                    float(ws1["H10"].value),
                    float(ws1["H11"].value),
                    float(ws1["H12"].value),
                    float(ws1["H13"].value),
                ]
                d_baseline = [db / 60 for db in d_baseline if db is not None]

                d_reject = [
                    ws1["J10"].value,
                    ws1["J11"].value,
                    ws1["J12"].value,
                    ws1["J13"].value,
                ]

                # (relies on strings evaluating True, and Nones evaluating False)
                valid = [
                    v and da is not None and db is not None and not dr
                    for v, da, db, dr in zip(valid, d_absolute, d_baseline, d_reject)
                ]

                # get horizontal field times (for consistency with WebAbsolutes, even
                #  if these spreadsheets always have the same times for D, H, and Z)
                h_time_str = [
                    "%04i" % ws1["B24"].value,
                    "%04i" % ws1["B25"].value,
                    "%04i" % ws1["B26"].value,
                    "%04i" % ws1["B27"].value,
                ]
                h_time_delta = [
                    timedelta(hours=int(s[0:2])) + timedelta(minutes=int(s[2:4]))
                    for s in h_time_str
                ]
                h_datetime = [date + td for td in h_time_delta]

                # get absolute horizontal field magnitude in nT
                h_absolute = [
                    float(ws1["D24"].value),
                    float(ws1["D25"].value),
                    float(ws1["D26"].value),
                    float(ws1["D27"].value),
                ]

                # get baseline horizontal field magnitude in nT
                h_baseline = [
                    float(ws1["H24"].value),
                    float(ws1["H25"].value),
                    float(ws1["H26"].value),
                    float(ws1["H27"].value),
                ]

                h_reject = [
                    ws1["J24"].value,
                    ws1["J25"].value,
                    ws1["J26"].value,
                    ws1["J27"].value,
                ]

                # (relies on strings evaluating True, and Nones evaluating False)
                valid = [
                    v and ha is not None and hb is not None and not hr
                    for v, ha, hb, hr in zip(valid, h_absolute, h_baseline, h_reject)
                ]

                # get vertical field times (for consistency with WebAbsolutes, even
                #  if these spreadsheets always have the same times for D, H, and Z)
                z_time_str = [
                    "%04i" % ws1["B38"].value,
                    "%04i" % ws1["B39"].value,
                    "%04i" % ws1["B40"].value,
                    "%04i" % ws1["B41"].value,
                ]
                z_time_delta = [
                    timedelta(hours=int(s[0:2])) + timedelta(minutes=int(s[2:4]))
                    for s in z_time_str
                ]
                z_datetime = [date + td for td in z_time_delta]

                # get absolute vertical field component in nT
                z_absolute = [
                    float(ws1["D38"].value),
                    float(ws1["D39"].value),
                    float(ws1["D40"].value),
                    float(ws1["D41"].value),
                ]

                # get baseline vertical field component in nT
                z_baseline = [
                    float(ws1["H38"].value),
                    float(ws1["H39"].value),
                    float(ws1["H40"].value),
                    float(ws1["H41"].value),
                ]

                z_reject = [
                    ws1["J38"].value,
                    ws1["J39"].value,
                    ws1["J40"].value,
                    ws1["J41"].value,
                ]

                # (relies on strings evaluating True, and Nones evaluating False)
                valid = [
                    v and za is not None and zb is not None and not zr
                    for v, za, zb, zr in zip(valid, z_absolute, z_baseline, z_reject)
                ]

            except:

                print(
                    "There was a problem reading file %s...skipping!"
                    % os.path.join(root, filename)
                )

            else:

                # add to lists, filtering on start_dt and end_dt and valid
                d_dt.extend(
                    [
                        dtt
                        for dtt, v in zip(d_datetime, valid)
                        if dtt >= start_dt and dtt <= end_dt and v
                    ]
                )
                d_abs.extend(
                    [
                        abs
                        for abs, dtt, v in zip(d_absolute, d_datetime, valid)
                        if dtt >= start_dt and dtt <= end_dt and v
                    ]
                )
                d_bas.extend(
                    [
                        bas
                        for bas, dtt, v in zip(d_baseline, d_datetime, valid)
                        if dtt >= start_dt and dtt <= end_dt and v
                    ]
                )

                h_dt.extend(
                    [
                        dtt
                        for dtt, v in zip(h_datetime, valid)
                        if dtt >= start_dt and dtt <= end_dt and v
                    ]
                )
                h_abs.extend(
                    [
                        abs
                        for abs, dtt, v in zip(h_absolute, h_datetime, valid)
                        if dtt >= start_dt and dtt <= end_dt and v
                    ]
                )
                h_bas.extend(
                    [
                        bas
                        for bas, dtt, v in zip(h_baseline, h_datetime, valid)
                        if dtt >= start_dt and dtt <= end_dt and v
                    ]
                )

                z_dt.extend(
                    [
                        dtt
                        for dtt, v in zip(z_datetime, valid)
                        if dtt >= start_dt and dtt <= end_dt and v
                    ]
                )
                z_abs.extend(
                    [
                        abs
                        for abs, dtt, v in zip(z_absolute, z_datetime, valid)
                        if dtt >= start_dt and dtt <= end_dt and v
                    ]
                )
                z_bas.extend(
                    [
                        bas
                        for bas, dtt, v in zip(z_baseline, z_datetime, valid)
                        if dtt >= start_dt and dtt <= end_dt and v
                    ]
                )

                # get pier corrections (one for each measurement, NOT one per file,
                #  even though that is all that is stored in these spreadsheets)
                pc.extend(
                    [
                        ws1["C5"].value
                        for dtt, v in zip(z_datetime, valid)
                        if dtt >= start_dt and dtt <= end_dt and v
                    ]
                )

                # the following is a kludge where we assume zero-amplitude horizontal field
                # serves as a "flag" for when some change was made to the observatory that
                # was significant enough to discard all previous absolute measurements
                # (i.e., an observer set inclination to exactly 90, which should never
                #  happen for valid absolute measurements at USGS observatories);
                flags = (
                    np.equal(h_absolute, 0)
                    & (np.array(h_datetime) >= start_dt)
                    & (np.array(h_datetime) <= end_dt)
                )
                if flags.any():
                    last_dt = max(max(np.array(h_datetime)[flags]), last_dt)

                # close workbook
                wb.close()

    # convert output lists to NumPy arrays
    h_abs = np.array(h_abs)
    d_abs = np.array(d_abs)
    z_abs = np.array(z_abs)
    h_bas = np.array(h_bas)
    d_bas = np.array(d_bas)
    z_bas = np.array(z_bas)
    pc = np.array(pc)

    # convert datetimes to UTCDateTimes
    h_utc = np.array([UTCDateTime(dt) for dt in h_dt])
    d_utc = np.array([UTCDateTime(dt) for dt in d_dt])
    z_utc = np.array([UTCDateTime(dt) for dt in z_dt])

    # print message about modified magnetometer
    if last_dt != start_dt:
        print("Magnetometer altered, discarding measurements prior to %s" % last_dt)

    # only return data more recent than last_dt
    good = (h_utc > last_dt) & (d_utc > last_dt) & (z_utc > last_dt)
    h_abs = h_abs[good]
    d_abs = d_abs[good]
    z_abs = z_abs[good]
    h_bas = h_bas[good]
    d_bas = d_bas[good]
    z_bas = z_bas[good]
    pc = pc[good]
    h_utc = h_utc[good]
    d_utc = d_utc[good]
    z_utc = z_utc[good]

    # return "good" data points
    return ((h_abs, h_bas, h_utc), (d_abs, d_bas, d_utc), (z_abs, z_bas, z_utc), pc)


def new_retrieve_baselines_webasolutes(
    observatory: str,
    starttime: str = UTCDateTime(0),
    endtime: UTCDateTime = UTCDateTime(),
):
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
    readings = WebAbsolutesFactory().get_readings(
        observatory=observatory, starttime=starttime, endtime=endtime
    )
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
    d_utc = d_utc[good]
    z_utc = z_utc[good]

    # return data arrays
    return ((h_abs, h_bas, h_utc), (d_abs, d_bas, d_utc), (z_abs, z_bas, z_utc), pc)


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


def generate_affine_0(ord_hez, abs_xyz, weights=None):
    """
    Generate affine transform matrix from ordinate to absolute coordinates,
    with least-squares and no constraints.

    Inputs:
    ord_hez - 3xN array holding HEZ vectors of Cartesian ordinate measurements
    abs_xyz - 3xN array holding XYZ vectors of Cartesian absolute measurements

    Options:
    weights - array of N weights that can be applied to observations

    Outout:
    M - a 4x4 affine transformation matrix to convert ord_hez into abs_xy
    """

    if weights is None:
        # equal weighting
        weights = 1
    else:
        # Wikipedia indicates sqrt(weights) is appropriate for WLS
        weights = np.sqrt(weights)
        # same weight applies to all three vector components
        weights = np.vstack((weights, weights, weights)).T.ravel()

    # extract measurements
    h_o = ord_hez[0]
    e_o = ord_hez[1]
    z_o = ord_hez[2]
    x_a = abs_xyz[0]
    y_a = abs_xyz[1]
    z_a = abs_xyz[2]

    # LHS, or dependent variables
    abs_st = np.vstack([x_a, y_a, z_a, np.ones_like(x_a)])

    # RHS, or independent variables
    ord_st = np.vstack([h_o, e_o, z_o, np.ones_like(h_o)])

    # LHS, or dependent variables
    abs_st = np.vstack([x_a, y_a, z_a])
    abs_st_r = abs_st.T.ravel()

    # RHS, or independent variables
    # (reduces degrees of freedom by 4:
    #  - 4 for the last row of zeros and a one)
    ord_st = np.vstack([h_o, e_o, z_o])
    ord_st_r = ord_st.T.ravel()
    ord_st_m = np.zeros((12, ord_st_r.size))
    ord_st_m[0, 0::3] = ord_st_r[0::3]
    ord_st_m[1, 0::3] = ord_st_r[1::3]
    ord_st_m[2, 0::3] = ord_st_r[2::3]
    ord_st_m[3, 0::3] = 1.0
    ord_st_m[4, 1::3] = ord_st_r[0::3]
    ord_st_m[5, 1::3] = ord_st_r[1::3]
    ord_st_m[6, 1::3] = ord_st_r[2::3]
    ord_st_m[7, 1::3] = 1.0
    ord_st_m[8, 2::3] = ord_st_r[0::3]
    ord_st_m[9, 2::3] = ord_st_r[1::3]
    ord_st_m[10, 2::3] = ord_st_r[2::3]
    ord_st_m[11, 2::3] = 1.0

    # apply weights
    ord_st_m = ord_st_m * weights
    abs_st_r = abs_st_r * weights

    # regression matrix M that minimizes L2 norm
    M_r, res, rank, sigma = spl.lstsq(ord_st_m.T, abs_st_r.T)

    if rank < 3:
        print("Poorly conditioned or singular matrix, returning NaNs")
        return np.nan * np.ones((4, 4))

    M = np.zeros((4, 4))
    M[0, 0] = M_r[0]
    M[0, 1] = M_r[1]
    M[0, 2] = M_r[2]
    M[0, 3] = M_r[3]
    M[1, 0] = M_r[4]
    M[1, 1] = M_r[5]
    M[1, 2] = M_r[6]
    M[1, 3] = M_r[7]
    M[2, 0] = M_r[8]
    M[2, 1] = M_r[9]
    M[2, 2] = M_r[10]
    M[2, 3] = M_r[11]
    M[3, :] = [0, 0, 0, 1]

    #     print(np.array_str(M, precision=3))

    return M


def generate_affine_1(ord_hez, abs_xyz, weights=None):
    """
    Generate affine transform matrix from ordinate to absolute coordinates,
    constrained to rotate about z-axis.

    Inputs:
    ord_hez - 3xN array holding HEZ vectors of Cartesian ordinate measurements
    abs_xyz - 3xN array holding XYZ vectors of Cartesian absolute measurements

    Options:
    weights - array of N weights that can be applied to observations

    Outout:
    M - a 4x4 affine transformation matrix to convert ord_hez into abs_xy
    """

    if weights is None:
        # equal weighting
        weights = 1
    else:
        # Wikipedia indicates sqrt(weights) is appropriate for WLS
        weights = np.sqrt(weights)
        # same weight applies to all three vector components
        weights = np.vstack((weights, weights, weights)).T.ravel()

    # extract measurements
    h_o = ord_hez[0]
    e_o = ord_hez[1]
    z_o = ord_hez[2]
    x_a = abs_xyz[0]
    y_a = abs_xyz[1]
    z_a = abs_xyz[2]

    # LHS, or dependent variables
    abs_st = np.vstack([x_a, y_a, z_a])
    abs_st_r = abs_st.T.ravel()

    # RHS, or independent variables
    # (reduces degrees of freedom by 8:
    #  - 2 for making x,y independent of z;
    #  - 2 for making z independent of x,y
    #  - 4 for the last row of zeros and a one)
    ord_st = np.vstack([h_o, e_o, z_o])
    ord_st_r = ord_st.T.ravel()
    ord_st_m = np.zeros((8, ord_st_r.size))
    ord_st_m[0, 0::3] = ord_st_r[0::3]
    ord_st_m[1, 0::3] = ord_st_r[1::3]
    ord_st_m[2, 0::3] = 1.0
    ord_st_m[3, 1::3] = ord_st_r[0::3]
    ord_st_m[4, 1::3] = ord_st_r[1::3]
    ord_st_m[5, 1::3] = 1.0
    ord_st_m[6, 2::3] = ord_st_r[2::3]
    ord_st_m[7, 2::3] = 1.0

    # apply weights
    ord_st_m = ord_st_m * weights
    abs_st_r = abs_st_r * weights

    # regression matrix M that minimizes L2 norm
    M_r, res, rank, sigma = spl.lstsq(ord_st_m.T, abs_st_r.T)

    if rank < 3:
        print("Poorly conditioned or singular matrix, returning NaNs")
        return np.nan * np.ones((4, 4))

    M = np.zeros((4, 4))
    M[0, 0] = M_r[0]
    M[0, 1] = M_r[1]
    M[0, 2] = 0.0
    M[0, 3] = M_r[2]
    M[1, 0] = M_r[3]
    M[1, 1] = M_r[4]
    M[1, 2] = 0.0
    M[1, 3] = M_r[5]
    M[2, 0] = 0.0
    M[2, 1] = 0.0
    M[2, 2] = M_r[6]
    M[2, 3] = M_r[7]
    M[3, :] = [0, 0, 0, 1]

    #     print(np.array_str(M, precision=3))

    return M


def generate_affine_2(ord_hez, abs_xyz, weights=None):
    """
    Generate affine transform matrix from ordinate to absolute coordinates,
    constrained to rotate about z-axis, and a uniform horizontal scaling
    factor.

    Inputs:
    ord_hez - 3xN array holding HEZ vectors of Cartesian ordinate measurements
    abs_xyz - 3xN array holding XYZ vectors of Cartesian absolute measurements

    Options:
    weights - array of N weights that can be applied to observations

    Outout:
    M - a 4x4 affine transformation matrix to convert ord_hez into abs_xy
    """

    if weights is None:
        # equal weighting
        weights = 1
    else:
        # Wikipedia indicates sqrt(weights) is appropriate for WLS
        weights = np.sqrt(weights)
        # same weight applies to all three vector components
        weights = np.vstack((weights, weights, weights)).T.ravel()

    # extract measurements
    h_o = ord_hez[0]
    e_o = ord_hez[1]
    z_o = ord_hez[2]
    x_a = abs_xyz[0]
    y_a = abs_xyz[1]
    z_a = abs_xyz[2]

    # LHS, or dependent variables
    abs_st = np.vstack([x_a, y_a, z_a])
    abs_st_r = abs_st.T.ravel()

    # RHS, or independent variables
    # (reduces degrees of freedom by 10:
    #  - 2 for making x,y independent of z;
    #  - 2 for making z independent of x,y
    #  - 2 for not allowing shear in x,y; and
    #  - 4 for the last row of zeros and a one)
    ord_st = np.vstack([h_o, e_o, z_o])
    ord_st_r = ord_st.T.ravel()
    ord_st_m = np.zeros((6, ord_st_r.size))
    ord_st_m[0, 0::3] = ord_st_r[0::3]
    ord_st_m[0, 1::3] = ord_st_r[1::3]
    ord_st_m[1, 0::3] = ord_st_r[1::3]
    ord_st_m[1, 1::3] = -ord_st_r[0::3]
    ord_st_m[2, 0::3] = 1.0
    ord_st_m[3, 1::3] = 1.0
    ord_st_m[4, 2::3] = ord_st_r[2::3]
    ord_st_m[5, 2::3] = 1.0

    # apply weights
    ord_st_m = ord_st_m * weights
    abs_st_r = abs_st_r * weights

    # regression matrix M that minimizes L2 norm
    M_r, res, rank, sigma = spl.lstsq(ord_st_m.T, abs_st_r.T)

    if rank < 3:
        print("Poorly conditioned or singular matrix, returning NaNs")
        return np.nan * np.ones((4, 4))

    M = np.zeros((4, 4))
    M[0, 0] = M_r[0]
    M[0, 1] = M_r[1]
    M[0, 2] = 0.0
    M[0, 3] = M_r[2]
    M[1, 0] = -M_r[1]
    M[1, 1] = M_r[0]
    M[1, 2] = 0.0
    M[1, 3] = M_r[3]
    M[2, 0] = 0.0
    M[2, 1] = 0.0
    M[2, 2] = M_r[4]
    M[2, 3] = M_r[5]
    M[3, :] = [0, 0, 0, 1]

    #     print(np.array_str(M, precision=3))

    return M


def generate_affine_3(ord_hez, abs_xyz, weights=None):
    """
    Generate affine transform matrix from ordinate to absolute coordinates,
    constrained to a rotation about the z-axis, a uniform scaling in the
    horizontal plane, and baseline shift only for z-axis. This is closest
    to how (quasi-)definitive data is processed at the USGS, and still be
    obtained directly from a least-squares inversion.

    Inputs:
    ord_hez - 3xN array holding HEZ vectors of Cartesian ordinate measurements
    abs_xyz - 3xN array holding XYZ vectors of Cartesian absolute measurements

    Options:
    weights - array of N weights that can be applied to observations

    Outout:
    M - a 4x4 affine transformation matrix to convert ord_hez into abs_xy
    """

    if weights is None:
        # equal weighting
        weights = 1
    else:
        # Wikipedia indicates sqrt(weights) is appropriate for WLS
        weights = np.sqrt(weights)
        # same weight applies to all three vector components
        weights = np.vstack((weights, weights, weights)).T.ravel()

    # extract measurements
    h_o = ord_hez[0]
    e_o = ord_hez[1]
    z_o = ord_hez[2]
    x_a = abs_xyz[0]
    y_a = abs_xyz[1]
    z_a = abs_xyz[2]

    # re-estimate cylindrical vectors from Cartesian
    h_ord = np.sqrt(h_o ** 2 + e_o ** 2)
    d_ord = np.arctan2(e_o, h_o)
    z_ord = z_o
    h_abs = np.sqrt(x_a ** 2 + y_a ** 2)
    d_abs = np.arctan2(y_a, x_a)
    z_abs = z_a

    # generate average rotation from ord to abs, then convert
    # to rotation affine transform matrix
    dRavg = (d_abs - d_ord).mean()
    Rmtx = np.eye(4)
    Rmtx[0, 0] = np.cos(dRavg)
    Rmtx[0, 1] = -np.sin(dRavg)
    Rmtx[1, 0] = np.sin(dRavg)
    Rmtx[1, 1] = np.cos(dRavg)

    # generate average ratio of h_abs/h_ord, use this to
    # define a scaling affine transform matrix
    rHavg = (h_abs / h_ord).mean()
    Smtx = np.eye(4)
    Smtx[0, 0] = rHavg
    Smtx[1, 1] = rHavg

    # apply average rotations and scales to HE data, determine the
    # average translations, then generate affine transform matrix
    dXavg = (x_a - (h_o * rHavg * np.cos(dRavg) - e_o * rHavg * np.sin(dRavg))).mean()
    dYavg = (y_a - (h_o * rHavg * np.sin(dRavg) + e_o * rHavg * np.cos(dRavg))).mean()
    dZavg = (z_a - z_o).mean()
    Tmtx = np.eye(4)
    Tmtx[0, 3] = dXavg
    Tmtx[1, 3] = dYavg
    Tmtx[2, 3] = dZavg

    # combine rotation, scale, and translation matrices
    M = np.dot(np.dot(Rmtx, Smtx), Tmtx)

    #     # NOTE: the preceding isn't quite how Definitive/Quasi-Definitive
    #     # processing works; the following is closer, but the two generate
    #     # very similar output, with most of the tiny discrepancy arising
    #     # due to the fact that the operation below *adds* an H baseline,
    #     # something that is not easy (or possible?) with an affine transform,
    #     # so instead, a scaling factor is used to adjust he to match xy.
    #     def_h = (h_o**2 + e_o**2)**0.5 + h_bas.mean()
    #     def_d = np.arctan2(e_o, h_o) * 180./np.pi + d_bas.mean()
    #     def_z = z_o + z_bas.mean()
    #     def_f = (def_h**2 + def_z**2)**0.5
    #     def_x = def_h * np.cos(def_d * np.pi/180.)
    #     def_y = def_h * np.sin(def_d * np.pi/180.)

    #     print(np.array_str(Rmtx, precision=3))
    #     print(np.array_str(Smtx, precision=3))
    #     print(np.array_str(Tmtx, precision=3))
    #     print(np.array_str(M, precision=3))

    # ...or, solve for M directly

    # LHS, or dependent variables
    abs_st = np.vstack([x_a, y_a, z_a])
    abs_st_r = abs_st.T.ravel()

    # RHS, or independent variables
    # (reduces degrees of freedom by 13:
    #  - 2 for making x,y independent of z;
    #  - 2 for making z independent of x,y;
    #  - 2 for not allowing shear in x,y;
    #  - 2 for not allowing translation in x,y;
    #  - 1 for not allowing scaling in z; and
    #  - 4 for the last row of zeros and a one)
    ord_st = np.vstack([h_o, e_o, z_o])
    ord_st_r = ord_st.T.ravel()
    ord_st_m = np.zeros((3, ord_st_r.size))
    ord_st_m[0, 0::3] = ord_st_r[0::3]
    ord_st_m[0, 1::3] = ord_st_r[1::3]
    ord_st_m[1, 0::3] = ord_st_r[1::3]
    ord_st_m[1, 1::3] = -ord_st_r[0::3]
    ord_st_m[2, 2::3] = 1.0

    # subtract z_o from z_a to force simple z translation
    abs_st_r[2::3] = abs_st_r[2::3] - ord_st_r[2::3]

    # apply weights
    ord_st_m = ord_st_m * weights
    abs_st_r = abs_st_r * weights

    # regression matrix M that minimizes L2 norm
    M_r, res, rank, sigma = spl.lstsq(ord_st_m.T, abs_st_r.T)

    if rank < 3:
        print("Poorly conditioned or singular matrix, returning NaNs")
        return np.nan * np.ones((4, 4))

    M = np.zeros((4, 4))
    M[0, 0] = M_r[0]
    M[0, 1] = M_r[1]
    M[0, 2] = 0.0
    M[0, 3] = 0.0
    M[1, 0] = -M_r[1]
    M[1, 1] = M_r[0]
    M[1, 2] = 0.0
    M[1, 3] = 0.0
    M[2, 0] = 0.0
    M[2, 1] = 0.0
    M[2, 2] = 1.0
    M[2, 3] = M_r[2]
    M[3, :] = [0, 0, 0, 1]

    #     print(np.array_str(M, precision=3))

    return M


def generate_affine_4(ord_hez, abs_xyz, weights=None):
    """
    Generate affine transform matrix from ordinate to absolute coordinates,
    constrained to 3D scaled rigid rotation+translation (that is, no shear).

    References:
    https://igl.ethz.ch/projects/ARAP/svd_rot.pdf
    http://graphics.stanford.edu/~smr/ICP/comparison/eggert_comparison_mva97.pdf
    http://graphics.stanford.edu/~smr/ICP/comparison/horn-hilden-orientation-josa88.pdf

    Inputs:
    ord_hez - 3xN array holding HEZ vectors of Cartesian ordinate measurements
    abs_xyz - 3xN array holding XYZ vectors of Cartesian absolute measurements

    Options:
    weights - array of N weights that can be applied to observations

    Outout:
    M - a 4x4 affine transformation matrix to convert ord_hez into abs_xy
    """

    if weights is None:
        # equal weighting
        weights = np.ones_like(ord_hez[0])

        # NOTE: do not sqrt(weights) as with weighted least-squares (WLS);
        #       NumPy's average and cov functions handle weights properly

    # extract measurements
    h_o = ord_hez[0]
    e_o = ord_hez[1]
    z_o = ord_hez[2]
    x_a = abs_xyz[0]
    y_a = abs_xyz[1]
    z_a = abs_xyz[2]

    # weighted centroids
    h_o_cent = np.average(h_o, weights=weights)
    e_o_cent = np.average(e_o, weights=weights)
    z_o_cent = np.average(z_o, weights=weights)
    x_a_cent = np.average(x_a, weights=weights)
    y_a_cent = np.average(y_a, weights=weights)
    z_a_cent = np.average(z_a, weights=weights)

    # generate weighted "covariance" matrix
    H = np.dot(
        np.vstack([h_o - h_o_cent, e_o - e_o_cent, z_o - z_o_cent]),
        np.dot(
            np.diag(weights),
            np.vstack([x_a - x_a_cent, y_a - y_a_cent, z_a - z_a_cent]).T,
        ),
    )

    # Singular value decomposition, then rotation matrix from L&R eigenvectors
    # (the determinant guarantees a rotation, and not a reflection)
    U, S, Vh = np.linalg.svd(H)

    if np.sum(S) < 3:
        print("Poorly conditioned or singular matrix, returning NaNs")
        return np.nan * np.ones((4, 4))

    R = np.dot(Vh.T, np.dot(np.diag([1, 1, np.linalg.det(np.dot(Vh.T, U.T))]), U.T))

    #     # symmetric scale factor
    #     s = np.sqrt(np.sum(np.vstack([(x_a - x_a_cent)**2,
    #                                    (y_a - y_a_cent)**2,
    #                                    (z_a - z_a_cent)**2])) /
    #                  np.sum(np.vstack([(h_o - h_o_cent)**2,
    #                                    (e_o - e_o_cent)**2,
    #                                    (z_o - z_o_cent)**2])) )

    #     # re-scale the rotation (must be done prior to estimating T)
    #     R *= s

    # now get translation using weighted centroids and R
    T = np.array([x_a_cent, y_a_cent, z_a_cent]) - np.dot(
        R, [h_o_cent, e_o_cent, z_o_cent]
    )

    M = np.eye(4)
    M[:3, :3] = R
    M[:3, 3] = T

    #     print(np.array_str(M, precision=3))

    return M


def generate_affine_5(ord_hez, abs_xyz, weights=None):
    """
    Generate affine transform matrix from ordinate to absolute coordinates,
    constrained to re-scale each axis.

    Inputs:
    ord_hez - 3xN array holding HEZ vectors of Cartesian ordinate measurements
    abs_xyz - 3xN array holding XYZ vectors of Cartesian absolute measurements

    Options:
    weights - array of N weights that can be applied to observations

    Outout:
    M - a 4x4 affine transformation matrix to convert ord_hez into abs_xy
    """

    if weights is None:
        # equal weighting
        weights = 1
    else:
        # Wikipedia indicates sqrt(weights) is appropriate for WLS
        weights = np.sqrt(weights)
        # same weight applies to all three vector components
        weights = np.vstack((weights, weights, weights)).T.ravel()

    # extract measurements
    h_o = ord_hez[0]
    e_o = ord_hez[1]
    z_o = ord_hez[2]
    x_a = abs_xyz[0]
    y_a = abs_xyz[1]
    z_a = abs_xyz[2]

    # LHS, or dependent variables
    abs_st = np.vstack([x_a, y_a, z_a])
    abs_st_r = abs_st.T.ravel()

    # RHS, or independent variables
    # (reduces degrees of freedom by 13:
    #  - 2 for making x independent of y,z;
    #  - 2 for making y,z independent of x;
    #  - 1 for making y independent of z;
    #  - 1 for making z independent of y;
    #  - 3 for not translating xyz
    #  - 4 for the last row of zeros and a one)
    ord_st = np.vstack([h_o, e_o, z_o])
    ord_st_r = ord_st.T.ravel()
    ord_st_m = np.zeros((3, ord_st_r.size))
    ord_st_m[0, 0::3] = ord_st_r[0::3]
    ord_st_m[1, 1::3] = ord_st_r[1::3]
    ord_st_m[2, 2::3] = ord_st_r[2::3]

    # apply weights
    ord_st_m = ord_st_m * weights
    abs_st_r = abs_st_r * weights

    # regression matrix M that minimizes L2 norm
    M_r, res, rank, sigma = spl.lstsq(ord_st_m.T, abs_st_r.T)

    if rank < 3:
        print("Poorly conditioned or singular matrix, returning NaNs")
        return np.nan * np.ones((4, 4))

    M = np.zeros((4, 4))
    M[0, 0] = M_r[0]
    M[0, 1] = 0.0
    M[0, 2] = 0.0
    M[0, 3] = 0.0
    M[1, 0] = 0.0
    M[1, 1] = M_r[1]
    M[1, 2] = 0.0
    M[1, 3] = 0.0
    M[2, 0] = 0.0
    M[2, 1] = 0.0
    M[2, 2] = M_r[2]
    M[2, 3] = 0.0
    M[3, :] = [0, 0, 0, 1]

    #     print(np.array_str(M, precision=3))

    return M


def generate_affine_6(ord_hez, abs_xyz, weights=None):
    """
    Generate affine transform matrix from ordinate to absolute coordinates,
    constrained to translate origins.

    Inputs:
    ord_hez - 3xN array holding HEZ vectors of Cartesian ordinate measurements
    abs_xyz - 3xN array holding XYZ vectors of Cartesian absolute measurements

    Options:
    weights - array of N weights that can be applied to observations

    Outout:
    M - a 4x4 affine transformation matrix to convert ord_hez into abs_xy
    """

    if weights is None:
        # equal weighting
        weights = 1
    else:
        # Wikipedia indicates sqrt(weights) is appropriate for WLS
        weights = np.sqrt(weights)
        # same weight applies to all three vector components
        weights = np.vstack((weights, weights, weights)).T.ravel()

    # extract measurements
    h_o = ord_hez[0]
    e_o = ord_hez[1]
    z_o = ord_hez[2]
    x_a = abs_xyz[0]
    y_a = abs_xyz[1]
    z_a = abs_xyz[2]

    # LHS, or dependent variables
    abs_st = np.vstack([x_a, y_a, z_a])
    abs_st_r = abs_st.T.ravel()

    # RHS, or independent variables
    # (reduces degrees of freedom by 10:
    #  - 2 for making x independent of y,z;
    #  - 2 for making y,z independent of x;
    #  - 1 for making y independent of z;
    #  - 1 for making z independent of y;
    #  - 3 for not scaling each axis
    #  - 4 for the last row of zeros and a one)
    ord_st = np.vstack([h_o, e_o, z_o])
    ord_st_r = ord_st.T.ravel()
    ord_st_m = np.zeros((3, ord_st_r.size))
    ord_st_m[0, 0::3] = 1.0
    ord_st_m[1, 1::3] = 1.0
    ord_st_m[2, 2::3] = 1.0

    # subtract ords from abs to force simple translation
    abs_st_r[0::3] = abs_st_r[0::3] - ord_st_r[0::3]
    abs_st_r[1::3] = abs_st_r[1::3] - ord_st_r[1::3]
    abs_st_r[2::3] = abs_st_r[2::3] - ord_st_r[2::3]

    # apply weights
    ord_st_m = ord_st_m * weights
    abs_st_r = abs_st_r * weights

    # regression matrix M that minimizes L2 norm
    M_r, res, rank, sigma = spl.lstsq(ord_st_m.T, abs_st_r.T)

    if rank < 3:
        print("Poorly conditioned or singular matrix, returning NaNs")
        return np.nan * np.ones((4, 4))

    M = np.zeros((4, 4))
    M[0, 0] = 1.0
    M[0, 1] = 0.0
    M[0, 2] = 0.0
    M[0, 3] = M_r[0]
    M[1, 0] = 0.0
    M[1, 1] = 1.0
    M[1, 2] = 0.0
    M[1, 3] = M_r[1]
    M[2, 0] = 0.0
    M[2, 1] = 0.0
    M[2, 2] = 1.0
    M[2, 3] = M_r[2]
    M[3, :] = [0, 0, 0, 1]

    #     print(np.array_str(M, precision=3))

    return M


def generate_affine_7(ord_hez, abs_xyz, weights=None):
    """
    Generate affine transform matrix from ordinate to absolute coordinates,
    constrained to shear y and z, but not x.

    Inputs:
    ord_hez - 3xN array holding HEZ vectors of Cartesian ordinate measurements
    abs_xyz - 3xN array holding XYZ vectors of Cartesian absolute measurements

    Options:
    weights - array of N weights that can be applied to observations

    Outout:
    M - a 4x4 affine transformation matrix to convert ord_hez into abs_xy
    """

    if weights is None:
        # equal weighting
        weights = 1
    else:
        # Wikipedia indicates sqrt(weights) is appropriate for WLS
        weights = np.sqrt(weights)
        # same weight applies to all three vector components
        weights = np.vstack((weights, weights, weights)).T.ravel()

    # extract measurements
    h_o = ord_hez[0]
    e_o = ord_hez[1]
    z_o = ord_hez[2]
    x_a = abs_xyz[0]
    y_a = abs_xyz[1]
    z_a = abs_xyz[2]

    # LHS, or dependent variables
    abs_st = np.vstack([x_a, y_a, z_a])
    abs_st_r = abs_st.T.ravel()

    # RHS, or independent variables
    # (reduces degrees of freedom by 13:
    #  - 2 for making x independent of y,z;
    #  - 1 for making y independent of z;
    #  - 3 for not scaling each axis
    #  - 4 for the last row of zeros and a one)
    ord_st = np.vstack([h_o, e_o, z_o])
    ord_st_r = ord_st.T.ravel()
    ord_st_m = np.zeros((3, ord_st_r.size))
    ord_st_m[0, 0::3] = 1.0
    ord_st_m[1, 0::3] = ord_st_r[0::3]
    ord_st_m[1, 1::3] = 1.0
    ord_st_m[2, 0::3] = ord_st_r[0::3]
    ord_st_m[2, 1::3] = ord_st_r[1::3]
    ord_st_m[2, 2::3] = 1.0

    # apply weights
    ord_st_m = ord_st_m * weights
    abs_st_r = abs_st_r * weights

    # regression matrix M that minimizes L2 norm
    M_r, res, rank, sigma = spl.lstsq(ord_st_m.T, abs_st_r.T)

    if rank < 3:
        print("Poorly conditioned or singular matrix, returning NaNs")
        return np.nan * np.ones((4, 4))

    M = np.zeros((4, 4))
    M[0, 0] = 1.0
    M[0, 1] = 0.0
    M[0, 2] = 0.0
    M[0, 3] = 0.0
    M[1, 0] = M_r[0]
    M[1, 1] = 1.0
    M[1, 2] = 0.0
    M[1, 3] = 0.0
    M[2, 0] = M_r[1]
    M[2, 1] = M_r[2]
    M[2, 2] = 1.0
    M[2, 3] = 0.0
    M[3, :] = [0, 0, 0, 1]

    #     print(np.array_str(M, precision=3))

    return M


def generate_affine_8(ord_hez, abs_xyz, weights=None):
    """
    Generate affine transform matrix from ordinate to absolute coordinates,
    constrained to rigid rotation+translation (that is, no scale or shear)
    in xy, and translation only in z.

    References:
    https://igl.ethz.ch/projects/ARAP/svd_rot.pdf
    http://graphics.stanford.edu/~smr/ICP/comparison/eggert_comparison_mva97.pdf
    http://graphics.stanford.edu/~smr/ICP/comparison/horn-hilden-orientation-josa88.pdf

    Inputs:
    ord_hez - 3xN array holding HEZ vectors of Cartesian ordinate measurements
    abs_xyz - 3xN array holding XYZ vectors of Cartesian absolute measurements

    Options:
    weights - array of N weights that can be applied to observations

    Outout:
    M - a 4x4 affine transformation matrix to convert ord_hez into abs_xy
    """

    if weights is None:
        # equal weighting
        weights = np.ones_like(ord_hez[0])

        # NOTE: do not sqrt(weights) as with weighted least-squares (WLS);
        #       NumPy's average and cov functions handle weights properly

    # extract measurements
    h_o = ord_hez[0]
    e_o = ord_hez[1]
    z_o = ord_hez[2]
    x_a = abs_xyz[0]
    y_a = abs_xyz[1]
    z_a = abs_xyz[2]

    # weighted centroids
    h_o_cent = np.average(h_o, weights=weights)
    e_o_cent = np.average(e_o, weights=weights)
    z_o_cent = np.average(z_o, weights=weights)
    x_a_cent = np.average(x_a, weights=weights)
    y_a_cent = np.average(y_a, weights=weights)
    z_a_cent = np.average(z_a, weights=weights)

    # generate weighted "covariance" matrix
    H = np.dot(
        np.vstack([h_o - h_o_cent, e_o - e_o_cent]),
        np.dot(np.diag(weights), np.vstack([x_a - x_a_cent, y_a - y_a_cent]).T),
    )

    # Singular value decomposition, then rotation matrix from L&R eigenvectors
    # (the determinant guarantees a rotation, and not a reflection)
    U, S, Vh = np.linalg.svd(H)

    if np.sum(S) < 2:
        print("Poorly conditioned or singular matrix, returning NaNs")
        return np.nan * np.ones((4, 4))

    R = np.dot(Vh.T, np.dot(np.diag([1, np.linalg.det(np.dot(Vh.T, U.T))]), U.T))

    # now get translation using weighted centroids and R
    T = np.array([x_a_cent, y_a_cent]) - np.dot(R, [h_o_cent, e_o_cent])

    M = np.eye(4)
    M[:2, :2] = R
    M[:2, 3] = T

    M[2, 3] = np.array(z_a_cent) - np.array(z_o_cent)

    #     print(np.array_str(M, precision=3))

    return M


def generate_affine_9(ord_hez, abs_xyz, weights=None):
    """
    Generate affine transform matix from ordinate to absolute coordinates,
    constrained to rotate about z-axis, with only rotation and shear in the
    horizontal plane (no scaling), using QR factorization.

    References:
    https://math.stackexchange.com/questions/1120209/decomposition-of-4x4-or-larger-affine-transformation-matrix-to-individual-variab
    https://math.stackexchange.com/questions/2237262/is-there-a-correct-qr-factorization-result

    Inputs:
    ord_hez - 3xN array holding HEZ vectors of Cartesian ordinate measurements
    abs_xyz - 3xN array holding XYZ vectors of Cartesian absolute measurements

    Options:
    weights - array of N weights that can be applied to observations

    Outout:
    M - a 4x4 affine transformation matrix to convert ord_hez into abs_xy
    """

    if weights is None:
        # equal weighting
        weights = 1

    # extract measurements
    h_o = ord_hez[0]
    e_o = ord_hez[1]
    z_o = ord_hez[2]
    x_a = abs_xyz[0]
    y_a = abs_xyz[1]
    z_a = abs_xyz[2]

    # weighted centroids
    h_o_cent = np.average(h_o, weights=weights)
    e_o_cent = np.average(e_o, weights=weights)
    z_o_cent = np.average(z_o, weights=weights)
    x_a_cent = np.average(x_a, weights=weights)
    y_a_cent = np.average(y_a, weights=weights)
    z_a_cent = np.average(z_a, weights=weights)

    # LHS, or dependent variables
    abs_st = np.vstack([x_a - x_a_cent, y_a - y_a_cent])

    # RHS, or independent variables
    ord_st = np.vstack([h_o - h_o_cent, e_o - e_o_cent])

    # apply weights
    ord_st = ord_st * np.sqrt(weights)
    abs_st = abs_st * np.sqrt(weights)

    # regression matrix M that minimizes L2 norm
    M_r, res, rank, sigma = spl.lstsq(ord_st.T, abs_st.T)

    if rank < 2:
        print("Poorly conditioned or singular matrix, returning NaNs")
        return np.nan * np.ones((4, 4))

    # QR fatorization
    # NOTE: forcing the diagonal elements of Q to be positive
    #       ensures that the determinant is 1, not -1, and is
    #       therefore a rotation, not a reflection
    Q, R = np.linalg.qr(M_r.T)
    neg = np.diag(Q) < 0
    Q[:, neg] = -1 * Q[:, neg]
    R[neg, :] = -1 * R[neg, :]

    # isolate scales from shear
    S = np.diag(np.diag(R))
    H = np.dot(np.linalg.inv(S), R)

    # combine shear and rotation
    QH = np.dot(Q, H)

    # now get translation using weighted centroids and R
    T = np.array([x_a_cent, y_a_cent]) - np.dot(QH, [h_o_cent, e_o_cent])

    M = np.eye(4)
    M[:2, :2] = QH
    M[:2, 3] = T

    M[2, 3] = np.array(z_a_cent) - np.array(z_o_cent)

    #     print(np.array_str(M, precision=3))

    return M


def interpolate_affine_polar(utc_target, utc_list, affine_list, fill_value=None):
    """
    Interpolate between affine transform matices. Interpolating linear/affine
    transform matrices is problematic because the rotation component cannot
    be directly interpolated in a way that maintains a valid rotation matrix
    at intermediate points. Here we first use Polar decomposition to decompose
    the transform into an orthogonal matrix Q and a "stretch" matrix S (M=QS).
    The Qs are interpolated between Slerp, while the Ss are interpolated using
    using standard linear interpolation.


    References:
    http://research.cs.wisc.edu/graphics/Courses/838-s2002/Papers/polar-decomp.pdf
    https://en.wikipedia.org/wiki/Slerp
    http://run.usc.edu/cs520-s15/assign2/p245-shoemake.pdf

    Inputs:
    utc_target    - list of UTCs at which to interpolate affine matrices
    utc_list      - list of UTCs that correspond to a list of known affine matrices
    affine_list   - list of known affine matrices

    Options:
    fill_value    - if None, disallow extrapolation; if not None, use this
                    value when utc_target falls outside utc_list range; if
                    "extrapolate", extrapolate based on first/last two in
                    affine_list.
                    NOTE: SciPy's Slerp cannot presently extrapolate, so
                          this function will simply extend the first/last
                          affine_list matrices to all times outside utc_list.

    Outout:
    affine_target - list of interpolated affine matrices
    """

    if fill_value is not None:
        raise ValueError("fill_value extrapolation not implemented")

    # decompose affine_list
    Ts_in = []  # translations
    Rs_in = []  # rotations
    Ns_in = []  # +/- I (accomodates reflections)
    Ss_in = []  # stretches
    for M in affine_list:
        # polar decomposition
        Q, S = spl.polar(M[:3, :3])
        if np.linalg.det(Q) < 0:
            # factor out -I if det(Q) is -1
            R = np.dot(Q, np.linalg.inv(-np.eye(3)))
            N = -np.eye(3)
        else:
            R = Q
            N = np.eye(3)
        Ts_in.append(M[:3, 3, None])
        Rs_in.append(R)
        Ns_in.append(N)
        Ss_in.append(S)

    # interp1d Ts
    Ts_out = []
    Rs_out = []
    Ns_out = []
    Ss_out = []
    for T in np.reshape(Ts_in, (-1, 3)).T:
        int1d = interp1d(
            np.asarray(utc_list).astype(float), T, fill_value="extrapolate"
        )
        Ts_out.append(int1d(np.asarray(utc_target).astype(float)))
    Ts_out = np.array(Ts_out).T.reshape(-1, 3, 1)

    # SLERP Rs
    Rs = Rotation.from_dcm(Rs_in)
    Rslerp = Slerp(np.asarray(utc_list).astype(float), Rs)
    Rs_out = Rslerp(np.asarray(utc_target).astype(float))
    Rs_out = Rs_out.as_dcm()
    # Rs_out = [R.as_dcm() for R in Rs_out]

    # interp1d Ns
    for N in np.reshape(Ns_in, (-1, 9)).T:
        int1d = interp1d(
            np.asarray(utc_list).astype(float), N, fill_value="extrapolate"
        )
        Ns_out.append(int1d(np.asarray(utc_target).astype(float)))
    Ns_out = np.array(Ns_out).T.reshape(-1, 3, 3)

    # interp1d Ss
    for S in np.reshape(Ss_in, (-1, 9)).T:
        int1d = interp1d(
            np.asarray(utc_list).astype(float), S, fill_value="extrapolate"
        )
        Ss_out.append(int1d(np.asarray(utc_target).astype(float)))
    Ss_out = np.array(Ss_out).T.reshape(-1, 3, 3)

    # recombine components into M_target list
    affine_target = []
    for t in np.arange(len(utc_target)):

        affine_target.append(
            np.vstack(
                (
                    np.hstack(
                        (np.dot(Rs_out[t], np.dot(Ns_out[t], Ss_out[t])), Ts_out[t])
                    ),
                    [0, 0, 0, 1],
                )
            )
        )

    return affine_target


def do_one(
    weights: List[float],
    h_utc: UTCDateTime.timestamp,
    memory: List[float],
    start_UTC: UTCDateTime,
    acausal: bool,
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
    obs_code,
    start_UTC,
    end_UTC,
    update_interval=None,
    acausal=False,
    interpolate=False,
    first_UTC=None,
    last_UTC=None,
    M_funcs=[generate_affine_0],
    memories: List[float] = [np.inf],
    path_or_url="https://geomag.usgs.gov",
    validate=False,
    edge_host="cwbpub.cr.usgs.gov",
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
    interpolate     - interpolate between key transforms
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
    validate        - if True, pull and process raw data, then compare with QD
                      (default = False)
    edge_host       - edge host for raw and QD magnetometer time series
                      (default = 'cwbpub.cr.usgs.gov')

    OUTPUTS:
    utc_list        - list of first UTCDateTimes for each update_interval
    M_composed_list - list of composed Adjusted Data matrices for each update_interval
    pc_list         - list of pier corrections for each update_interval

    (if validate is True)
    utc_xyzf_list   - list of UTCDateTime arrays for each observation
    xyzf_trad_list  - list of static baseline adjusted data arrays for each update_interval
    xyzf_adj_list   - list of Adjusted Data arrays for each update_interval
    xyzf_def_list   - list of Definitive Data arrays for each update_interval
    utc_bas         - UTCDateTimes for absolute measurements
    abs_xyz         - absolute XYZ values used to train affine transforms
    ord_hez         - ordinate HEZ values used to train affine transforms
    Ms_list         - list of lists of Adjusted Data matrices for each M_func,
                      for each update_interval
    weights_list    - list of lists of weights used to estimate Adjusted Data
                      matrices for each M_func, for each update_interval

    """

    # set start_UTC and end_UTC if not passed
    if first_UTC is None:
        first_UTC = start_UTC
    if last_UTC is None:
        last_UTC = end_UTC

    # default update_interval
    if update_interval is None:
        # only one interval from start_UTC to end_UTC
        update_interval = end_UTC - start_UTC

    # make sure memory is compatible with M_funcs
    if np.isscalar(memories):
        memories = [memories for func in M_funcs]
    elif len(memories) == 1:
        memories = [memories[0] for func in M_funcs]
    elif len(memories) != len(M_funcs):
        raise ValueError(
            "Memories must be a scalar or list with same length as M_funcs"
        )

    # retrieve all absolute calibrations and baselines from start_UTC to end_UTC
    if obs_code == "DED" or obs_code == "CMO":
        # use residual method summary spreadsheets to retrieve baseline info

        # if a file: URL is passed, just trim off the front for now
        if path_or_url.startswith("file:"):
            path_or_url = path_or_url[len("file:") :]
            while path_or_url.startswith("//"):
                path_or_url = path_or_url[2:]

        (
            (h_abs, h_bas, h_utc),
            (d_abs, d_bas, d_utc),
            (z_abs, z_bas, z_utc),
            pc,
        ) = retrieve_baselines_resid_summary_xlsm(
            obs_code, start_date=first_UTC, end_date=last_UTC, path_or_url=path_or_url
        )
    else:

        # use WebAbsolutes web service to retrieve baseline info
        (
            (h_abs, h_bas, h_utc),
            (d_abs, d_bas, d_utc),
            (z_abs, z_bas, z_utc),
            pc,
        ) = new_retrieve_baselines_webasolutes(
            obs_code, starttime=first_UTC, endtime=last_UTC
        )

    # recreate ordinate variometer measurements from absolutes and baselines
    h_ord = h_abs - h_bas
    d_ord = d_abs - d_bas
    z_ord = z_abs - z_bas

    # convert from cylindrical to Cartesian coordinates
    x_a = h_abs * np.cos(d_abs * np.pi / 180)
    y_a = h_abs * np.sin(d_abs * np.pi / 180)
    z_a = z_abs
    #     h_o = h_ord * np.cos(d_ord * np.pi/180)
    #     e_o = h_ord * np.sin(d_ord * np.pi/180)
    #     z_o = z_ord

    # WebAbsolutes defines/generates h differently than USGS residual
    # method spreadsheets. The following should ensure that ordinate
    # values are converted back to their original raw measurements:
    e_o = h_abs * d_ord * 60 / 3437.7468
    if obs_code == "DED" or obs_code == "CMO":
        h_o = np.sqrt(h_ord ** 2 - e_o ** 2)
    else:
        h_o = h_ord
    z_o = z_ord

    # use h_utc as common time stamp for vectors
    utc_bas = h_utc
    # stack absolute and ordinate vectors for output
    abs_xyz = np.vstack((x_a, y_a, z_a))
    ord_hez = np.vstack((h_o, e_o, z_o))

    # initialize outputs
    utc_list = []
    M_composed_list = []
    Ms_list = []
    pcwa_list = []
    weights_list = []
    utc_xyzf_list = []
    xyzf_trad_list = []
    xyzf_adj_list = []
    xyzf_def_list = []

    # process each update_interval from start_UTC to end_UTC
    while (start_UTC < end_UTC) or (start_UTC <= end_UTC and interpolate is True):

        print("Generating key transform for ", start_UTC)

        # reset intermediate input values
        h_tmp = h_o
        e_tmp = e_o
        z_tmp = z_o

        # reinitialize weights, Ms and pcwa lists
        weights = []
        Ms = []
        pcwa = []

        # loop over M_funcs and memories to compose affine matrix
        for M_func, memory in zip(M_funcs, memories):
            # Calculate time-dependent weights using h_utc
            weights.append(time_weights_exponential(h_utc, memory, start_UTC.timestamp))

            # set weights for future observations to zero if not acausal
            if not acausal:
                weights[-1][h_utc > start_UTC] = 0.0

            # return NaNs if no valid observations
            if np.sum(weights[-1]) == 0:
                Ms.append(np.nan * np.zeros((4, 4)))
                pcwa.append(np.nan)
                print("No valid observations for interval")
                continue
            h_tmp, e_tmp, z_tmp, pcwa, Ms, weights = do_one(
                weights=weights,
                h_utc=h_utc,
                memory=memory,
                start_UTC=start_UTC,
                acausal=acausal,
                Ms=Ms,
                pcwa=pcwa,
                h_bas=h_bas,
                d_bas=d_bas,
                z_bas=z_bas,
                M_func=M_func,
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
        Ms_list.append(Ms)
        pcwa_list.append(pcwa)
        weights_list.append(weights)

        # compose affine transform matrices
        M_composed = reduce(np.dot, Ms[::-1])

        # append to list of outputs for each update_interval
        M_composed_list.append(M_composed)

        # append to list of outputs for each update_interval
        utc_list.append(start_UTC)

        # generate/pull data for validation if requested
        if validate:

            if interpolate is True:
                if len(utc_list) == 1:
                    # can't interpolate with only 1 transform
                    start_UTC = start_UTC + update_interval
                    continue
                else:
                    valid_start = start_UTC - update_interval
                    valid_end = start_UTC
            else:
                valid_start = start_UTC
                valid_end = start_UTC + update_interval

            print("Validating interval ", valid_start, " to ", valid_end)

            # retrieve raw HEZF variometer data from Edge server
            factory = EdgeFactory(host=edge_host)
            hezf = factory.get_timeseries(
                observatory=obs_code,
                interval="minute",
                type="variation",
                channels=("H", "E", "Z", "F"),
                starttime=valid_start,
                endtime=valid_end,
            )

            # place hez traces into hez1 matrix required for regression
            hez1_arr = np.vstack(
                (hezf[0].data, hezf[1].data, hezf[2].data, np.ones_like(hezf[3]))
            )

            # generate list of UTCDateTimes
            utc_arr = np.array(
                [(hezf[0].stats.starttime + second) for second in hezf[0].times()]
            )

            if interpolate is True:
                # interpolate transform matrices
                M_each = interpolate_affine_polar(
                    utc_arr, utc_list[-2:], M_composed_list[-2:]
                )
            else:
                # generate list of identical matrices
                M_each = [M_composed for each in utc_arr]

            # generate adjusted data using composed affine transform matrix
            xyz1 = np.transpose(
                [
                    np.dot(M_each[obs], hez1_arr[:, obs])
                    for obs in np.arange(len(utc_arr))
                ]
            ).squeeze()
            xyzf = np.vstack((xyz1[:-1], hezf[3].data + np.mean(pcwa_list[-1])))

            # append xyzf to list of outputs for each update interval
            xyzf_adj_list.append(xyzf)

            # apply average traditional baseline adjustment to cylindrical
            # ordinates, then convert to XYZ (this may not be exactly how
            # MagProc does things, but it is how BGS documented it)
            h_bas_avg = np.mean(h_bas[filter_iqr(h_bas, threshold=3)])
            d_bas_avg = np.mean(d_bas[filter_iqr(d_bas, threshold=3)])
            z_bas_avg = np.mean(z_bas[filter_iqr(z_bas, threshold=3)])

            # WebAbsolutes defines/generates h differently than USGS residual
            # method spreadsheets; here we ensure that h_trad is the total
            # horizontal field, then use it and declination to get X and Y.
            if obs_code == "DED" or obs_code == "CMO":
                h_trad = h_bas_avg + np.sqrt(hez1_arr[0] ** 2 + hez1_arr[1] ** 2)
            else:
                h_trad = np.sqrt((h_bas_avg + hez1_arr[0]) ** 2 + hez1_arr[1] ** 2)

            # d_trad = d_bas_avg * np.pi/180 + np.arcsin(hez1_arr[1] / h_trad)
            d_trad = (
                d_bas_avg * np.pi / 180 + hez1_arr[1] / h_trad
            )  # small-angle approx.

            x_trad = h_trad * np.cos(d_trad)
            y_trad = h_trad * np.sin(d_trad)
            z_trad = z_bas_avg + hez1_arr[2]

            xyzf_trad_list.append(np.vstack((x_trad, y_trad, z_trad, xyzf[3])))

            # retrieve (Quasi)Definitive xyzf data from Edge server
            factory = EdgeFactory(host=edge_host)
            xyzf = factory.get_timeseries(
                observatory=obs_code,
                interval="minute",
                type="quasi-definitive",
                channels=("X", "Y", "Z", "F"),
                starttime=valid_start,
                endtime=valid_end,
            )

            # place xyzf traces into xyzf matrix
            xyzf = np.vstack((xyzf[0].data, xyzf[1].data, xyzf[2].data, xyzf[3].data))

            # append xyzf to list of outputs for each update interval
            xyzf_def_list.append(xyzf)

            # finally, return array of common times for plotting, etc.
            utc_xyzf_list.append(utc_arr)

        # increment start_UTC
        start_UTC += update_interval

    if validate:
        return (
            utc_list,
            M_composed_list,
            pcwa_list,
            utc_xyzf_list,
            xyzf_trad_list,
            xyzf_adj_list,
            xyzf_def_list,
            utc_bas,
            abs_xyz,
            ord_hez,
            Ms_list,
            weights_list,
        )
    else:
        return utc_list, M_composed_list, pcwa_list


# configuration parameters for all observatories
# (set to None here if you want to use default values)
start_UTC = UTCDateTime("2019-11-01T00:00:00Z")
end_UTC = UTCDateTime("2020-01-31T23:59:00Z")

first_UTC = UTCDateTime("2019-10-01T00:00:00Z")
last_UTC = UTCDateTime("2020-02-29T23:59:00Z")

update_interval = 86400 * 7

M_funcs = [generate_affine_8, generate_affine_6]
memories = [86400 * 100, 86400 * 10]

edge_host = None

# configuration parameters for BOU

# INPUTS
obs_code = "BOU"
start_UTC = start_UTC or UTCDateTime("2015-01-01T00:00:00Z")
end_UTC = end_UTC or UTCDateTime("2015-12-31T23:59:00Z")

# OPTIONS
update_interval = update_interval or 86400 * 7
acausal = False
first_UTC = first_UTC or start_UTC
last_UTC = last_UTC or end_UTC

# This is slowly evolving horizontal rotation, and
# quickly evolving baseline offsets (including Ebase)
M_funcs = M_funcs or [generate_affine_8, generate_affine_6]
memories = memories or [86400 * 100, 86400 * 10]

# path_or_url = '/Volumes/geomag/pub/Caldata/Checked Baseline Data/'
path_or_url = "https://geomag.usgs.gov"

validate = True
edge_host = edge_host or "cwbpub.cr.usgs.gov"

(utc_weekly_007_causal, M_weekly_007_causal, pc_weekly_007_causal,) = do_it_all(
    obs_code,
    start_UTC,
    end_UTC,
    update_interval=update_interval,
    acausal=False,
    interpolate=False,
    first_UTC=first_UTC,
    last_UTC=last_UTC,
    M_funcs=M_funcs,
    memories=memories,
    path_or_url=path_or_url,
    edge_host=edge_host,
)


(utc_weekly_007_acausal, M_weekly_007_acausal, pc_weekly_007_acausal,) = do_it_all(
    obs_code,
    start_UTC,
    end_UTC,
    update_interval=update_interval,
    acausal=True,
    interpolate=True,
    first_UTC=first_UTC,
    last_UTC=last_UTC,
    M_funcs=M_funcs,
    memories=memories,
    path_or_url=path_or_url,
    edge_host=edge_host,
)

(utc_weekly_inf_acausal, M_weekly_inf_acausal, pc_weekly_inf_acausal,) = do_it_all(
    obs_code,
    start_UTC,
    end_UTC,
    update_interval=update_interval,
    acausal=True,
    interpolate=True,
    first_UTC=first_UTC,
    last_UTC=last_UTC,
    M_funcs=M_funcs,
    memories=[np.inf, np.inf],
    path_or_url=path_or_url,
    edge_host=edge_host,
)


(utc_all_inf_acausal, M_all_inf_acausal, pc_all_inf_acausal,) = do_it_all(
    obs_code,
    start_UTC,
    end_UTC,
    update_interval=None,
    acausal=True,
    interpolate=True,
    first_UTC=first_UTC,
    last_UTC=last_UTC,
    M_funcs=M_funcs,
    memories=[np.inf, np.inf],
    path_or_url=path_or_url,
    edge_host=edge_host,
)


short_memory_causal = {
    "utc": utc_weekly_007_causal,
    "M": M_weekly_007_causal,
    "pc": pc_weekly_007_causal,
}
short_memory_acausal = {
    "utc": utc_weekly_007_acausal,
    "M": M_weekly_007_acausal,
    "pc": pc_weekly_007_acausal,
}
weekly_inf_memory_acausal = {
    "utc": utc_weekly_inf_acausal,
    "M": M_weekly_inf_acausal,
    "pc": pc_weekly_inf_acausal,
}
all_inf_memory_acausal = {
    "utc": utc_all_inf_acausal,
    "M": M_all_inf_acausal,
    "pc": pc_all_inf_acausal,
}


with open("short_memory_causal.p", "rb") as fp:
    data = pickle.load(fp)

assert_equal(data, short_memory_causal)

with open("short_memory_acausal.p", "rb") as fp:
    data = pickle.load(fp)

assert_equal(data, short_memory_acausal)

with open("weekly_inf_memory_acausal.p", "rb") as fp:
    data = pickle.load(fp)

assert_equal(data, weekly_inf_memory_acausal)

with open("all_inf_memory_acausal.p", "rb") as fp:
    data = pickle.load(fp)

assert_equal(data, all_inf_memory_acausal)
