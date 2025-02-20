"""Timeseries Utilities"""
from builtins import range
from datetime import datetime
import math
import sys
import numpy
from obspy.core import Stats, Stream, Trace, UTCDateTime

from .Util import get_intervals


def create_empty_trace(
    starttime, endtime, observatory, channel, type, interval, network, station, location
):
    """create an empty trace filled with nans.

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
    type : str
        data type {definitive, quasi-definitive, variation}
    interval : str
        interval length {minute, second}
    network: str
        the network code
    station: str
        the observatory station code
    location: str
        the location code
    Returns
    -------
    Trace:
        trace for the requested channel
    """
    delta = get_delta_from_interval(interval)
    stats = Stats()
    stats.network = network
    stats.station = station
    stats.location = location
    stats.channel = channel
    # Calculate first valid sample time based on interval
    trace_starttime = UTCDateTime(numpy.ceil(starttime.timestamp / delta) * delta)
    if delta > 60.0:
        trace_starttime += (delta - 60) / 2
        if trace_starttime > endtime:
            sys.stderr.write(
                "Starttime greater than endtime, adjusting request to one sample"
            )
            endtime = trace_starttime
    stats.starttime = trace_starttime
    stats.delta = delta
    # Calculate number of valid samples up to or before endtime
    length = int((endtime - trace_starttime) / delta)
    stats.npts = length + 1
    data = numpy.full(stats.npts, numpy.nan, dtype=numpy.float64)
    return Trace(data, stats)


def encode_stream(stream: Stream, encoding: str) -> Stream:
    """Ensures that factory encoding matches output data encoding

    Parameters:
    -----------
    stream: Stream
        stream of input data

    Returns:
    --------
    out_stream: Stream
        stream with matching data encoding to factory specification

    """
    out_stream = Stream()
    for trace in stream:
        trace_out = trace.copy()
        if trace_out.data.dtype != encoding:
            trace_out.data = trace_out.data.astype(encoding)
            if "mseed" in trace_out.stats:
                trace_out.stats.mseed.encoding = encoding.upper()
        out_stream += trace_out
    return out_stream


def get_delta_from_interval(data_interval):
    """Convert interval name to number of seconds

    Parameters
    ----------
    interval : str
        interval length {day, hour, minute, second, tenhertz}

    Returns
    -------
    int
        number of seconds for interval, or None if unknown
    """
    if data_interval == "tenhertz":
        delta = 0.1
    elif data_interval == "second":
        delta = 1.0
    elif data_interval == "minute":
        delta = 60.0
    elif data_interval == "hour":
        delta = 3600.0
    elif data_interval == "day":
        delta = 86400.0
    else:
        delta = None
    return delta


def get_interval_from_delta(delta):
    """Convert delta to an interval name

    Parameters
    ----------
    delta: str
        number of seconds for interval, or None if unknown

    Returns
    -------
    interval : str
        interval length {day, hour, minute, second, tenhertz}
    """
    if delta == 0.1:
        data_interval = "tenhertz"
    elif delta == 1:
        data_interval = "second"
    elif delta == 60:
        data_interval = "minute"
    elif delta == 3600:
        data_interval = "hour"
    elif delta == 86400:
        data_interval = "day"
    else:
        data_interval = delta
    return data_interval


def get_stream_start_end_times(timeseries, without_gaps=False):
    """get start and end times from a stream.
            Traverses all traces, and find the earliest starttime, and
            the latest endtime.
    Parameters
    ----------
    timeseries: Stream
        The timeseries stream

    Returns
    -------
    tuple: (starttime, endtime)
        starttime: UTCDateTime
        endtime: UTCDateTime

    NOTE: when the entire timeseries is a gap, and without_gaps is True,
    the returned endtime will be one delta earlier than starttime.
    """
    starttime = UTCDateTime(datetime.now())
    endtime = UTCDateTime(0)
    for trace in timeseries:
        if trace.stats.starttime < starttime:
            starttime = trace.stats.starttime
        if trace.stats.endtime > endtime:
            endtime = trace.stats.endtime
    if without_gaps:
        gaps = get_merged_gaps(get_stream_gaps(timeseries))
        for gap in gaps:
            if gap[0] == starttime and gap[1] != endtime:
                # gap at start of timeseries, move to first data point
                starttime = gap[2]
            elif gap[1] == endtime:
                # gap at end of timeseries
                endtime = gap[0] - timeseries[0].stats.delta
    return (starttime, endtime)


