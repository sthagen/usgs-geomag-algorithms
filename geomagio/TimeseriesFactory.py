"""Abstract Timeseries Factory Interface."""
from __future__ import absolute_import, print_function
from io import BytesIO
import os
import sys
from typing import List, Optional

import numpy
from obspy import Stream, Trace, UTCDateTime

from .geomag_types import DataInterval, DataType
from .TimeseriesFactoryException import TimeseriesFactoryException
from . import TimeseriesUtility
from . import Util


class TimeseriesFactory(object):
    """Base class for timeseries factories.

    Add input support by:
        - implementing `parse_string`
        - or, overriding `get_timeseries`

    Add output support by:
        - implementing `write_file`
        - or, overriding `put_timeseries`

    Attributes
    ----------
    observatory : str
        default observatory code, usually 3 characters.
    channels : array_like
        default list of channels to load, optional.
        default ('H', 'D', 'Z', 'F')
    type : {'adjusted', 'definitive', 'provisional', 'quasi-definitive', 'reported', 'variation'}
        default data type, optional.
        default 'variation'.
    interval : {'tenhertz', 'second', 'minute', 'hour', 'day', 'month'}
        data interval, optional.
        default 'minute'.
    urlTemplate : str
        A string that contains replacement patterns.
        See https://github.com/usgs/geomag-algorithms/blob/master/docs/io.md
        and/or TimeseriesFactory._get_url()
    urlInterval : int
        Interval in seconds between URLs.
        Intervals begin at the unix epoch (1970-01-01T00:00:00Z)
    """

    def __init__(
        self,
        observatory: Optional[str] = None,
        channels: List[str] = ("H", "D", "Z", "F"),
        type: DataType = "variation",
        interval: DataInterval = "minute",
        urlTemplate: str = "",
        urlInterval: int = -1,
    ):
        self.observatory = observatory
        self.channels = channels
        self.type = type
        self.interval = interval
        self.urlTemplate = urlTemplate
        self.urlInterval = urlInterval

    def get_timeseries(
        self,
        starttime: UTCDateTime,
        endtime: UTCDateTime,
        add_empty_channels: bool = True,
        observatory: Optional[str] = None,
        channels: Optional[List[str]] = None,
        type: Optional[DataType] = None,
        interval: Optional[DataInterval] = None,
    ) -> Stream:
        """Get timeseries data.

        Support for specific channels, types, and intervals varies
        between factory and observatory.  Subclasses should raise
        TimeseriesFactoryException if the data is not available, or
        if an error occurs accessing data.

        Parameters
        ----------
        starttime : UTCDateTime
            time of first sample in timeseries.
        endtime : UTCDateTime
            time of last sample in timeseries.
        observatory : str
            observatory code, usually 3 characters, optional.
            uses default if unspecified.
        channels : array_like
            list of channels to load, optional.
            uses default if unspecified.
        type : {'adjusted', 'definitive', 'provisional', 'quasi-definitive', 'reported', 'variation'}
            data type, optional.
            uses default if unspecified.
        interval : {'tenhertz', 'second', 'minute', 'hour', 'day', 'month'}
            data interval, optional.
            uses default if unspecified.
        add_empty_channels : bool
            if True, returns channels without data as empty traces

        Returns
        -------
        timeseries : Stream
            stream containing traces for requested timeseries.

        Raises
        ------
        TimeseriesFactoryException
            if any parameters are unsupported, or errors occur loading data.
        """
        observatory = observatory or self.observatory
        channels = channels or self.channels
        type = type or self.type
        interval = interval or self.interval

        timeseries = Stream()
        urlIntervals = Util.get_intervals(
            starttime=starttime, endtime=endtime, size=self.urlInterval
        )
        for urlInterval in urlIntervals:
            url = self._get_url(
                observatory=observatory,
                date=urlInterval["start"],
                type=type,
                interval=interval,
                channels=channels,
            )
            try:
                data = Util.read_url(url)
            except IOError as e:
                print("Error reading url: %s, continuing" % str(e), file=sys.stderr)
                continue
            try:
                timeseries += self.parse_string(
                    data,
                    observatory=observatory,
                    type=type,
                    interval=interval,
                    channels=channels,
                )
            except NotImplementedError:
                raise NotImplementedError('"get_timeseries" not implemented')
            except Exception as e:
                print("Error parsing data: " + str(e), file=sys.stderr)
                print(data, file=sys.stderr)
        if channels is not None:
            filtered = Stream()
            for channel in channels:
                filtered += timeseries.select(channel=channel)
            timeseries = filtered
        timeseries.merge()
        timeseries.trim(
            starttime=starttime,
            endtime=endtime,
            nearest_sample=False,
            pad=True,
            fill_value=numpy.nan,
        )
        return timeseries

    def parse_string(self, data: str, **kwargs):
        """Creates error message that this functions is not implemented by
        TimeseriesFactory.

        Parameters
        ----------
        data : str
            string containing parsable content.
        Raises
        -------
        NotImplementedError
            if function is called
        """
        raise NotImplementedError('"parse_string" not implemented')

    def put_timeseries(
        self,
        timeseries: Stream,
        starttime: Optional[UTCDateTime] = None,
        endtime: Optional[UTCDateTime] = None,
        channels: Optional[List[str]] = None,
        type: Optional[DataType] = None,
        interval: Optional[DataInterval] = None,
    ):
        """Store timeseries data.

        Parameters
        ----------
        timeseries : Stream
            stream containing traces to store.
        starttime : UTCDateTime
            time of first sample in timeseries to store.
            uses first sample if unspecified.
        endtime : UTCDateTime
            time of last sample in timeseries to store.
            uses last sample if unspecified.
        channels : array_like
            list of channels to store, optional.
            uses default if unspecified.
        type : {'adjusted', 'definitive', 'provisional', 'quasi-definitive', 'reported', 'variation'}
            data type, optional.
            uses default if unspecified.
        interval : {'tenhertz', 'second', 'minute', 'hour', 'day', 'month'}
            data interval, optional.
            uses default if unspecified.
        Raises
        ------
        TimeseriesFactoryException
            if any errors occur.
        """
        if len(timeseries) == 0:
            # no data to put
            return
        if not self.urlTemplate.startswith("file://"):
            raise TimeseriesFactoryException("Only file urls are supported")
        channels = channels or self.channels
        type = type or self.type
        interval = interval or self.interval
        stats = timeseries[0].stats
        delta = stats.delta
        observatory = stats.station
        starttime = starttime or stats.starttime
        endtime = endtime or stats.endtime

        urlIntervals = Util.get_intervals(
            starttime=starttime, endtime=endtime, size=self.urlInterval
        )
        for urlInterval in urlIntervals:
            interval_start = urlInterval["start"]
            interval_end = urlInterval["end"]
            if interval_start != interval_end:
                interval_end = interval_end - delta
            url = self._get_url(
                observatory=observatory,
                date=interval_start,
                type=type,
                interval=interval,
                channels=channels,
            )
            url_data = timeseries.slice(
                starttime=interval_start,
                # subtract delta to omit the sample at end: `[start, end)`
                endtime=interval_end,
            )
            url_file = Util.get_file_from_url(url, createParentDirectory=True)
            # existing data file, merge new data into existing
            if os.path.isfile(url_file):
                try:
                    existing_data = Util.read_file(url_file)
                    existing_data = self.parse_string(
                        existing_data,
                        observatory=url_data[0].stats.station,
                        type=type,
                        interval=interval,
                        channels=channels,
                    )
                    # TODO: make parse_string return the correct location code
                    for trace in existing_data:
                        # make location codes match, just in case
                        new_trace = url_data.select(
                            network=trace.stats.network,
                            station=trace.stats.station,
                            channel=trace.stats.channel,
                        )[0]
                        trace.stats.location = new_trace.stats.location
                    url_data = TimeseriesUtility.merge_streams(existing_data, url_data)
                except IOError:
                    # no data yet
                    pass
                except NotImplementedError:
                    # factory only supports output
                    pass
            # pad with NaN's out to urlInterval (like get_timeseries())
            url_data.trim(
                starttime=interval_start,
                endtime=interval_end,
                nearest_sample=False,
                pad=True,
                fill_value=numpy.nan,
            )
            with open(url_file, "wb") as fh:
                try:
                    self.write_file(fh, url_data, channels)
                except NotImplementedError:
                    raise NotImplementedError('"put_timeseries" not implemented')

    def write_file(self, fh: BytesIO, timeseries: Stream, channels: List[str]):
        """Write timeseries data to the given file object.

        Parameters
        ----------
        fh : writable
            file handle where data is written.
        timeseries : Stream
            stream containing traces to store.
        channels : list
            list of channels to store.
        """
        raise NotImplementedError('"write_file" not implemented')

    def _get_empty_trace(
        self,
        starttime: UTCDateTime,
        endtime: UTCDateTime,
        observatory: str,
        channel: str,
        data_type: str,
        interval: str,
        network: str = "NT",
        location: str = "",
    ) -> Trace:
        """creates empty trace"""
        trace = TimeseriesUtility.create_empty_trace(
            starttime=starttime,
            endtime=endtime,
            observatory=observatory,
            channel=channel,
            type=data_type,
            interval=interval,
            station=observatory,
            network=network,
            location=location,
        )
        return trace

    def _get_file_from_url(self, url: str) -> str:
        """Get a file for writing.

        Ensures parent directory exists.

        Parameters
        ----------
        url : str
            path to file

        Returns
        -------
        filename : str
            path to file without file:// prefix

        Raises
        ------
        TimeseriesFactoryException
            if url does not start with file://
        """
        if not url.startswith("file://"):
            raise TimeseriesFactoryException("Only file urls are supported for writing")
        filename = url.replace("file://", "")
        parent = os.path.dirname(filename)
        if not os.path.exists(parent):
            os.makedirs(parent)
        return filename

    def _get_url(
        self,
        observatory: str,
        date: UTCDateTime,
        type: DataType = "variation",
        interval: DataInterval = "minute",
        channels: Optional[List[str]] = None,
    ) -> str:
        """Get the url for a specified file.

        Replaces patterns (described in class docstring) with values based on
        parameter values.

        Parameters
        ----------
        observatory : str
            observatory code.
        date : UTCDateTime
            day to fetch (only year, month, day are used)
        type : {'adjusted', 'definitive', 'provisional', 'quasi-definitive', 'reported', 'variation'}
            data type.
        interval : {'tenhertz', 'second', 'minute', 'hour', 'day', 'month'}
            data interval.
        channels : list
            list of data channels being requested

        Raises
        ------
        TimeseriesFactoryException
            if type or interval are not supported.
        """
        params = {
            "date": date.datetime,
            "i": self._get_interval_abbreviation(interval),
            "interval": self._get_interval_name(interval),
            # used by Hermanus
            "minute": date.hour * 60 + date.minute,
            # end Hermanus
            # used by Kakioka
            "month": date.strftime("%b").lower(),
            "MONTH": date.strftime("%b").upper(),
            # end Kakioka
            "obs": observatory.lower(),
            "OBS": observatory.upper(),
            "t": self._get_type_abbreviation(type),
            "type": self._get_type_name(type),
            # LEGACY
            # old date properties, string.format supports any strftime format
            # i.e. '{date:%j}'
            "julian": date.strftime("%j"),
            "year": date.strftime("%Y"),
            "ymd": date.strftime("%Y%m%d"),
        }
        if "{" in self.urlTemplate:
            # use new style string formatting
            return self.urlTemplate.format(**params)
        # use old style string interpolation
        return self.urlTemplate % params

    def _get_interval_abbreviation(self, interval: DataInterval) -> str:
        """Get abbreviation for a data interval.

        Used by ``_get_url`` to replace ``%(i)s`` in urlTemplate.

        Parameters
        ----------
        interval : {'tenhertz', 'second', 'minute', 'hour', 'day', 'month'}
            data interval

        Returns
        -------
        abbreviation for ``interval``.

        Raises
        ------
        TimeseriesFactoryException
            if ``interval`` is not supported.
        """

        interval_abbr = None
        if interval == "day":
            interval_abbr = "day"
        elif interval == "hour":
            interval_abbr = "hor"
        elif interval == "minute":
            interval_abbr = "min"
        elif interval == "month":
            interval_abbr = "mon"
        elif interval == "second":
            interval_abbr = "sec"
        else:
            raise TimeseriesFactoryException('Unexpected interval "%s"' % interval)
        return interval_abbr

    def _get_interval_name(self, interval: DataInterval) -> str:
        """Get name for a data interval.

        Used by ``_get_url`` to replace ``%(interval)s`` in urlTemplate.

        Parameters
        ----------
        interval : {'tenhertz', 'second', 'minute', 'hour', 'day', 'month'}
            data interval

        Returns
        -------
        name for ``interval``.

        Raises
        ------
        TimeseriesFactoryException
            if ``interval`` is not supported.
        """
        interval_name = None
        if interval == "minute":
            interval_name = "OneMinute"
        elif interval == "second":
            interval_name = "OneSecond"
        elif interval == "hour":
            interval_name = "OneHour"
        else:
            raise TimeseriesFactoryException('Unsupported interval "%s"' % interval)
        return interval_name

    def _get_type_abbreviation(self, type: DataType) -> str:
        """Get abbreviation for a data type.

        Used by ``_get_url`` to replace ``%(t)s`` in urlTemplate.

        Parameters
        ----------
        type : {'adjusted', 'definitive', 'provisional', 'quasi-definitive', 'reported', 'variation'}
            data type

        Returns
        -------
        name for ``type``.

        Raises
        ------
        TimeseriesFactoryException
            if ``type`` is not supported.
        """
        type_abbr = None
        if type == "definitive":
            type_abbr = "d"
        elif type == "provisional" or type == "adjusted":
            type_abbr = "p"
        elif type == "quasi-definitive":
            type_abbr = "q"
        elif type == "variation" or type == "reported":
            type_abbr = "v"
        else:
            raise TimeseriesFactoryException('Unexpected type "%s"' % type)
        return type_abbr

    def _get_type_name(self, type: DataType) -> str:
        """Get name for a data type.

        Used by ``_get_url`` to replace ``%(type)s`` in urlTemplate.

        Parameters
        ----------
        type : {'adjusted', 'definitive', 'provisional', 'quasi-definitive', 'reported', 'variation'}
            data type

        Returns
        -------
        name for ``type``.

        Raises
        ------
        TimeseriesFactoryException
            if ``type`` is not supported.
        """
        type_name = None
        if type == "variation" or type == "reported":
            type_name = ""
        elif type == "provisional" or type == "adjusted":
            type_name = "Provisional"
        elif type == "quasi-definitive" or type == "quasidefinitive":
            type_name = "QuasiDefinitive"
        elif type == "definitive":
            type_name = "Definitive"
        else:
            raise TimeseriesFactoryException('Unsupported type "%s"' % type)
        return type_name

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
        observatory : str
            observatory code
        channel : str
            edge channel code {MVH, MVE, MVD, ...}
        type : {'adjusted', 'definitive', 'provisional', 'quasi-definitive', 'reported', 'variation'}
            data type
        interval : {'tenhertz', 'second', 'minute', 'hour', 'day', 'month'}
            interval length
        """
        pass
