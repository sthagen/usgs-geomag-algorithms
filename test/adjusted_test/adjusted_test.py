import json
import numpy as np
from numpy.testing import assert_equal, assert_array_almost_equal
from obspy.core import UTCDateTime

from geomagio.adjusted.SpreadsheetSummaryFactory import SpreadsheetSummaryFactory
from geomagio.adjusted.Affine import Affine
from geomagio.adjusted.Transform import (
    NoConstraints,
    ZRotationShear,
    ZRotationHscale,
    ZRotationHscaleZbaseline,
    RotationTranslation3D,
    Rescale3D,
    TranslateOrigins,
    ShearYZ,
    RotationTranslationXY,
    QRFactorization,
)

from geomagio.residual.WebAbsolutesFactory import WebAbsolutesFactory


def get_spreadsheet_directory_readings(path, observatory, starttime, endtime):
    ssf = SpreadsheetSummaryFactory(base_directory=path)
    readings = ssf.get_readings(
        observatory=observatory, starttime=starttime, endtime=endtime
    )
    return readings


def get_spreadsheet_readings(path):
    ssf = SpreadsheetSummaryFactory()
    readings = ssf.parse_spreadsheet(path=path)
    return readings


def test_DED20202200248_summary():
    readings = get_spreadsheet_readings(path="etc/adjusted/Caldata/DED20202200248.xlsm")
    for reading in readings:
        assert_equal(reading.metadata["instrument"], 300611)
        assert_equal(reading.pier_correction, -0.5)
        assert_equal(reading.metadata["observatory"], "DED")


