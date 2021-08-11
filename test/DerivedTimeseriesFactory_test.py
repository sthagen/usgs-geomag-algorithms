from typing import List

from obspy import Stream

from geomagio import DerivedTimeseriesFactory, TimeseriesUtility
from geomagio.algorithm import Algorithm, DeltaFAlgorithm, XYZAlgorithm
from geomagio.iaga2002 import StreamIAGA2002Factory
from geomagio.edge import EdgeFactory


def test_derive_trace():
    """test.DerivedTimeseriesFactory_test.test_derive_trace()"""
    timeseries = get_derived_timeseries(
        "etc/filter/BOU20200101vsec.sec", ["H", "E", "Z", "F"], "variation", "second"
    )
    factory = DerivedTimeseriesFactory(EdgeFactory())
    assert factory._derive_trace(
        input_timeseries=timeseries, channel="G", data_type="variation"
    ) == DeltaFAlgorithm(informat="obs").process(timeseries=timeseries)
    assert factory._derive_trace(
        input_timeseries=timeseries, channel="X", data_type="variation"
    ) == XYZAlgorithm(informat="obs", outformat="geo").process(timeseries=timeseries)
    assert factory._derive_trace(
        input_timeseries=timeseries, channel="Y", data_type="variation"
    ) == XYZAlgorithm(informat="obs", outformat="geo").process(timeseries=timeseries)
    assert factory._derive_trace(
        input_timeseries=timeseries, channel="D", data_type="variation"
    ) == XYZAlgorithm(informat="obs", outformat="obsd").process(timeseries=timeseries)
    timeseries = get_derived_timeseries(
        "etc/adjusted/BOU201601adj.min", ["X", "Y", "Z", "F"], "adjusted", "minute"
    )
    assert factory._derive_trace(
        input_timeseries=timeseries, channel="G", data_type="adjusted"
    ) == DeltaFAlgorithm(informat="geo").process(timeseries=timeseries)
    assert factory._derive_trace(
        input_timeseries=timeseries, channel="H", data_type="adjusted"
    ) == XYZAlgorithm(informat="geo", outformat="mag").process(timeseries=timeseries)
    assert factory._derive_trace(
        input_timeseries=timeseries, channel="D", data_type="adjusted"
    ) == XYZAlgorithm(informat="geo", outformat="mag").process(timeseries=timeseries)


def test_get_derived_input_channels():
    """test.DerivedTimeseriesFactory_test.test_get_derived_input_channels()"""
    factory = DerivedTimeseriesFactory(EdgeFactory(host=None, port=None))
    assert factory._get_derived_input_channels(channel="G", data_type="variation") == [
        "H",
        "E",
        "Z",
        "F",
    ]
    assert factory._get_derived_input_channels(channel="G", data_type="adjusted") == [
        "X",
        "Y",
        "Z",
        "F",
    ]
    assert factory._get_derived_input_channels(channel="X", data_type="variation") == [
        "H",
        "E",
    ]
    assert factory._get_derived_input_channels(channel="H", data_type="adjusted") == [
        "X",
        "Y",
    ]
    # invalid channel, should return empty list
    assert factory._get_derived_input_channels(channel="Q", data_type="variation") == []


def test_get_timeseries():
    """test.DerivedTimeseriesFactory_test.test_get_timeseries()"""
    variation_url = "etc/filter/BOU20200101vsec.sec"
    timeseries = get_derived_timeseries(
        variation_url, ["H", "E", "Z", "F"], "variation", "second"
    )
    assert TimeseriesUtility.get_channels(timeseries) == ["H", "E", "Z", "F"]
    timeseries = get_derived_timeseries(variation_url, ["G"], "variation", "second")
    assert TimeseriesUtility.get_channels(timeseries) == ["G"]
    timeseries = get_derived_timeseries(
        variation_url, ["X", "Y"], "variation", "second"
    )
    assert set(TimeseriesUtility.get_channels(timeseries)) == set(["X", "Y"])
    adjusted_url = "etc/adjusted/BOU201601adj.min"
    timeseries = get_derived_timeseries(
        adjusted_url, ["X", "Y", "Z", "F"], "adjusted", "minute"
    )
    assert TimeseriesUtility.get_channels(timeseries) == ["X", "Y", "Z", "F"]
    timeseries = get_derived_timeseries(adjusted_url, ["G"], "adjusted", "minute")
    assert TimeseriesUtility.get_channels(timeseries) == ["G"]
    timeseries = get_derived_timeseries(adjusted_url, ["H", "D"], "adjusted", "minute")
    assert set(TimeseriesUtility.get_channels(timeseries)) == set(["H", "D"])


def get_derived_timeseries(
    url: str, channels: List[str], data_type: str, interval: str
) -> Stream:
    with open(url, "r") as file:
        return DerivedTimeseriesFactory(
            StreamIAGA2002Factory(stream=file)
        ).get_timeseries(
            starttime=None,
            endtime=None,
            observatory="BOU",
            channels=channels,
            interval=interval,
            add_empty_channels=False,
            derive_missing=True,
            data_type=data_type,
        )
