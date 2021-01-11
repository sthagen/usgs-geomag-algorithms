from geomagio.residual.WebAbsolutesFactory import WebAbsolutesFactory
import json
import numpy as np
from numpy.testing import assert_equal, assert_array_almost_equal
from obspy.core import UTCDateTime
import pytest

from geomagio.adjusted.SpreadsheetSummaryFactory import SpreadsheetSummaryFactory
from geomagio.adjusted.Generator import Generator
from geomagio.adjusted.GeneratorType import GeneratorType
from geomagio.adjusted.Affine import Affine
from geomagio.adjusted.Transform import (
    NoConstraints,
    ZRotation,
    ZRotationHscale,
    ZRotationHscaleZbaseline,
    RotationTranslation3D,
    Rescale3D,
    TranslateOrigins,
    ShearYZ,
    RotationTranslationXY,
    QRFactorization,
)
from geomagio.adjusted.Calculation import (
    calculate,
)


H_ORD = np.array(
    [
        1.79289322,
        1.83983806,
        1.91024109,
        2.51489726,
        1.78952971,
        2.81157403,
        2.36417497,
        2.43864844,
        3.25364394,
        2.27479228,
        3.47800226,
        2.95694665,
        3.03482926,
        3.84541634,
        2.92632734,
        4.01635411,
        3.59456862,
        3.69312428,
        4.27043672,
        3.82250402,
    ]
)

E_ORD = np.array(
    [
        4.46592583,
        3.99414122,
        4.86042918,
        4.08398446,
        4.06789278,
        4.89701546,
        3.29221074,
        4.91313376,
        3.76430406,
        3.77979418,
        4.76896396,
        2.98259167,
        4.69899703,
        3.54330923,
        3.56461527,
        4.43474537,
        2.93993354,
        4.24945532,
        3.43005774,
        3.46078181,
    ]
)

Z_ORD = np.array(
    [
        2.24118095,
        2.17339265,
        2.88988358,
        1.74783897,
        3.18842428,
        2.36825251,
        2.39116112,
        3.56453372,
        1.85923781,
        3.7224498,
        2.71235632,
        2.74095046,
        3.96752743,
        2.26503334,
        4.0367477,
        3.13361064,
        3.18331114,
        4.12716967,
        3.00224898,
        4.03024472,
    ]
)

X_ABS = np.array(
    [
        -1.00000000e00,
        -8.99979996e-01,
        -7.99959992e-01,
        -6.99939988e-01,
        -5.99919984e-01,
        -4.99899980e-01,
        -3.99879976e-01,
        -2.99859972e-01,
        -1.99839968e-01,
        -9.98199640e-02,
        2.00040008e-04,
        1.00220044e-01,
        2.00240048e-01,
        3.00260052e-01,
        4.00280056e-01,
        5.00300060e-01,
        6.00320064e-01,
        7.00340068e-01,
        8.00360072e-01,
        9.00380076e-01,
    ]
)

Y_ABS = np.array(
    [
        0.0,
        -0.35248241,
        0.18456572,
        0.22223661,
        -0.64867776,
        0.86607699,
        -0.7390734,
        0.29000341,
        0.30840017,
        -0.80892729,
        0.99997154,
        -0.80006479,
        0.29431378,
        0.30363751,
        -0.74702288,
        0.8657967,
        -0.64130022,
        0.211858,
        0.19298425,
        -0.35563497,
    ]
)

Z_ABS = np.array(
    [
        0.0,
        -0.25649982,
        0.57096366,
        -0.67874509,
        0.46830885,
        0.0032657,
        -0.54209456,
        0.90883553,
        -0.93002867,
        0.57937261,
        0.00754126,
        -0.59148311,
        0.93449629,
        -0.904239,
        0.53078497,
        0.00979431,
        -0.47785966,
        0.68164505,
        -0.56760976,
        0.25067805,
    ]
)


def get_spreadsheet_readings(path, observatory, starttime, endtime):
    ssf = SpreadsheetSummaryFactory(base_directory=path)
    readings = ssf.get_readings(
        observatory=observatory, starttime=starttime, endtime=endtime
    )
    return readings


