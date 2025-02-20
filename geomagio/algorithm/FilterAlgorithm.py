import json
import sys
from typing import Dict

import numpy as np
from numpy.lib import stride_tricks as npls
from obspy.core import Stream, Stats
import scipy.signal as sps

from .Algorithm import Algorithm
from .. import TimeseriesUtility


STEPS = [
    {  # 10 Hz to one second filter
        "name": "10Hz",
        "data_interval": "second",
        "data_interval_type": "1-second",
        "input_sample_period": 0.1,
        "output_sample_period": 1.0,
        "window": sps.firwin(123, 0.25, window="blackman", fs=10.0),
        "type": "firfilter",
        "filter_comments": [
            "Vector 1-second values are computed from 10 Hz values using a Blackman filter (123 taps, cutoff 0.25Hz) centered on the start of the second."
        ],
    },
    {  # one second to one minute filter
        "name": "Intermagnet One Minute",
        "data_interval": "minute",
        "data_interval_type": "1-minute",
        "input_sample_period": 1.0,
        "output_sample_period": 60.0,
        "window": sps.get_window(window=("gaussian", 15.8734), Nx=91),
        "type": "firfilter",
        "filter_comments": [
            "Scalar and Vector 1-minute values are computed from 1 Hz values using an INTERMAGNET gaussian filter centered on the start of the minute (00:30-01:30)."
        ],
    },
    {  # one minute to one hour filter
        "name": "One Hour",
        "data_interval": "hour",
        "data_interval_type": "1-hour (00-59)",
        "input_sample_period": 60.0,
        "output_sample_period": 3600.0,
        "window": sps.windows.boxcar(60),
        "type": "average",
        "filter_comments": [
            "Scalar and Vector 1-hour values are computed from average of 1-minute values in the hour (00-59)",
        ],
    },
    {  # one minute to one day filter
        "name": "One Day",
        "data_interval": "day",
        "data_interval_type": "1-day (00:00-23:59)",
        "input_sample_period": 60.0,
        "output_sample_period": 86400,
        "window": sps.windows.boxcar(1440),
        "type": "average",
        "filter_comments": [
            "Scalar and Vector 1-day values are computed from average of 1-minute values in the day (00:00-23:59)",
        ],
    },
]


def get_nearest_time(step, output_time, left=True):
    interval_start = output_time - (
        output_time.timestamp % step["output_sample_period"]
    )
    # shift interval right if needed
    if interval_start != output_time and not left:
        interval_start += step["output_sample_period"]
    # position center of filter, data around interval
    half_width = get_step_time_shift(step)
    if step["type"] == "average":
        filter_center = interval_start + half_width
        data_start = interval_start
        data_end = (interval_start + step["output_sample_period"]) - step[
            "input_sample_period"
        ]
    else:
        filter_center = interval_start
        data_start = filter_center - half_width
        data_end = filter_center + half_width
    return {
        "time": filter_center,
        "data_start": data_start,
        "data_end": data_end,
    }


def get_step_time_shift(step):
    """Calculates the time shift generated in each filtering step

    Parameters
    ----------
    step: dict
        Dictionary object holding information about a given filter step
    Returns
    -------
    shift: float
        Time shift value
    """
    input_sample_period = step["input_sample_period"]
    numtaps = len(step["window"])
    shift = input_sample_period * ((numtaps - 1) / 2)
    return shift


