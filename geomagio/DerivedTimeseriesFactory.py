from typing import List, Optional

from obspy import Stream, UTCDateTime

from .algorithm import Algorithm, DeltaFAlgorithm, XYZAlgorithm
from .TimeseriesFactory import TimeseriesFactory, TimeseriesUtility


class DerivedTimeseriesFactory(TimeseriesFactory):
    factory: TimeseriesFactory

    def __init__(self, factory: TimeseriesFactory):
        self.factory = factory
        super().__init__(
            observatory=factory.observatory,
            channels=factory.channels,
            type=factory.type,
            interval=factory.interval,
            urlTemplate=factory.urlTemplate,
            urlInterval=factory.urlInterval,
        )

    def get_timeseries(
        self,
        starttime: UTCDateTime,
        endtime: UTCDateTime,
        observatory: str,
        channels: List[str],
        interval: str,
        add_empty_channels: bool = True,
        derive_missing: bool = True,
        type: Optional[str] = None,
    ) -> Stream:
        type = type or self.type
        timeseries = self.factory.get_timeseries(
            starttime=starttime,
            endtime=endtime,
            observatory=observatory,
            channels=channels,
            type=type,
            interval=interval,
            add_empty_channels=False,
        )
        missing = get_missing(timeseries, channels)
        if missing and derive_missing:
            timeseries += self._get_derived_channels(
                starttime=starttime,
                endtime=endtime,
                observatory=observatory,
                channels=channels,
                data_type=type,
                interval=interval,
                timeseries=timeseries,
            )
        missing = get_missing(timeseries, channels)
        if missing and add_empty_channels:
            timeseries += self.factory._get_empty_channels(
                starttime=starttime,
                endtime=endtime,
                observatory=observatory,
                channels=channels,
                data_type=type,
                interval=interval,
            )
        # file-based factories return all channels found in file
        timeseries = Stream([t for t in timeseries if t.stats.channel in channels])
        return timeseries

    def _get_derived_channels(
        self,
        starttime: UTCDateTime,
        endtime: UTCDateTime,
        observatory: str,
        channels: List[str],
        data_type: str,
        interval: str,
        timeseries: Stream,
    ):
        """calculate derived channels"""
        input_timeseries = timeseries.copy()
        input_channels = []
        for channel in channels:
            input_channels += self._get_derived_input_channels(channel, data_type)
        missing_inputs = get_missing(input_timeseries, list(set(input_channels)))
        if missing_inputs:
            input_timeseries += self.factory.get_timeseries(
                starttime=starttime,
                endtime=endtime,
                observatory=observatory,
                channels=missing_inputs,
                type=data_type,
                interval=interval,
                add_empty_channels=False,
            )
        output_timeseries = Stream()
        for channel in channels:
            if channel in get_missing(output_timeseries, channels):
                derived = self._derive_trace(
                    input_timeseries=input_timeseries,
                    channel=channel,
                    data_type=data_type,
                )
                for channel in get_missing(
                    output_timeseries, TimeseriesUtility.get_channels(stream=derived)
                ):
                    output_timeseries += derived.select(channel=channel)
        return output_timeseries

    def _get_derived_input_channels(self, channel: str, data_type: str) -> List[str]:
        """get channels required to calculate desired channel"""
        if data_type == "variation":
            if channel == "G":
                return ["H", "E", "Z", "F"]
            elif channel in ["X", "Y", "D"]:
                return ["H", "E"]
        else:
            if channel == "G":
                return ["X", "Y", "Z", "F"]
            elif channel in ["H", "D"]:
                return ["X", "Y"]
        return []

    def _derive_trace(
        self, input_timeseries: Stream, channel: str, data_type: str
    ) -> Stream:
        """Process timeseries based on desired channel

        Note: All derived channels are returned
        """
        if data_type == "variation":
            if channel == "G":
                return DeltaFAlgorithm(informat="obs").process(
                    timeseries=input_timeseries
                )
            elif channel in ["X", "Y"]:
                return XYZAlgorithm(informat="obs", outformat="geo").process(
                    timeseries=input_timeseries
                )
            elif channel == "D":
                return XYZAlgorithm(informat="obs", outformat="obsd").process(
                    timeseries=input_timeseries
                )
        else:
            if channel == "G":
                return DeltaFAlgorithm(informat="geo").process(
                    timeseries=input_timeseries
                )
            elif channel in ["H", "D"]:
                return XYZAlgorithm(informat="geo", outformat="mag").process(
                    timeseries=input_timeseries
                )
        return Stream()


def get_missing(input: Stream, desired: List[str]) -> List[str]:
    """Return missing channels from input"""
    present = TimeseriesUtility.get_channels(stream=input)
    return list(set(desired).difference(set(present)))