def get_spreadsheet_reading(path):
    ssf = SpreadsheetSummaryFactory()
    reading = ssf.parse_spreadsheet(path=path)
    return reading


def test_DED20202200248_summary():
    reading = get_spreadsheet_reading(path="etc/adjusted/Caldata/DED20202200248.xlsm")
    assert_equal(reading.metadata["instrument"], 300611)
    assert_equal(reading.pier_correction, -0.5)
    assert_equal(reading.metadata["observatory"], "DED")
    assert_equal(reading.metadata["observer"], "KR")
    assert_equal(reading.metadata["date"], "20200807")
    assert_array_almost_equal(
        [absolute.baseline for absolute in reading.absolutes],
        [1028.93, -143.83, 21.78],
        decimal=2,
    )
    assert_array_almost_equal(
        [absolute.absolute for absolute in reading.absolutes],
        [16.25, 9107.75, 56568.35],
        decimal=2,
    )


def test_Caldata_summaries():
    readings = get_spreadsheet_readings(
        path="etc/adjusted/Caldata",
        observatory="DED",
        starttime=UTCDateTime("2020-01-01"),
        endtime=UTCDateTime("2020-12-31"),
    )
    for reading in readings:
        assert_equal(reading.metadata["observatory"], "DED")
        assert_equal(reading.metadata["instrument"], 300611)
        assert_equal(reading.pier_correction, -0.5)
    # assert that the number of readings equals the number of file within directory
    assert_equal(len(readings), 10)


def get_affine_result(type, weights=None):
    matrix = type.calculate_matrix(
        ord_hez=(H_ORD, E_ORD, Z_ORD),
        abs_xyz=(X_ABS, Y_ABS, Z_ABS),
        weights=weights,
    )
    return matrix


def test_Affine_result():
    # load results
    with open("etc/adjusted/synthetic_results.json") as file:
        expected = json.load(file)
    # numbers in keys pertain to method numbers from original documentation(generate_affine_...)
    assert_array_almost_equal(
        NoConstraints().calculate(
            ordinates=(H_ORD, E_ORD, Z_ORD),
            absolutes=(X_ABS, Y_ABS, Z_ABS),
            weights=None,
        ),
        np.array(expected["zero"]),
        decimal=6,
    )
    assert_array_almost_equal(
        ZRotation().calculate(
            ordinates=(H_ORD, E_ORD, Z_ORD),
            absolutes=(X_ABS, Y_ABS, Z_ABS),
            weights=None,
        ),
        np.array(expected["one"]),
        decimal=6,
    )
    assert_array_almost_equal(
        ZRotationHscale().calculate(
            ordinates=(H_ORD, E_ORD, Z_ORD),
            absolutes=(X_ABS, Y_ABS, Z_ABS),
            weights=None,
        ),
        np.array(expected["two"]),
        decimal=6,
    )
    assert_array_almost_equal(
        ZRotationHscaleZbaseline().calculate(
            ordinates=(H_ORD, E_ORD, Z_ORD),
            absolutes=(X_ABS, Y_ABS, Z_ABS),
            weights=None,
        ),
        np.array(expected["three"]),
        decimal=6,
    )
    assert_array_almost_equal(
        RotationTranslation3D().calculate(
            ordinates=(H_ORD, E_ORD, Z_ORD),
            absolutes=(X_ABS, Y_ABS, Z_ABS),
            weights=None,
        ),
        expected["four"],
        decimal=6,
    )
    assert_array_almost_equal(
        Rescale3D().calculate(
            ordinates=(H_ORD, E_ORD, Z_ORD),
            absolutes=(X_ABS, Y_ABS, Z_ABS),
            weights=None,
        ),
        expected["five"],
        decimal=6,
    )
    assert_array_almost_equal(
        TranslateOrigins().calculate(
            ordinates=(H_ORD, E_ORD, Z_ORD),
            absolutes=(X_ABS, Y_ABS, Z_ABS),
            weights=None,
        ),
        expected["six"],
        decimal=6,
    )
    assert_array_almost_equal(
        ShearYZ().calculate(
            ordinates=(H_ORD, E_ORD, Z_ORD),
            absolutes=(X_ABS, Y_ABS, Z_ABS),
            weights=None,
        ),
        expected["seven"],
        decimal=6,
    )
    assert_array_almost_equal(
        RotationTranslationXY().calculate(
            ordinates=(H_ORD, E_ORD, Z_ORD),
            absolutes=(X_ABS, Y_ABS, Z_ABS),
            weights=None,
        ),
        expected["eight"],
        decimal=6,
    )
    assert_array_almost_equal(
        QRFactorization().calculate(
            ordinates=(H_ORD, E_ORD, Z_ORD),
            absolutes=(X_ABS, Y_ABS, Z_ABS),
            weights=None,
        ),
        expected["nine"],
        decimal=6,
    )