def get_stream_gaps(stream, channels=None):
    """Get gaps in a given stream
    Parameters
    ----------
    stream: Stream
        the stream to check for gaps
    channels: array_like
        list of channels to check for gaps
        Default is None (check all channels).

    Returns
    -------
    dictionary of channel gaps arrays

    Notes
    -----
    Returns a dictionary with channel: gaps array pairs. Where the gaps array
        consists of arrays of starttime/endtime pairs representing each gap.
    """
    gaps = {}
    for trace in stream:
        channel = trace.stats.channel
        if channels is not None and channel not in channels:
            continue
        gaps[channel] = get_trace_gaps(trace)
    return gaps


def get_trace_gaps(trace):
    """Gets gaps in a trace representing a single channel
    Parameters
    ----------
    trace: Trace
        a stream containing a single channel of data.

    Returns
    -------
    array of gaps, which is empty when there are no gaps.
    each gap is an array [start of gap, end of gap, next sample]
    """
    gaps = []
    gap = None
    data = trace.data
    stats = trace.stats
    starttime = stats.starttime
    length = len(data)
    delta = stats.delta
    for i in range(0, length):
        if numpy.isnan(data[i]):
            if gap is None:
                # start of a gap
                gap = [starttime + i * delta]
        else:
            if gap is not None:
                # end of a gap
                gap.extend([starttime + (i - 1) * delta, starttime + i * delta])
                gaps.append(gap)
                gap = None
    # check for gap at end
    if gap is not None:
        gap.extend([starttime + (length - 1) * delta, starttime + length * delta])
        gaps.append(gap)
    return gaps


def get_merged_gaps(gaps):
    """Get gaps merged across channels/streams
    Parameters
    ----------
    gaps: dictionary
        contains channel/gap array pairs

    Returns
    -------
    array_like
        an array of startime/endtime arrays representing gaps.

    Notes
    -----
    Takes an dictionary of gaps, and merges those gaps across channels,
        returning an array of the merged gaps.
    """
    merged_gaps = []
    for key in gaps:
        merged_gaps.extend(gaps[key])
    # sort gaps so earlier gaps are before later gaps
    sorted_gaps = sorted(merged_gaps, key=lambda gap: gap[0])
    # merge gaps that overlap
    merged_gaps = []
    merged_gap = None
    for gap in sorted_gaps:
        if merged_gap is None:
            # start of gap
            merged_gap = gap
        elif gap[0] > merged_gap[2]:
            # next gap starts after current gap ends
            merged_gaps.append(merged_gap)
            merged_gap = gap
        elif gap[0] <= merged_gap[2]:
            # next gap starts at or before next data
            if gap[1] > merged_gap[1]:
                # next gap ends after current gap ends, extend current
                merged_gap[1] = gap[1]
                merged_gap[2] = gap[2]
    if merged_gap is not None:
        merged_gaps.append(merged_gap)
    return merged_gaps


def get_channels(stream):
    """Get a list of channels in a stream.

    Parameters
    ----------
    stream : Stream

    Returns
    -------
    channels : array_like
    """
    channels = {}
    for trace in stream:
        channel = trace.stats.channel
        if channel:
            channels[channel] = True
    return [ch for ch in channels]


def get_trace_value(traces, time, default=None):
    """Get a value at a specific time.

    Parameters
    ----------
    trace : Trace
    time : UTCDateTime

    Returns
    -------
    nearest time in trace
    value from trace at nearest time, or None
    """
    # array of UTCDateTime values corresponding
    for trace in traces:
        times = trace.times("utcdatetime")
        index = times.searchsorted(time)
        trace_time = times[index]
        trace_value = trace.data[index]
        if trace_time == time:
            if numpy.isnan(trace_value):
                return default
            else:
                return trace_value
    return default