def test_DED_summaries():
    readings = get_spreadsheet_directory_readings(
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
    assert_equal(len(readings), 33)


def get_sythetic_variables():
    with open("etc/adjusted/synthetic_variables.json") as file:
        variables = json.load(file)
    ordinates = np.array([variables["h_ord"], variables["e_ord"], variables["z_ord"]])
    absolutes = np.array([variables["x_abs"], variables["y_abs"], variables["z_abs"]])
    return ordinates, absolutes


def test_Affine_result():
    # load results
    with open("etc/adjusted/synthetic_results.json") as file:
        expected = json.load(file)

    ordinates, absolutes = get_sythetic_variables()

    # numbers in keys pertain to method numbers from original documentation(generate_affine_...)
    assert_array_almost_equal(
        NoConstraints().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=None,
        ),
        np.array(expected["zero"]),
        decimal=6,
    )
    assert_array_almost_equal(
        ZRotationShear().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=None,
        ),
        np.array(expected["one"]),
        decimal=6,
    )
    assert_array_almost_equal(
        ZRotationHscale().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=None,
        ),
        np.array(expected["two"]),
        decimal=6,
    )
    assert_array_almost_equal(
        ZRotationHscaleZbaseline().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=None,
        ),
        np.array(expected["three"]),
        decimal=6,
    )
    assert_array_almost_equal(
        RotationTranslation3D().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=None,
        ),
        expected["four"],
        decimal=6,
    )
    assert_array_almost_equal(
        Rescale3D().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=None,
        ),
        expected["five"],
        decimal=6,
    )
    assert_array_almost_equal(
        TranslateOrigins().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=None,
        ),
        expected["six"],
        decimal=6,
    )
    assert_array_almost_equal(
        ShearYZ().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=None,
        ),
        expected["seven"],
        decimal=6,
    )
    assert_array_almost_equal(
        RotationTranslationXY().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=None,
        ),
        expected["eight"],
        decimal=6,
    )
    assert_array_almost_equal(
        QRFactorization().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
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
    short_causal = Affine(
        observatory="BOU",
        starttime=UTCDateTime("2019-11-01T00:00:00Z"),
        endtime=UTCDateTime("2020-01-31T23:59:00Z"),
    ).calculate(readings=readings)

    result = format_result([adjusted_matrix.matrix for adjusted_matrix in short_causal])

    with open("etc/adjusted/short_memory_causal.json", "r") as file:
        expected = json.load(file)

    assert_array_almost_equal(result, expected["M"], decimal=3)


def test_BOU201911202001_short_acausal():
    readings = get_readings_BOU201911202001()
    short_acausal = Affine(
        observatory="BOU",
        starttime=UTCDateTime("2019-11-01T00:00:00Z"),
        endtime=UTCDateTime("2020-01-31T23:59:00Z"),
        acausal=True,
    ).calculate(
        readings=readings,
    )

    result = format_result(
        [adjusted_matrix.matrix for adjusted_matrix in short_acausal]
    )

    with open("etc/adjusted/short_memory_acausal.json", "r") as file:
        expected = json.load(file)

    assert_array_almost_equal(result, expected["M"], decimal=3)


def test_BOU201911202001_infinite_weekly():
    readings = get_readings_BOU201911202001()
    infinite_weekly = Affine(
        observatory="BOU",
        starttime=UTCDateTime("2019-11-01T00:00:00Z"),
        endtime=UTCDateTime("2020-01-31T23:59:00Z"),
        acausal=True,
        transforms=[
            RotationTranslationXY(memory=np.inf),
            TranslateOrigins(memory=np.inf),
        ],
    ).calculate(
        readings=readings,
    )

    result = format_result(
        [adjusted_matrix.matrix for adjusted_matrix in infinite_weekly]
    )

    with open("etc/adjusted/weekly_inf_memory_acausal.json", "r") as file:
        expected = json.load(file)

    assert_array_almost_equal(result, expected["M"], decimal=3)


def test_BOU201911202001_infinite_one_interval():
    readings = get_readings_BOU201911202001()
    infinite_one_interval = Affine(
        observatory="BOU",
        starttime=UTCDateTime("2019-11-01T00:00:00Z"),
        endtime=UTCDateTime("2020-01-31T23:59:00Z"),
        acausal=True,
        transforms=[
            RotationTranslationXY(memory=np.inf),
            TranslateOrigins(memory=np.inf),
        ],
        update_interval=None,
    ).calculate(
        readings=readings,
    )

    result = format_result(
        [adjusted_matrix.matrix for adjusted_matrix in infinite_one_interval]
    )

    with open("etc/adjusted/all_inf_memory_acausal.json", "r") as file:
        expected = json.load(file)

    assert_array_almost_equal(result, expected["M"], decimal=3)


def test_CMO2015_causal():
    readings = get_spreadsheet_directory_readings(
        observatory="CMO",
        starttime=UTCDateTime("2015-01-01T00:00:00Z"),
        endtime=UTCDateTime("2015-12-31T23:59:00Z"),
        path="etc/adjusted/Caldata/",
    )

    causal = Affine(
        observatory="CMO",
        starttime=UTCDateTime("2015-02-01T00:00:00Z"),
        endtime=UTCDateTime("2015-11-27T23:59:00Z"),
        acausal=False,
    ).calculate(
        readings=readings,
    )

    result = format_result([adjusted_matrix.matrix for adjusted_matrix in causal])

    with open("etc/adjusted/causal.json", "r") as file:
        expected = json.load(file)

    assert_array_almost_equal(result, expected["M"], decimal=3)


def test_CMO2015_acausal():
    readings = get_spreadsheet_directory_readings(
        observatory="CMO",
        starttime=UTCDateTime("2015-01-01T00:00:00Z"),
        endtime=UTCDateTime("2015-12-31T23:59:00Z"),
        path="etc/adjusted/Caldata/",
    )

    causal = Affine(
        observatory="CMO",
        starttime=UTCDateTime("2015-02-01T00:00:00Z"),
        endtime=UTCDateTime("2015-11-27T23:59:00Z"),
        acausal=True,
    ).calculate(
        readings=readings,
    )

    result = format_result([adjusted_matrix.matrix for adjusted_matrix in causal])

    with open("etc/adjusted/acausal.json", "r") as file:
        expected = json.load(file)

    assert_array_almost_equal(result, expected["M"], decimal=3)


def test_CMO2015_infinite_weekly():
    readings = get_spreadsheet_directory_readings(
        observatory="CMO",
        starttime=UTCDateTime("2015-01-01T00:00:00Z"),
        endtime=UTCDateTime("2015-12-31T23:59:00Z"),
        path="etc/adjusted/Caldata/",
    )

    causal = Affine(
        observatory="CMO",
        starttime=UTCDateTime("2015-02-01T00:00:00Z"),
        endtime=UTCDateTime("2015-11-27T23:59:00Z"),
        transforms=[
            RotationTranslationXY(memory=np.inf),
            TranslateOrigins(memory=np.inf),
        ],
        acausal=True,
    ).calculate(
        readings=readings,
    )

    result = format_result([adjusted_matrix.matrix for adjusted_matrix in causal])

    with open("etc/adjusted/weekly_inf.json", "r") as file:
        expected = json.load(file)

    assert_array_almost_equal(result, expected["M"], decimal=3)


def test_CMO2015_infinite_one_interval():
    readings = get_spreadsheet_directory_readings(
        observatory="CMO",
        starttime=UTCDateTime("2015-01-01T00:00:00Z"),
        endtime=UTCDateTime("2015-12-31T23:59:00Z"),
        path="etc/adjusted/Caldata/",
    )

    causal = Affine(
        observatory="CMO",
        starttime=UTCDateTime("2015-02-01T00:00:00Z"),
        endtime=UTCDateTime("2015-11-27T23:59:00Z"),
        transforms=[
            RotationTranslationXY(memory=np.inf),
            TranslateOrigins(memory=np.inf),
        ],
        acausal=True,
        update_interval=None,
    ).calculate(
        readings=readings,
    )

    result = format_result([adjusted_matrix.matrix for adjusted_matrix in causal])

    with open("etc/adjusted/inf_one_interval.json", "r") as file:
        expected = json.load(file)

    assert_array_almost_equal(result, expected["M"][0], decimal=3)