def format_result(result) -> dict:
    if len(result) != 1:
        Ms = []
        for M in result:
            m = []
            for row in M:
                m.append(list(row))
            Ms.append(m)
    else:
        Ms = [list(row) for row in result[0]]
    return Ms


def get_readings_BOU201911202001():
    readings = WebAbsolutesFactory().get_readings(
        observatory="BOU",
        starttime=UTCDateTime("2019-10-01T00:00:00Z"),
        endtime=UTCDateTime("2020-02-29T23:59:00Z"),
    )
    return readings


def test_BOU201911202001_short_causal():
    readings = get_readings_BOU201911202001()
    affine = Affine(
        observatory="BOU",
        starttime=UTCDateTime("2019-11-01T00:00:00Z"),
        endtime=UTCDateTime("2020-01-31T23:59:00Z"),
    )
    calculate(
        affine=affine,
        readings=readings,
    )

    short_causal = format_result(affine.matrices)

    with open("etc/adjusted/short_memory_causal.json", "r") as file:
        expected = json.load(file)

    assert_array_almost_equal(short_causal, expected["M"], decimal=3)


def test_BOU201911202001_short_acausal():
    readings = get_readings_BOU201911202001()
    affine = Affine(
        observatory="BOU",
        starttime=UTCDateTime("2019-11-01T00:00:00Z"),
        endtime=UTCDateTime("2020-01-31T23:59:00Z"),
        acausal=True,
    )
    calculate(
        affine=affine,
        readings=readings,
    )

    short_acausal = format_result(affine.matrices)

    with open("etc/adjusted/short_memory_acausal.json", "r") as file:
        expected = json.load(file)

    assert_array_almost_equal(short_acausal, expected["M"], decimal=3)


def test_BOU201911202001_infinite_weekly():
    readings = get_readings_BOU201911202001()
    affine = Affine(
        observatory="BOU",
        starttime=UTCDateTime("2019-11-01T00:00:00Z"),
        endtime=UTCDateTime("2020-01-31T23:59:00Z"),
        acausal=True,
        generators=[
            Generator(type=GeneratorType.ROTATION_TRANSLATION_XY, memory=np.inf),
            Generator(type=GeneratorType.TRANSLATE_ORIGINS, memory=np.inf),
        ],
    )
    calculate(
        affine=affine,
        readings=readings,
    )

    weekly_inf_acausal = format_result(affine.matrices)

    with open("etc/adjusted/weekly_inf_memory_acausal.json", "r") as file:
        expected = json.load(file)

    assert_array_almost_equal(weekly_inf_acausal, expected["M"], decimal=3)


def test_BOU201911202001_infinite_one_interval():
    readings = get_readings_BOU201911202001()
    affine = Affine(
        observatory="BOU",
        starttime=UTCDateTime("2019-11-01T00:00:00Z"),
        endtime=UTCDateTime("2020-01-31T23:59:00Z"),
        acausal=True,
        generators=[
            Generator(type=GeneratorType.ROTATION_TRANSLATION_XY, memory=np.inf),
            Generator(type=GeneratorType.TRANSLATE_ORIGINS, memory=np.inf),
        ],
        update_interval=None,
    )
    calculate(
        affine=affine,
        readings=readings,
    )

    all_inf_acausal = format_result(affine.matrices)

    with open("etc/adjusted/all_inf_memory_acausal.json", "r") as file:
        expected = json.load(file)

    assert_array_almost_equal(all_inf_acausal, expected["M"], decimal=3)
