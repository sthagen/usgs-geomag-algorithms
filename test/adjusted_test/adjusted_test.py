from numpy.testing import assert_equal, assert_array_almost_equal
import pytest

from geomagio.adjusted.SpreadsheetSummaryFactory import SpreadsheetSummaryFactory


def get_spreadsheet_summary(path):
    ssf = SpreadsheetSummaryFactory()
    reading = ssf.parse_spreadsheet(path=path)
    return reading


def test_DED20202200248_summary():
    reading = get_spreadsheet_summary(path="etc/adjusted/DED20202200248.xlsm")
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