def has_all_channels(stream, channels, starttime, endtime):
    """Check whether all channels have any data within time range.

    Parameters
    ----------
    stream: Stream
        The input stream we want to make certain has data
    channels: array_like
        The list of channels that we want to have concurrent data
    starttime: UTCDateTime
        start time of requested output
    end : UTCDateTime
        end time of requested output

    Returns
    -------
    bool: True if data found across all channels between starttime/endtime
    """
    input_gaps = get_merged_gaps(get_stream_gaps(stream=stream, channels=channels))
    for input_gap in input_gaps:
        # Check for gaps that include the entire range
        if (
            starttime >= input_gap[0]
            and starttime <= input_gap[1]
            and endtime < input_gap[2]
        ):
            return False
    return True


def has_any_channels(stream, channels, starttime, endtime):
    """Check whether any channel has data within time range.

    Parameters
    ----------
    stream: Stream
        The input stream we want to make certain has data
    channels: array_like
        The list of channels that we want to have concurrent data
    starttime: UTCDateTime
        start time of requested output
    end : UTCDateTime
        end time of requested output

    Returns
    -------
    bool: True if any data found between starttime/endtime
    """
    # process if any channels have data not covering the time range
    input_gaps = get_stream_gaps(stream=stream, channels=channels)
    for channel in channels:
        if channel not in input_gaps:
            continue
        channel_gaps = input_gaps[channel]
        if len(channel_gaps) == 0:
            # no gaps in channel
            return True
        for gap in channel_gaps:
            if not (starttime >= gap[0] and starttime <= gap[1] and endtime < gap[2]):
                # gap doesn't span channel
                return True
    # didn't find any data
    return False


def mask_stream(stream):
    """Convert stream traces to masked arrays.

    Parameters
    ----------
    stream : Stream
        stream to mask

    Returns
    -------
    Stream
        stream with new Trace objects with numpy masked array data.
    """
    masked = Stream()
    for trace in stream:
        masked += Trace(numpy.ma.masked_invalid(trace.data), trace.stats)
    return masked


def unmask_stream(stream):
    """Convert stream traces to unmasked arrays.

    Parameters
    ----------
    stream : Stream
        stream to unmask

    Returns
    -------
    Stream
        stream with new Trace objects with numpy array data, with numpy.nan
        as a fill value in a filled array.
    """
    unmasked = Stream()
    for trace in stream:
        unmasked += Trace(
            trace.data.filled(fill_value=numpy.nan)
            if isinstance(trace.data, numpy.ma.MaskedArray)
            else trace.data,
            trace.stats,
        )
    return unmasked


def merge_streams(*streams):
    """Merge one or more streams.

    Parameters
    ----------
    *streams : Stream
        one or more streams to merge

    Returns
    -------
    Stream
        stream with contiguous traces merged, and gaps filled with numpy.nan
    """
    merged = Stream()

    # sort out empty
    for stream in streams:
        merged += stream

    split = mask_stream(merged)

    # split traces that contain gaps
    split = split.split()

    # Re-add any empty traces that were removed by split()
    readd = Stream()
    for trace in merged:
        stats = trace.stats
        split_stream = split.select(
            channel=stats.channel,
            station=stats.station,
            network=stats.network,
            location=stats.location,
        )
        if len(split_stream) == 0:
            readd += trace
    split += readd

    # merge data
    split.merge(
        # 1 = do not interpolate
        interpolation_samples=0,
        # 1 = when there is overlap, use data from trace with last endtime
        method=1,
        # np.nan = work-around for (problematic) intermediate masked arrays
        fill_value=numpy.nan,
    )

    # convert back to NaN filled array
    merged = unmask_stream(split)
    return merged


