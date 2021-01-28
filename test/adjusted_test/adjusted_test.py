import json
import numpy as np
from numpy.testing import assert_equal, assert_array_almost_equal, assert_array_less
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


def test_CMO_summaries():
    starttime = UTCDateTime("2015-04-01")
    endtime = UTCDateTime("2015-06-15")
    readings = get_spreadsheet_directory_readings(
        path="etc/adjusted/Caldata",
        observatory="CMO",
        starttime=starttime,
        endtime=endtime,
    )
    for reading in readings:
        assert_equal(reading.metadata["observatory"], "CMO")
        assert_equal(reading.metadata["instrument"], 200803)
        assert_equal(reading.pier_correction, 10.5)
    assert_equal(len(readings), 26)

    assert readings[0].time > starttime
    assert readings[-1].time < endtime


def get_sythetic_variables():
    with open("etc/adjusted/synthetic.json") as file:
        data = json.load(file)
    variables = data["variables"]
    ordinates = np.array([variables["h_ord"], variables["e_ord"], variables["z_ord"]])
    absolutes = np.array([variables["x_abs"], variables["y_abs"], variables["z_abs"]])
    weights = np.arange(0, len(ordinates[0]))
    return ordinates, absolutes, weights


def get_expected_synthetic_result(key):
    with open("etc/adjusted/synthetic.json") as file:
        expected = json.load(file)
    return expected["results"][key]


def test_NoConstraints_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        NoConstraints().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("NoConstraints"),
        decimal=3,
    )


def test_ZRotationShear_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        ZRotationShear().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("ZRotationShear"),
        decimal=3,
    )


def test_ZRotationHscale_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        ZRotationHscale().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("ZRotationHscale"),
        decimal=3,
    )


def test_ZRotationHscaleZbaseline_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        ZRotationHscaleZbaseline().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("ZRotationHscaleZbaseline"),
        decimal=3,
    )


def test_RotationTranslation3D_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        RotationTranslation3D().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("RotationTranslation3D"),
        decimal=3,
    )


def test_Rescale3D_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        Rescale3D().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("Rescale3D"),
        decimal=3,
    )


def test_TranslateOrigins_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        TranslateOrigins().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("TranslateOrigins"),
        decimal=3,
    )


def test_ShearYZ_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        ShearYZ().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("ShearYZ"),
        decimal=3,
    )


def test_RotationTranslationXY_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        RotationTranslationXY().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("RotationTranslationXY"),
        decimal=3,
    )


def test_QRFactorization_synthetic():
    ordinates, absolutes, weights = get_sythetic_variables()
    assert_array_almost_equal(
        QRFactorization().calculate(
            ordinates=ordinates,
            absolutes=absolutes,
            weights=weights,
        ),
        get_expected_synthetic_result("QRFactorization"),
        decimal=3,
    )


def format_result(result) -> dict:
    Ms = []
    for M in result:
        m = []
        for row in M:
            m.append(list(row))
        Ms.append(m)
    return Ms


def get_excpected_matrices(observatory, key):
    with open(f"etc/adjusted/{observatory}_expected.json", "r") as file:
        expected = json.load(file)
    return expected[key]


def get_readings_BOU201911202001():
    readings = WebAbsolutesFactory().get_readings(
        observatory="BOU",
        starttime=UTCDateTime("2019-10-01T00:00:00Z"),
        endtime=UTCDateTime("2020-02-29T23:59:00Z"),
    )
    return readings


