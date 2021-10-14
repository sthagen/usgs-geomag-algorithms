"""Factory that loads data from earthworm and writes to Edge.

EdgeFactory uses obspy earthworm class to read data from any
earthworm standard Waveserver using the obspy getWaveform call.

Writing will be implemented with Edge specific capabilities,
to take advantage of it's newer realtime abilities.

Edge is the USGS earthquake hazard centers replacement for earthworm.
"""
from __future__ import absolute_import
import sys
from typing import List, Optional

import numpy
import numpy.ma
from obspy.clients.neic import client as miniseed
from obspy.core import Stats, Stream, Trace, UTCDateTime

from .. import ChannelConverter, TimeseriesUtility
from ..geomag_types import DataInterval, DataType
from ..Metadata import get_instrument
from ..TimeseriesFactory import TimeseriesFactory
from ..TimeseriesFactoryException import TimeseriesFactoryException
from ..ObservatoryMetadata import ObservatoryMetadata
from .MiniSeedInputClient import MiniSeedInputClient
from .SNCL import SNCL


class MiniSeedFactory(TimeseriesFactory):
    """TimeseriesFactory for Edge related data.

    Parameters
    ----------
    host: str
        a string representing the IP number of the host to connect to.
    port: integer
        the port number the miniseed query server is listening on.
    observatory: str
        the observatory code for the desired observatory.
    channels: array
        an array of channels {H, D, E, F, Z, MGD, MSD, HGD}.
        Known since channel names are mapped based on interval and type,
        others are passed through, see #_get_edge_channel().
    type: {'adjusted', 'definitive', 'quasi-definitive', 'variation'}
        data type
    interval: {'tenhertz', 'second', 'minute', 'hour', 'day'}
        data interval
    observatoryMetadata: ObservatoryMetadata object
        an ObservatoryMetadata object used to replace the default
        ObservatoryMetadata.
    locationCode: str
        the location code for the given edge server, overrides type
        in get_timeseries/put_timeseries
    convert_channels: array
        list of channels to convert from volt/bin to nT

    See Also
    --------
    TimeseriesFactory

    Notes
    -----
    This is designed to read from any earthworm style waveserver, but it
        currently only writes to an edge. Edge mimics an earthworm style
        waveserver close enough that we hope to maintain that compatibility
        for reading.
    """

    def __init__(
        self,
        host: str = "cwbpub.cr.usgs.gov",
        port: int = 2061,
        write_port: int = 7974,
        observatory: Optional[str] = None,
        channels: Optional[List[str]] = None,
        type: Optional[DataType] = None,
        interval: Optional[DataInterval] = None,
        observatoryMetadata: Optional[ObservatoryMetadata] = None,
        locationCode: Optional[str] = None,
        convert_channels: Optional[List[str]] = None,
    ):
        TimeseriesFactory.__init__(self, observatory, channels, type, interval)

        self.client = miniseed.Client(host, port)
        self.observatoryMetadata = observatoryMetadata or ObservatoryMetadata()
        self.locationCode = locationCode
        self.interval = interval
        self.host = host
        self.port = port
        self.write_port = write_port
        self.convert_channels = convert_channels or []
        self.write_client = MiniSeedInputClient(self.host, self.write_port)

    def get_timeseries(
        self,
        starttime: UTCDateTime,
        endtime: UTCDateTime,
        observatory: Optional[str] = None,
        channels: Optional[List[str]] = None,
        type: Optional[DataType] = None,
        interval: Optional[DataInterval] = None,
        add_empty_channels: bool = True,
    ) -> Stream:
        """Get timeseries data

        Parameters
        ----------
        starttime: UTCDateTime
            time of first sample
        endtime: UTCDateTime
            time of last sample
        add_empty_channels: bool
            if True, returns channels without data as empty traces
        observatory: str
            observatory code
        channels: array
            list of channels to load
        type: {'adjusted', 'definitive', 'quasi-definitive', 'variation'}
            data type
        interval: {'tenhertz', 'second', 'minute', 'hour', 'day'}
            data interval

        Returns
        -------
        timeseries: Stream
            timeseries object with requested data.

        Raises
        ------
        TimeseriesFactoryException
            if invalid values are requested, or errors occur while
            retrieving timeseries.
        """
        observatory = observatory or self.observatory
        channels = channels or self.channels
        type = type or self.type
        interval = interval or self.interval

        if starttime > endtime:
            raise TimeseriesFactoryException(
                'Starttime before endtime "%s" "%s"' % (starttime, endtime)
            )

        # obspy factories sometimes write to stdout, instead of stderr
        original_stdout = sys.stdout
        try:
            # send stdout to stderr
            sys.stdout = sys.stderr
            # get the timeseries
            timeseries = Stream()
            for channel in channels:
                if channel in self.convert_channels:
                    data = self._convert_timeseries(
                        starttime, endtime, observatory, channel, type, interval
                    )
                else:
                    data = self._get_timeseries(
                        starttime,
                        endtime,
                        observatory,
                        channel,
                        type,
                        interval,
                        add_empty_channels,
                    )
                    if len(data) == 0:
                        continue
                timeseries += data
        finally:
            # restore stdout
            sys.stdout = original_stdout

        self._post_process(timeseries, starttime, endtime, channels)
        return timeseries

    def put_timeseries(
        self,
        timeseries: Stream,
        starttime: Optional[UTCDateTime] = None,
        endtime: Optional[UTCDateTime] = None,
        observatory: Optional[str] = None,
        channels: Optional[List[str]] = None,
        type: Optional[DataType] = None,
        interval: Optional[DataInterval] = None,
    ):
        """Put timeseries data

        Parameters
        ----------
        timeseries: Stream
            timeseries object with data to be written
        observatory: str
            observatory code
        channels: array
            list of channels to load
        type: {'adjusted', 'definitive', 'quasi-definitive', 'variation'}
            data type
        interval: {'tenhertz', 'second', 'minute', 'hour', 'day'}
            data interval

        Notes
        -----
        Streams sent to timeseries are expected to have a single trace per
            channel and that trace should have an ndarray, with nan's
            representing gaps.
        """
        stats = timeseries[0].stats
        observatory = observatory or stats.station or self.observatory
        channels = channels or self.channels
        type = type or self.type or stats.data_type
        interval = interval or self.interval or stats.data_interval

        if starttime is None or endtime is None:
            starttime, endtime = TimeseriesUtility.get_stream_start_end_times(
                timeseries
            )
        for channel in channels:
            if timeseries.select(channel=channel).count() == 0:
                raise TimeseriesFactoryException(
                    'Missing channel "%s" for output, available channels %s'
                    % (channel, str(TimeseriesUtility.get_channels(timeseries)))
                )
        for channel in channels:
            self._put_channel(
                timeseries, observatory, channel, type, interval, starttime, endtime
            )
        # close socket
        self.write_client.close()

    def get_calculated_timeseries(
        self,
        starttime: UTCDateTime,
        endtime: UTCDateTime,
        observatory: str,
        channel: str,
        type: DataType,
        interval: DataInterval,
        components: List[dict],
    ) -> Trace:
        """Calculate a single channel using multiple component channels.

        Parameters
        ----------
        starttime: UTCDateTime
            the starttime of the requested data
        endtime: UTCDateTime
            the endtime of the requested data
        observatory: str
            observatory code
        channel: str
            single character channel {H, E, D, Z, F}
        type: {'adjusted', 'definitive', 'quasi-definitive', 'variation'}
            data type
        interval: {'tenhertz', 'second', 'minute', 'hour', 'day'}
            data interval
        components: list
            each component is a dictionary with the following keys:
                channel: str
                offset: float
                scale: float

        Returns
        -------
        out: Trace
            timeseries trace of the converted channel data
        """
        # sum channels
        stats = None
        converted = None
        for component in components:
            # load component
            data = self._get_timeseries(
                starttime, endtime, observatory, component["channel"], type, interval
            )[0]
            # convert to nT
            nt = data.data * component["scale"] + component["offset"]
            # add to converted
            if converted is None:
                converted = nt
                stats = Stats(data.stats)
            else:
                converted += nt
        # set channel parameter to U, V, or W
        stats.channel = channel
        # create empty trace with adapted stats
        out = TimeseriesUtility.create_empty_trace(
            stats.starttime,
            stats.endtime,
            stats.station,
            stats.channel,
            stats.data_type,
            stats.data_interval,
            stats.network,
            stats.station,
            stats.location,
        )
        out.data = converted
        return out

    def _convert_stream_to_masked(self, timeseries: Stream, channel: str) -> Stream:
        """convert geomag edge traces in a timeseries stream to a MaskedArray
            This allows for gaps and splitting.
        Parameters
        ----------
        stream: Stream
            a stream retrieved from a geomag edge representing one channel
        channel: str
            the channel to be masked
        Returns
        -------
        stream: Stream
            a stream with all traces converted to masked arrays
        """
        stream = timeseries.copy()
        for trace in stream.select(channel=channel):
            trace.data = numpy.ma.masked_invalid(trace.data)
        return stream

    def _get_timeseries(
        self,
        starttime: UTCDateTime,
        endtime: UTCDateTime,
        observatory: str,
        channel: str,
        type: DataType,
        interval: DataInterval,
        add_empty_channels: bool = True,
    ) -> Trace:
        """get timeseries data for a single channel.

        Parameters
        ----------
        starttime: UTCDateTime
            the starttime of the requested data
        endtime: UTCDateTime
            the endtime of the requested data
        observatory: str
            observatory code
        channel: str
            single character channel {H, E, D, Z, F}
        type: {'adjusted', 'definitive', 'quasi-definitive', 'variation'}
            data type
        interval: {'tenhertz', 'second', 'minute', 'hour', 'day'}
            interval length
        add_empty_channels: bool
            if True, returns channels without data as empty traces

        Returns
        -------
        data: Trace
            timeseries trace of the requested channel data
        """
        sncl = SNCL.get_sncl(
            station=observatory,
            data_type=type,
            interval=interval,
            element=channel,
            location=self.locationCode,
        )
        data = self.client.get_waveforms(
            sncl.network, sncl.station, sncl.location, sncl.channel, starttime, endtime
        )
        data.merge()
        if data.count() == 0 and add_empty_channels:
            data += self._get_empty_trace(
                starttime=starttime,
                endtime=endtime,
                observatory=observatory,
                channel=channel,
                data_type=type,
                interval=interval,
                network=sncl.network,
                location=sncl.location,
            )
        if data.count() != 0:
            TimeseriesUtility.pad_and_trim_trace(
                trace=data[0], starttime=starttime, endtime=endtime
            )
        self._set_metadata(data, observatory, channel, type, interval)
        return data

    def _convert_timeseries(
        self,
        starttime: UTCDateTime,
        endtime: UTCDateTime,
        observatory: str,
        channel: str,
        type: DataType,
        interval: DataInterval,
    ) -> Trace:
        """Generate a single channel using multiple components.

        Finds metadata, then calls _get_converted_timeseries for actual
        conversion.

        Parameters
        ----------
        starttime: UTCDateTime
            the starttime of the requested data
        endtime: UTCDateTime
            the endtime of the requested data
        observatory : str
            observatory code
        channel : str
            single character channel {H, E, D, Z, F}
        type : {'adjusted', 'definitive', 'quasi-definitive', 'variation'}
            data type
        interval : {'tenhertz', 'second', 'minute', 'hour', 'day'}
            data interval

        Returns
        -------
        out: Trace
            timeseries trace of the requested channel data
        """
        out = Stream()
        metadata = get_instrument(observatory, starttime, endtime)
        # loop in case request spans different configurations
        for entry in metadata:
            entry_endtime = entry["end_time"]
            entry_starttime = entry["start_time"]
            instrument = entry["instrument"]
            instrument_channels = instrument["channels"]
            if channel not in instrument_channels:
                # no idea how to convert
                continue
            # determine metadata overlap with request
            start = (
                starttime
                if entry_starttime is None or entry_starttime < starttime
                else entry_starttime
            )
            end = (
                endtime
                if entry_endtime is None or entry_endtime > endtime
                else entry_endtime
            )
            # now convert
            out += self.get_calculated_timeseries(
                start,
                end,
                observatory,
                channel,
                type,
                interval,
                instrument_channels[channel],
            )
        return out

    def _post_process(
        self,
        timeseries: Stream,
        starttime: UTCDateTime,
        endtime: UTCDateTime,
        channels: List[str],
    ):
        """Post process a timeseries stream after the raw data is
                is fetched from querymom. Specifically changes
                any MaskedArray to a ndarray with nans representing gaps.
                Then calls pad_timeseries to deal with gaps at the
                beggining or end of the streams.

        Parameters
        ----------
        timeseries: Stream
            The timeseries stream as returned by the call to get_waveforms
        starttime: UTCDateTime
            the starttime of the requested data
        endtime: UTCDateTime
            the endtime of the requested data
        channels: array
            list of channels to load

        Notes: the original timeseries object is changed.
        """
        for trace in timeseries:
            if isinstance(trace.data, numpy.ma.MaskedArray):
                trace.data.set_fill_value(numpy.nan)
                trace.data = trace.data.filled()

        if "D" in channels:
            for trace in timeseries.select(channel="D"):
                trace.data = ChannelConverter.get_radians_from_minutes(trace.data)

        TimeseriesUtility.pad_timeseries(timeseries, starttime, endtime)

    def _put_channel(
        self,
        timeseries: Stream,
        observatory: str,
        channel: str,
        type: DataType,
        interval: DataInterval,
        starttime: UTCDateTime,
        endtime: UTCDateTime,
    ):
        """Put a channel worth of data

        Parameters
        ----------
        timeseries: Stream
            timeseries object with data to be written
        observatory: str
            observatory code
        channel: str
            channel to load
        type: {'adjusted', 'definitive', 'quasi-definitive', 'variation'}
            data type
        interval: {'tenhertz', 'second', 'minute', 'hour', 'day'}
            data interval
        starttime: UTCDateTime
        endtime: UTCDateTime
        """
        # use separate traces when there are gaps
        to_write = timeseries.select(channel=channel)
        to_write = TimeseriesUtility.mask_stream(to_write)
        to_write = to_write.split()
        to_write = TimeseriesUtility.unmask_stream(to_write)
        # relabel channels from internal to edge conventions
        sncl = SNCL.get_sncl(
            station=observatory,
            data_type=type,
            interval=interval,
            element=channel,
            location=self.locationCode,
        )
        for trace in to_write:
            trace.stats.station = sncl.station
            trace.stats.location = sncl.location
            trace.stats.network = sncl.network
            trace.stats.channel = sncl.channel
        # finally, send to edge
        self.write_client.send(to_write)

    def _set_metadata(
        self,
        stream: Stream,
        observatory: str,
        channel: str,
        type: DataType,
        interval: DataInterval,
    ):
        """set metadata for a given stream/channel
        Parameters
        ----------
        observatory: str
            observatory code
        channel: str
            edge channel code {MVH, MVE, MVD, ...}
        type: {'adjusted', 'definitive', 'quasi-definitive', 'variation'}
            data type
        interval: {'tenhertz', 'second', 'minute', 'hour', 'day'}
            data interval
        """
        for trace in stream:
            self.observatoryMetadata.set_metadata(
                trace.stats, observatory, channel, type, interval
            )
