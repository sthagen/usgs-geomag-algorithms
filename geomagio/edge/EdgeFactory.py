"""Factory that loads data from earthworm and writes to Edge.

EdgeFactory uses obspy earthworm class to read data from any
earthworm standard Waveserver using the obspy getWaveform call.

Writing will be implemented with Edge specific capabilities,
to take advantage of it's newer realtime abilities.

Edge is the USGS earthquake hazard centers replacement for earthworm.
"""
from __future__ import absolute_import
from datetime import datetime
import sys
from typing import List, Optional

import numpy
import numpy.ma
from obspy import Stream, Trace, UTCDateTime
from obspy.clients import earthworm

from .. import ChannelConverter, TimeseriesUtility
from ..geomag_types import DataInterval, DataType
from ..TimeseriesFactory import TimeseriesFactory
from ..TimeseriesFactoryException import TimeseriesFactoryException
from ..ObservatoryMetadata import ObservatoryMetadata
from .RawInputClient import RawInputClient
from .LegacySNCL import LegacySNCL


class EdgeFactory(TimeseriesFactory):
    """TimeseriesFactory for Edge related data.

    Parameters
    ----------
    host: str
        a string representing the IP number of the host to connect to.
    port: integer
        the port number the waveserver is listening on.
    write_port: integer
        the port number the client is writing to.
    cwbport: int
        the port number of the cwb host to connect to.
    tag: str
        A tag used by edge to log and associate a socket with a given data
        source
    forceout: bool
        Tells edge to forceout a packet to miniseed.  Generally used when
        the user knows no more data is coming.
    observatory: str
        the observatory code for the desired observatory.
    channels: array
        an array of channels {H, D, E, F, Z, MGD, MSD, HGD}.
        Known since channel names are mapped based on interval and type,
        others are passed through, see #_get_edge_channel().
    type: {'adjusted', 'definitive', 'quasi-definitive', 'variation'}
        data type
    interval: {'second', 'minute', 'hour', 'day'}
        data interval
    observatoryMetadata: ObservatoryMetadata object
        an ObservatoryMetadata object used to replace the default
        ObservatoryMetadata.
    locationCode: str
        the location code for the given edge server, overrides type
        in get_timeseries/put_timeseries
    cwbhost: str
        a string represeting the IP number of the cwb host to connect to.

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
        port: int = 2060,
        write_port: int = 7981,
        cwbport: int = 0,
        tag: str = "GeomagAlg",
        forceout: bool = False,
        observatory: Optional[str] = None,
        channels: Optional[List[str]] = None,
        type: Optional[DataType] = None,
        interval: Optional[DataInterval] = None,
        observatoryMetadata: Optional[ObservatoryMetadata] = None,
        locationCode: Optional[str] = None,
        cwbhost: Optional[str] = None,
    ):
        TimeseriesFactory.__init__(self, observatory, channels, type, interval)
        self.client = earthworm.Client(host, port)
        self.host = host
        self.port = port
        self.write_port = write_port
        self.cwbport = cwbport
        self.tag = tag
        self.forceout = forceout
        self.interval = interval
        self.observatoryMetadata = observatoryMetadata or ObservatoryMetadata()
        self.locationCode = locationCode
        self.cwbhost = cwbhost or ""

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
            time of first sample.
        endtime: UTCDateTime
            time of last sample.
        observatory: str
            observatory code.
        channels: array
            list of channels to load
        type: {'adjusted', 'definitive', 'quasi-definitive', 'variation'}
            data type
        interval: {'second', 'minute', 'hour', 'day'}
            data interval
        add_empty_channels: bool
            if True, returns channels without data as empty traces

        Returns
        -------
        timeseries: Stream
            timeseries object with requested data

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
        interval: {'second', 'minute', 'hour', 'day'}
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

    def _convert_timeseries_to_decimal(self, stream: Stream):
        """convert geomag edge timeseries data stored as ints, to decimal by
            dividing by 1000.00
        Parameters
        ----------
        stream: Stream
            a stream retrieved from a geomag edge representing one channel
        Notes
        -----
        This routine changes the values in the timeseries. The user should
            make a copy before calling if they don't want that side effect.
        """
        for trace in stream:
            trace.data = numpy.divide(trace.data, 1000.00)

    def _convert_trace_to_int(self, trace_in: Trace) -> Trace:
        """convert geomag edge traces stored as decimal, to ints by multiplying
           by 1000

        Parameters
        ----------
        trace: Trace
            a trace retrieved from a geomag edge representing one channel
        Returns
        -------
        trace: Trace
            a trace converted to ints
        Notes
        -----
        this doesn't work on ndarray with nan's in it.
        the trace must be a masked array.
        """
        trace = trace_in.copy()
        trace.data = numpy.multiply(trace.data, 1000.00)
        trace.data = trace.data.astype(int)

        return trace

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
        interval: {'second', 'minute', 'hour', 'day'}
            data interval
        add_empty_channels: bool
            if True, returns channels without data as empty traces

        Returns
        -------
        data: Trace
            timeseries trace of the requested channel data
        """
        sncl = LegacySNCL.get_sncl(
            station=observatory,
            data_type=type,
            interval=interval,
            element=channel,
            location=self.locationCode,
        )
        try:
            data = self.client.get_waveforms(
                sncl.network,
                sncl.station,
                sncl.location,
                sncl.channel,
                starttime,
                endtime,
            )
        except TypeError:
            # get_waveforms() fails if no data is returned from Edge
            data = Stream()

        # make sure data is 32bit int
        for trace in data:
            trace.data = trace.data.astype("i4")
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
        self._set_metadata(data, observatory, channel, type, interval)
        return data

    def _post_process(
        self,
        timeseries: Stream,
        starttime: UTCDateTime,
        endtime: UTCDateTime,
        channels: List[str],
    ):
        """Post process a timeseries stream after the raw data is
                is fetched from a waveserver. Specifically changes
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
        self._convert_timeseries_to_decimal(timeseries)
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
        interval: {'second', 'minute', 'hour', 'day'}
            data interval
        starttime: UTCDateTime
        endtime: UTCDateTime

        Notes
        -----
        RawInputClient seems to only work when sockets are
        """
        sncl = LegacySNCL.get_sncl(
            station=observatory,
            data_type=type,
            interval=interval,
            element=channel,
            location=self.locationCode,
        )

        now = UTCDateTime(datetime.utcnow())
        if ((now - endtime) > 864000) and (self.cwbport > 0):
            host = self.cwbhost
            port = self.cwbport
        else:
            host = self.host
            port = self.write_port

        ric = RawInputClient(
            self.tag,
            host,
            port,
            sncl.station,
            sncl.channel,
            sncl.location,
            sncl.network,
        )

        stream = self._convert_stream_to_masked(timeseries=timeseries, channel=channel)

        # Make certain there's actually data
        if not numpy.ma.any(stream.select(channel=channel)[0].data):
            return

        for trace in stream.select(channel=channel).split():
            trace_send = trace.copy()
            trace_send.trim(starttime, endtime)
            if channel == "D":
                trace_send.data = ChannelConverter.get_minutes_from_radians(
                    trace_send.data
                )
            trace_send = self._convert_trace_to_int(trace_send)
            ric.send_trace(interval, trace_send)
        if self.forceout:
            ric.forceout()
        ric.close()

    def _set_metadata(
        self,
        stream: Stream,
        observatory: str,
        channel: str,
        type: str,
        interval: str,
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
        interval: {'second', 'minute', 'hour', 'day'}
            data interval
        """
        for trace in stream:
            self.observatoryMetadata.set_metadata(
                trace.stats, observatory, channel, type, interval
            )