def pad_timeseries(timeseries, starttime, endtime):
    """Calls pad_and_trim_trace for each trace in a stream.

    Traces should be merged before calling this method.

    Parameters
    ----------
    timeseries: Stream
        The timeseries stream as returned by the call to getWaveform
    starttime: UTCDateTime
        the starttime of the requested data
    endtime: UTCDateTime
        the endtime of the requested data

    Notes: the original timeseries object is changed.
    """
    for trace in timeseries:
        pad_and_trim_trace(trace, starttime, endtime)


def pad_and_trim_trace(trace, starttime, endtime):
    """Pads and trims trace data so it is in the range [starttime, endtime].

    Uses trace stats to compute start/end times that are consistent with
    other trace data.  (starttime and endtime are not checked).

    Parameters
    ----------
    trace: Trace
        One trace to be processed
    starttime: UTCDateTime
        the starttime of the requested data
    endtime: UTCDateTime
        the endtime of the requested data

    Notes: the original timeseries object is changed.
    """
    trace_starttime = UTCDateTime(trace.stats.starttime)
    trace_endtime = UTCDateTime(trace.stats.endtime)
    trace_delta = trace.stats.delta
    if trace_starttime < starttime:
        # trim to starttime
        cnt = int(math.ceil(round((starttime - trace_starttime) / trace_delta, 6)))
        if cnt > 0:
            trace.data = trace.data[cnt:]
            trace_starttime = trace_starttime + trace_delta * cnt
            trace.stats.starttime = trace_starttime
    elif trace_starttime > starttime:
        # pad to starttime
        cnt = int(round((trace_starttime - starttime) / trace_delta, 6))
        # cnt = int((trace_starttime - starttime) / trace_delta)
        if cnt > 0:
            trace.data = numpy.concatenate(
                [numpy.full(cnt, numpy.nan, dtype=numpy.float64), trace.data]
            )
            trace_starttime = trace_starttime - trace_delta * cnt
            trace.stats.starttime = trace_starttime
    if trace_endtime > endtime:
        # trim to endtime, at least 1 sample to remove
        cnt = int(math.ceil(round((trace_endtime - endtime) / trace_delta, 6)))
        trace.data = trace.data[:-cnt]
        trace.stats.npts = len(trace.data)
    elif trace_endtime < endtime:
        # pad to endtime
        cnt = int(round((endtime - trace_endtime) / trace.stats.delta, 6))
        # cnt = int((endtime - trace_endtime) / trace.stats.delta)
        if cnt > 0:
            trace.data = numpy.concatenate(
                [trace.data, numpy.full(cnt, numpy.nan, dtype=numpy.float64)]
            )


def round_usecs(time):
    """Rounds residual microseconds to milliseconds.

    Parameters
    ----------
    time: UTCDateTime
        time containing microsecond values

    Returns
    ----------
    time: UTCDateTime
        time containing rounded(or non-rounded) microsecond values
    """
    usecs = time.microsecond
    # round microseconds to nearest millisecond
    rounded_usecs = int(round(usecs / 1000, 0)) * 1000
    # reset microseconds to 0 at top of second, add second to input time
    if rounded_usecs > 999000:
        rounded_usecs = 0
        time += 1
    if rounded_usecs != usecs:
        time = time.replace(microsecond=rounded_usecs)
    return time


def split_stream(stream: Stream, size: int = 86400) -> Stream:
    out_stream = Stream()
    for trace in stream:
        out_stream += split_trace(trace, size)
    return out_stream


def split_trace(trace: Trace, size: int = 86400) -> Stream:
    # copy in case original trace changes later
    stream = Stream()
    out_trace = trace.copy()
    for interval in get_intervals(
        starttime=out_trace.stats.starttime,
        endtime=out_trace.stats.endtime,
        size=size,
        trim=True,
    ):
        interval_start = interval["start"]
        interval_end = interval["end"]
        delta = out_trace.stats.delta
        # accounts for trace containing one sample
        if interval_end - delta < interval_start:
            stream += out_trace
            continue
        stream += out_trace.slice(
            starttime=interval_start,
            endtime=interval_end - delta,
            nearest_sample=False,
        )
    return stream
