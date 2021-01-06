from numpy.testing import assert_equal, assert_array_almost_equal
from obspy.core import UTCDateTime
import pytest

from geomagio.adjusted.SpreadsheetSummaryFactory import SpreadsheetSummaryFactory


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