def test_BOU201911202001_short_causal():
    readings = get_readings_BOU201911202001()

    starttime = UTCDateTime("2019-11-01T00:00:00Z")
    endtime = UTCDateTime("2020-01-31T23:59:00Z")

    update_interval = 86400 * 7

    result = Affine(
        observatory="BOU",
        starttime=starttime,
        endtime=endtime,
        update_interval=update_interval,
    ).calculate(readings=readings)

    matrices = format_result([adjusted_matrix.matrix for adjusted_matrix in result])
    metrics = [adjusted_matrix.metrics for adjusted_matrix in result]
    expected_matrices = get_excpected_matrices("BOU", "short_causal")
    for i in range(len(matrices)):
        assert_array_almost_equal(
            matrices[i],
            expected_matrices[i],
            decimal=3,
            err_msg=f"Matrix {i} not equal",
        )
    assert_equal(len(matrices), ((endtime - starttime) // update_interval) + 1)


def test_BOU201911202001_short_acausal():
    readings = get_readings_BOU201911202001()

    starttime = UTCDateTime("2019-11-01T00:00:00Z")
    endtime = UTCDateTime("2020-01-31T23:59:00Z")

    update_interval = 86400 * 7

    result = Affine(
        observatory="BOU",
        starttime=starttime,
        endtime=endtime,
        update_interval=update_interval,
        acausal=True,
    ).calculate(
        readings=readings,
    )

    matrices = format_result([adjusted_matrix.matrix for adjusted_matrix in result])
    metrics = [adjusted_matrix.metrics for adjusted_matrix in result]
    expected_matrices = get_excpected_matrices("BOU", "short_acausal")
    for i in range(len(matrices)):
        assert_array_almost_equal(
            matrices[i],
            expected_matrices[i],
            decimal=3,
            err_msg=f"Matrix {i} not equal",
        )
    assert_equal(len(matrices), ((endtime - starttime) // update_interval) + 1)


def test_BOU201911202001_infinite_weekly():
    readings = get_readings_BOU201911202001()

    starttime = UTCDateTime("2019-11-01T00:00:00Z")
    endtime = UTCDateTime("2020-01-31T23:59:00Z")

    update_interval = 86400 * 7

    result = Affine(
        observatory="BOU",
        starttime=starttime,
        endtime=endtime,
        update_interval=update_interval,
        acausal=True,
        transforms=[
            RotationTranslationXY(memory=np.inf),
            TranslateOrigins(memory=np.inf),
        ],
    ).calculate(
        readings=readings,
    )

    matrices = format_result([adjusted_matrix.matrix for adjusted_matrix in result])
    metrics = [adjusted_matrix.metrics for adjusted_matrix in result]
    expected_matrices = get_excpected_matrices("BOU", "inf_weekly")
    for i in range(len(matrices)):
        assert_array_almost_equal(
            matrices[i],
            expected_matrices[i],
            decimal=3,
            err_msg=f"Matrix {i} not equal",
        )
    assert_equal(len(matrices), ((endtime - starttime) // update_interval) + 1)


def test_BOU201911202001_infinite_one_interval():
    readings = get_readings_BOU201911202001()
    result = Affine(
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

    matrices = format_result([adjusted_matrix.matrix for adjusted_matrix in result])
    metrics = [adjusted_matrix.metrics for adjusted_matrix in result]
    expected_matrices = get_excpected_matrices("BOU", "inf_one_interval")
    for i in range(len(matrices)):
        assert_array_almost_equal(
            matrices[i],
            expected_matrices[i],
            decimal=3,
            err_msg=f"Matrix {i} not equal",
        )
    assert_equal(len(matrices), 1)


def test_CMO2015_causal():
    readings = get_spreadsheet_directory_readings(
        observatory="CMO",
        starttime=UTCDateTime("2015-01-01T00:00:00Z"),
        endtime=UTCDateTime("2015-12-31T23:59:00Z"),
        path="etc/adjusted/Caldata/",
    )
    assert len(readings) == 146

    starttime = UTCDateTime("2015-02-01T00:00:00Z")
    endtime = UTCDateTime("2015-11-27T23:59:00Z")

    update_interval = 86400 * 7

    result = Affine(
        observatory="CMO",
        starttime=starttime,
        endtime=endtime,
        update_interval=update_interval,
    ).calculate(
        readings=readings,
    )

    matrices = format_result([adjusted_matrix.matrix for adjusted_matrix in result])
    metrics = [adjusted_matrix.metrics for adjusted_matrix in result]
    expected_matrices = get_excpected_matrices("CMO", "short_causal")
    for i in range(len(matrices)):
        assert_array_almost_equal(
            matrices[i],
            expected_matrices[i],
            decimal=3,
            err_msg=f"Matrix {i} not equal",
        )
    assert_equal(len(matrices), ((endtime - starttime) // update_interval) + 1)


def test_CMO2015_acausal():
    readings = get_spreadsheet_directory_readings(
        observatory="CMO",
        starttime=UTCDateTime("2015-01-01T00:00:00Z"),
        endtime=UTCDateTime("2015-12-31T23:59:00Z"),
        path="etc/adjusted/Caldata/",
    )
    assert len(readings) == 146

    starttime = UTCDateTime("2015-02-01T00:00:00Z")
    endtime = UTCDateTime("2015-11-27T23:59:00Z")

    update_interval = 86400 * 7

    result = Affine(
        observatory="CMO",
        starttime=starttime,
        endtime=endtime,
        update_interval=update_interval,
        acausal=True,
    ).calculate(
        readings=readings,
    )

    matrices = format_result([adjusted_matrix.matrix for adjusted_matrix in result])
    metrics = [adjusted_matrix.metrics for adjusted_matrix in result]
    expected_matrices = get_excpected_matrices("CMO", "short_acausal")
    for i in range(len(matrices)):
        assert_array_almost_equal(
            matrices[i],
            expected_matrices[i],
            decimal=3,
            err_msg=f"Matrix {i} not equal",
        )
    assert_equal(len(matrices), ((endtime - starttime) // update_interval) + 1)


def test_CMO2015_infinite_weekly():
    readings = get_spreadsheet_directory_readings(
        observatory="CMO",
        starttime=UTCDateTime("2015-01-01T00:00:00Z"),
        endtime=UTCDateTime("2015-12-31T23:59:00Z"),
        path="etc/adjusted/Caldata/",
    )
    assert len(readings) == 146

    starttime = UTCDateTime("2015-02-01T00:00:00Z")
    endtime = UTCDateTime("2015-11-27T23:59:00Z")

    update_interval = 86400 * 7

    result = Affine(
        observatory="CMO",
        starttime=starttime,
        endtime=endtime,
        transforms=[
            RotationTranslationXY(memory=np.inf),
            TranslateOrigins(memory=np.inf),
        ],
        update_interval=update_interval,
        acausal=True,
    ).calculate(
        readings=readings,
    )

    matrices = format_result([adjusted_matrix.matrix for adjusted_matrix in result])
    metrics = [adjusted_matrix.metrics for adjusted_matrix in result]
    expected_matrices = get_excpected_matrices("CMO", "inf_weekly")
    for i in range(len(matrices)):
        assert_array_almost_equal(
            matrices[i],
            expected_matrices[i],
            decimal=3,
            err_msg=f"Matrix {i} not equal",
        )
    assert_equal(len(matrices), ((endtime - starttime) // update_interval) + 1)


def test_CMO2015_infinite_one_interval():
    readings = get_spreadsheet_directory_readings(
        observatory="CMO",
        starttime=UTCDateTime("2015-01-01T00:00:00Z"),
        endtime=UTCDateTime("2015-12-31T23:59:00Z"),
        path="etc/adjusted/Caldata/",
    )

    assert len(readings) == 146

    result = Affine(
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

    matrices = format_result([adjusted_matrix.matrix for adjusted_matrix in result])
    metrics = [adjusted_matrix.metrics for adjusted_matrix in result]
    expected_matrices = get_excpected_matrices("CMO", "inf_one_interval")
    for i in range(len(matrices)):
        assert_array_almost_equal(
            matrices[i],
            expected_matrices[i],
            decimal=3,
            err_msg=f"Matrix {i} not equal",
        )

    assert_equal(len(matrices), 1)
