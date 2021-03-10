from geomagio.adjusted import AdjustedMatrix
from geomagio.algorithm import AdjustedAlgorithm
import geomagio.iaga2002 as i2
from numpy.testing import assert_almost_equal, assert_array_equal, assert_equal


def test_construct():
    """algorithm_test.AdjustedAlgorithm_test.test_construct()"""
    # load adjusted data transform matrix and pier correction
    a = AdjustedAlgorithm(statefile="etc/adjusted/adjbou_state_.json")

    assert_almost_equal(actual=a.matrix.matrix[0][0], desired=9.83427577e-01, decimal=6)

    assert_equal(actual=a.matrix.pier_correction, desired=-22)


def assert_streams_almost_equal(adjusted, expected, channels):
    for channel in channels:
        assert_almost_equal(
            actual=adjusted.select(channel=channel)[0].data,
            desired=expected.select(channel=channel)[0].data,
            decimal=2,
        )


def test_process_XYZF_AdjustedMatrix():
    """algorithm_test.AdjustedAlgorithm_test.test_process_XYZF_AdjustedMatrix()

    Check adjusted data processing versus files generated from
    original script
    """
    # Initiate algorithm with AdjustedMatrix object
    a = AdjustedAlgorithm(
        matrix=AdjustedMatrix(
            matrix=[
                [
                    0.9834275767090617,
                    -0.15473074200902157,
                    0.027384986324932026,
                    -1276.164681191976,
                ],
                [
                    0.16680172992706568,
                    0.987916201012128,
                    -0.0049868332295851525,
                    -0.8458192581350419,
                ],
                [
                    -0.006725053082782385,
                    -0.011809351484171948,
                    0.9961869012493976,
                    905.3800885796844,
                ],
                [0, 0, 0, 1],
            ],
            pier_correction=-22,
        )
    )

    # load boulder Jan 16 files from /etc/ directory
    with open("etc/adjusted/BOU201601vmin.min") as f:
        raw = i2.IAGA2002Factory().parse_string(f.read())
    with open("etc/adjusted/BOU201601adj.min") as f:
        expected = i2.IAGA2002Factory().parse_string(f.read())

    # process hezf (raw) channels with loaded transform
    adjusted = a.process(raw)

    assert_streams_almost_equal(
        adjusted=adjusted, expected=expected, channels=["X", "Y", "Z", "F"]
    )


def test_process_reverse_polarity_AdjustedMatrix():
    """algorithm_test.AdjustedAlgorithm_test.test_process_reverse_polarity_AdjustedMatrix()

    Check adjusted data processing versus files generated from
    original script. Tests reverse polarity martix.
    """
    # Initiate algorithm with AdjustedMatrix object
    a = AdjustedAlgorithm(
        matrix=AdjustedMatrix(
            matrix=[
                [-1, 0, 0],
                [0, -1, 0],
                [0, 0, 1],
            ],
            pier_correction=-22,
        ),
        inchannels=["H", "E"],
        outchannels=["H", "E"],
    )

    # load boulder May 20 files from /etc/ directory
    with open("etc/adjusted/BOU202005vmin.min") as f:
        raw = i2.IAGA2002Factory().parse_string(f.read())
    with open("etc/adjusted/BOU202005adj.min") as f:
        expected = i2.IAGA2002Factory().parse_string(f.read())

    # process he(raw) channels with loaded transform
    adjusted = a.process(raw)

    assert_streams_almost_equal(
        adjusted=adjusted, expected=expected, channels=["H", "E"]
    )


def test_process_XYZF_statefile():
    """algorithm_test.AdjustedAlgorithm_test.test_process_XYZF_statefile()

    Check adjusted data processing versus files generated from
    original script

    Uses statefile to generate AdjustedMatrix
    """
    # load adjusted data transform matrix and pier correction
    a = AdjustedAlgorithm(statefile="etc/adjusted/adjbou_state_.json")

    # load boulder Jan 16 files from /etc/ directory
    with open("etc/adjusted/BOU201601vmin.min") as f:
        raw = i2.IAGA2002Factory().parse_string(f.read())
    with open("etc/adjusted/BOU201601adj.min") as f:
        expected = i2.IAGA2002Factory().parse_string(f.read())

    # process hezf (raw) channels with loaded transform
    adjusted = a.process(raw)

    assert_streams_almost_equal(
        adjusted=adjusted, expected=expected, channels=["X", "Y", "Z", "F"]
    )


def test_process_reverse_polarity_statefile():
    """algorithm_test.AdjustedAlgorithm_test.test_process_reverse_polarity_statefile()

    Check adjusted data processing versus files generated from
    original script. Tests reverse polarity martix.

    Uses statefile to generate AdjustedMatrix
    """
    # load adjusted data transform matrix and pier correction
    a = AdjustedAlgorithm(
        statefile="etc/adjusted/adjbou_state_HE_.json",
        inchannels=["H", "E"],
        outchannels=["H", "E"],
    )

    # load boulder May 20 files from /etc/ directory
    with open("etc/adjusted/BOU202005vmin.min") as f:
        raw = i2.IAGA2002Factory().parse_string(f.read())
    with open("etc/adjusted/BOU202005adj.min") as f:
        expected = i2.IAGA2002Factory().parse_string(f.read())

    # process he(raw) channels with loaded transform
    adjusted = a.process(raw)

    assert_streams_almost_equal(
        adjusted=adjusted, expected=expected, channels=["H", "E"]
    )


def test_process_no_statefile():
    """algorithm_test.AdjustedAlgorithm_test.test_process_no_statefile()

    Check adjusted data processing versus raw data

    Uses default AdjustedMatrix with identity transform
    """
    # initialize adjusted algorithm with no statefile
    a = AdjustedAlgorithm()
    # load boulder Jan 16 files from /etc/ directory
    with open("etc/adjusted/BOU201601vmin.min") as f:
        raw = i2.IAGA2002Factory().parse_string(f.read())
    # process hezf (raw) channels with identity transform
    adjusted = a.process(raw)
    for i in range(len(adjusted)):
        assert_array_equal(adjusted[i].data, raw[i].data)