class FilterAlgorithm(Algorithm):
    """
    Filter Algorithm that filters and downsamples data
    """

    def __init__(
        self,
        coeff_filename=None,
        filtertype=None,
        steps=None,
        input_sample_period=None,
        output_sample_period=None,
        inchannels=None,
        outchannels=None,
    ):

        Algorithm.__init__(self, inchannels=inchannels, outchannels=outchannels)
        self.coeff_filename = coeff_filename
        self.filtertype = filtertype
        self.input_sample_period = input_sample_period
        self.output_sample_period = output_sample_period
        self.steps = steps
        self.load_state()
        # ensure correctly aligned coefficients in each step
        self.steps = (
            self.steps and [self._validate_step(step) for step in self.steps] or []
        )

    def load_state(self):
        """Load filter coefficients from json file if custom filter is used.
        File name is self.coeff_filename.
        """
        if self.coeff_filename is None:
            return
        with open(self.coeff_filename, "r") as f:
            data = f.read()
            data = json.loads(data)
        if data is None or data == "":
            return
        self.steps = [
            {
                "name": "name" in data and data["name"] or "custom",
                "data_interval": TimeseriesUtility.get_interval_from_delta(
                    self.output_sample_period
                ),
                "data_interval_type": "filtered custom interval",
                "filter_comments": "filter_comments" in data
                and data["filter_comments"]
                or [
                    "Data produced by filter utilizing custom coefficients and intervals."
                ],
                "input_sample_period": self.input_sample_period,
                "output_sample_period": self.output_sample_period,
                "window": data["window"],
                "type": data["type"],
            }
        ]

    def save_state(self):
        """Save algorithm state to a file.
        File name is self.statefile.
        """
        if self.coeff_filename is None:
            return
        data = {"window": list(self.window), "type": self.type}
        with open(self.coeff_filename, "w") as f:
            f.write(json.dumps(data))

    def get_filter_steps(self):
        """Method to gather necessary filtering steps from STEPS constant.
        Returns
        -------
        list
            Returns list of filter steps.
            Steps can be passed in constructor as an array as steps.

        """
        if self.steps:
            return self.steps

        steps = []
        for step in STEPS:
            if (
                self.input_sample_period <= step["input_sample_period"]
                and self.output_sample_period >= step["output_sample_period"]
            ):
                if (
                    step["type"] == "average"
                    and step["output_sample_period"] != self.output_sample_period
                ):
                    continue
                steps.append(step)
        return steps

    def _validate_step(self, step):
        """Verifies whether or not firfirlter steps have an odd number of coefficients"""
        if step["type"] == "firfilter" and len(step["window"]) % 2 != 1:
            raise ValueError("Firfilter requires an odd number of coefficients")
        else:
            return step

    def can_produce_data(self, starttime, endtime, stream):
        """Can Produce data

        The FilterAlgorithm can produce data for each channel independently.

        Parameters
        ----------
        starttime: UTCDateTime
            start time of requested output
        end : UTCDateTime
            end time of requested output
        stream: obspy.core.Stream
            The input stream we want to make certain has data for the algorithm
        """
        return TimeseriesUtility.has_any_channels(
            stream, self.get_required_channels(), starttime, endtime
        )

    def create_trace(self, channel, stats, data):
        """Utility to create a new trace object.
        This may be necessary for more sophisticated metadata
        modifications, but for now it simply passes inputs back
        to parent Algorithm class.
        Parameters
        ----------
        channel : str
            channel name.
        stats : obspy.core.Stats
            channel metadata to clone.
        data : numpy.array
            channel data.
        Returns
        -------
        obspy.core.Trace
            trace containing data and metadata.
        """

        trace = super(FilterAlgorithm, self).create_trace(channel, stats, data)
        return trace

    def process(self, stream):
        """Run algorithm for a stream.
        Processes all traces in the stream.
        Parameters
        ----------
        stream : obspy.core.Stream
            stream of data to process
        Returns
        -------
        out : obspy.core.Stream
            stream containing 1 trace per original trace.
        """
        # intitialize step array for filter
        steps = self.get_filter_steps()
        for step in steps:
            stream = self.process_step(step, stream.copy())

        return stream

    def process_step(self, step, stream):
        """Filters stream for one step.
        Filters all traces in stream.
        Parameters
        ----------
        step : array element
            step holding variables for one filtering operation
        stream : obspy.core.Stream
            stream of data to filter
        Returns
        -------
        out : obspy.core.Stream
            stream containing 1 trace per original trace.
        """
        # gather variables from step
        input_sample_period = step["input_sample_period"]
        output_sample_period = step["output_sample_period"]
        window = np.array(step["window"])
        decimation = int(output_sample_period / input_sample_period)
        numtaps = len(window)
        window = window / sum(window)
        out = Stream()
        for trace in stream:
            starttime, data = self.align_trace(step, trace)
            # check that there is still enough data to filter
            if len(data) < numtaps:
                continue
            filtered = self.firfilter(data, window, decimation)
            stats = Stats(trace.stats)
            stats.delta = output_sample_period
            stats.data_interval = step["data_interval"]
            stats.data_interval_type = step["data_interval_type"]
            stats.filter_comments = step["filter_comments"]
            stats.starttime = starttime
            stats.npts = len(filtered)
            trace_out = self.create_trace(stats.channel, stats, filtered)
            out += trace_out
        return out

    def align_trace(self, step, trace):
        """Aligns trace to handle trailing or missing values.
        Parameters
        ----------
        step: dict
            Dictionary object holding information about a given filter step
        trace: obspy.core.trace
            trace holding data and stats(starttime/endtime) to manipulate in alignment
        Returns
        -------
        filter_start["time"]: UTCDateTime
            shifted time for filtered output
        data: numpy array
            trimmed data if input trace is misaligned
        """
        data = trace.data
        start = trace.stats.starttime
        filter_start = get_nearest_time(step=step, output_time=start, left=False)
        while filter_start["data_start"] < start:
            # filter needs more data, shift one output right
            filter_start = get_nearest_time(
                step=step,
                output_time=filter_start["time"] + step["output_sample_period"],
                left=False,
            )

        if start != filter_start["data_start"]:
            offset = int(
                1e-6
                + (filter_start["data_start"] - start) / step["input_sample_period"]
            )
            data = data[offset:]
        return filter_start["time"], data

    @staticmethod
    def firfilter(data, window, step, allowed_bad=0.1):
        """Run fir filter for a numpy array.
        Processes all traces in the stream.
        Parameters
        ----------
        data: numpy.ndarray
            array of data to process
        window: numpy.ndarray
            array of filter coefficients
        step: int
            ratio of output sample period to input sample period
            should always be an integer
        allowed_bad: float
            ratio of bad samples to total window size
        Returns
        -------
        filtered_out : numpy.ndarray
            stream containing filtered output
        """
        numtaps = len(window)

        # build view into data, with numtaps  chunks separated into
        # overlapping 'rows'
        shape = data.shape[:-1] + (data.shape[-1] - numtaps + 1, numtaps)
        strides = data.strides + (data.strides[-1],)
        as_s = npls.as_strided(data, shape=shape, strides=strides, writeable=False)
        # build masked array for invalid entries, also 'decimate' by step
        as_masked = np.ma.masked_invalid(as_s[::step], copy=True)
        # sums of the total 'weights' of the filter corresponding to
        # valid samples
        as_weight_sums = np.dot(window, (~as_masked.mask).T)
        # mark the output locations as 'bad' that have missing input weights
        # that sum to greater than the allowed_bad threshhold
        as_invalid_masked = np.ma.masked_less(as_weight_sums, 1 - allowed_bad)
        # apply filter, using masked version of dot (in 3.5 and above, there
        # seems to be a move toward np.matmul and/or @ operator as opposed to
        # np.dot/np.ma.dot - haven't tested to see if the shape of first and
        # second argument need to be changed)
        filtered = np.ma.dot(window, as_masked.T)
        # re-normalize, especially important for partially filled windows
        filtered = np.divide(filtered, as_weight_sums)
        # use the earlier marked output locations to mask the output data
        # array
        filtered.mask = as_invalid_masked.mask
        # convert masked array back to regular array, with nan as fill value
        # (otherwise the type returned is not always the same, and can cause
        # problems with factories, merge, etc.)
        filtered_out = np.ma.filled(filtered, np.nan)
        return filtered_out

    def get_input_interval(self, start, end, observatory=None, channels=None):
        """Get Input Interval
        start : UTCDateTime
            start time of requested output.
        end : UTCDateTime
            end time of requested output.
        observatory : string
            observatory code.
        channels : string
            input channels.
        Returns
        -------
        input_start : UTCDateTime
            start of input required to generate requested output
        input_end : UTCDateTime
            end of input required to generate requested output.
        """
        steps = self.get_filter_steps()
        # calculate start/end from inverted step array
        for step in reversed(steps):
            start_interval = get_nearest_time(step=step, output_time=start, left=False)
            end_interval = get_nearest_time(step=step, output_time=end, left=True)
            start, end = start_interval["data_start"], end_interval["data_end"]
        return (start, end)

    @classmethod
    def add_arguments(cls, parser):
        """Add command line arguments to argparse parser.
        Parameters
        ----------
        parser: ArgumentParser
            command line argument parser
        """
        # input and output time intervals are managed
        # by Controller and TimeriesUtility

        parser.add_argument(
            "--filter-coefficients",
            default=None,
            help="File storing custom filter coefficients",
        )

    def configure(self, arguments):
        """Configure algorithm using comand line arguments.
        Parameters
        ----------
        arguments: Namespace
            parsed command line arguments
        """
        Algorithm.configure(self, arguments)
        # intialize filter with command line arguments
        self.coeff_filename = arguments.filter_coefficients
        self.input_sample_period = TimeseriesUtility.get_delta_from_interval(
            arguments.input_interval or arguments.interval
        )
        self.output_sample_period = TimeseriesUtility.get_delta_from_interval(
            arguments.output_interval or arguments.interval
        )
        self.load_state()
