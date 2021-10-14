from fastapi import Depends
from fastapi.testclient import TestClient
from numpy.testing import assert_equal
from obspy import UTCDateTime
import pytest

from geomagio.api.ws import app
from geomagio.api.ws.data import get_data_query
from geomagio.api.ws.DataApiQuery import DataApiQuery, OutputFormat, SamplingPeriod


@pytest.fixture(scope="module")
def test_client():
    @app.get("/query/", response_model=DataApiQuery)
    def get_query(query: DataApiQuery = Depends(get_data_query)):
        return query

    client = TestClient(app)
    yield client


def test_get_data_query(test_client):
    """test.api_test.ws_test.data_test.test_get_data_query()"""
    response = test_client.get(
        "/query/?id=BOU&starttime=2020-09-01T00:00:01&elements=X,Y,Z,F&type=R1&sampling_period=60&format=iaga2002"
    )
    query = DataApiQuery(**response.json())
    assert_equal(query.id, "BOU")
    assert_equal(query.starttime, UTCDateTime("2020-09-01T00:00:01"))
    assert_equal(query.endtime, UTCDateTime("2020-09-02T00:00:00.999"))
    assert_equal(query.elements, ["X", "Y", "Z", "F"])
    assert_equal(query.sampling_period, SamplingPeriod.MINUTE)
    assert_equal(query.format, OutputFormat.IAGA2002)
    assert_equal(query.data_type, "R1")


def test_get_data_query_extra_params(test_client):
    """test.api_test.ws_test.data_test.test_get_data_query_extra_params()"""
    with pytest.raises(ValueError) as error:
        test_client.get(
            "/query/?id=BOU&starttime=2020-09-01T00:00:01&elements=X,Y,Z,F&type=variation&sampling_period=60&format=iaga2002&location=R1&network=NT"
        )
        assert error.message == "Invalid query parameter(s): location, network"


def test_get_data_query_bad_params(test_client):
    """test.api_test.ws_test.data_test.test_get_data_query_bad_params()"""
    with pytest.raises(ValueError) as error:
        test_client.get(
            "/query/?id=BOU&startime=2020-09-01T00:00:01&elements=X,Y,Z,F&data_type=variation&sampling_period=60&format=iaga2002"
        )
        assert error.message == "Invalid query parameter(s): startime, data_type"
