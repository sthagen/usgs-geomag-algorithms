import sys

import json
import numpy as np
from obspy.core import Stream, Stats

from ..adjusted import AdjustedMatrix
from .Algorithm import Algorithm


class AdjustedAlgorithm(Algorithm):
    """Algorithm that converts from one geomagnetic coordinate system to a
    related geographic coordinate system, by using transformations generated
    from absolute, baseline measurements.
    """

    def __init__(
        self,
        matrix: AdjustedMatrix = None,
        statefile=None,
        data_type=None,
        location=None,
        inchannels=None,
        outchannels=None,
    ):
        inchannels = inchannels or ["H", "E", "Z", "F"]
        outchannels = outchannels or ["X", "Y", "Z", "F"]
        Algorithm.__init__(
            self,
            inchannels=inchannels,
            outchannels=outchannels,
        )
        # state variables
        self.matrix = matrix
        self.statefile = statefile
        self.data_type = data_type
        self.location = location
        # load matrix with statefile
        if matrix is None:
            self.load_state()

    def load_state(self):
        """Load algorithm state from a file.
        File name is self.statefile.
        """
        # Adjusted matrix defaults to identity matrix
        matrix_size = len([c for c in self.get_input_channels() if c != "F"]) + 1
        matrix = np.eye(matrix_size).tolist()
        if self.statefile is None:
            self.matrix = AdjustedMatrix(matrix=matrix)
            return
        try:
            with open(self.statefile, "r") as f:
                data = f.read()
                data = json.loads(data)
        except IOError as err:
            raise FileNotFoundError("statefile not found")
        if "pier_correction" in data:
            self.matrix = AdjustedMatrix(**data)
        elif "PC" in data:
            # read data from legacy format
            for row in range(matrix_size):
                for col in range(matrix_size):
                    matrix[row][col] = np.float64(data[f"M{row+1}{col+1}"])
            pier_correction = np.float64(data["PC"])
            self.matrix = AdjustedMatrix(matrix=matrix, pier_correction=pier_correction)
        else:
            raise ValueError("pier correction not found in statefile")

    def save_state(self):
        """Save algorithm state to a file.
        File name is self.statefile.
        """
        if self.statefile is None:
            return
        json_string = self.matrix.json()
        json_dict = json.loads(json_string)
        with open(self.statefile, "w") as f:
            f.write(json.dumps(json_dict))

    def create_trace(self, channel, stats, data):
        """Utility to create a new trace object.

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
        stats = Stats(stats)
        if self.data_type is None:
            stats.data_type = "adjusted"
        else:
            stats.data_type = self.data_type
        if self.data_type is None:
            stats.location = "A0"
        else:
            stats.location = self.location

        trace = super(AdjustedAlgorithm, self).create_trace(channel, stats, data)
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
            stream containing 1 trace per original trace. (h, e, z)->(X, Y, Z)
        """

        out = None
        inchannels = self.get_input_channels()
        outchannels = self.get_output_channels()
        adjusted = self.matrix.process(
            stream,
            inchannels=inchannels,
            outchannels=outchannels,
        )
        out = Stream(
            [
                self.create_trace(
                    outchannels[i],
                    stream.select(channel=inchannels[i])[0].stats,
                    adjusted[i],
                )
                for i in range(len(outchannels))
            ]
        )
        return out

    def can_produce_data(self, starttime, endtime, stream):
        """Can Product data
        Parameters
        ----------
        starttime: UTCDateTime
            start time of requested output
        end : UTCDateTime
            end time of requested output
        stream: obspy.core.Stream
            The input stream we want to make certain has data for the algorithm
        """

        channels = self.get_input_channels()

        # if F is available, can produce at least adjusted F
        if "F" in channels and super().can_produce_data(
            starttime, endtime, stream.select(channel="F")
        ):
            return True

        # if E-E and E-N available
        if (
            "E-E" in channels
            and "E-N" in channels
            and super().can_produce_data(starttime, endtime, stream)
        ):
            return True

        # check validity of remaining channels
        for c in channels:
            if c != "F" and not (
                super().can_produce_data(starttime, endtime, stream.select(channel=c))
            ):
                return False

        # return false if F or remaining channels cannot produce data
        return False

    @classmethod
    def add_arguments(cls, parser):
        """Add command line arguments to argparse parser.
        Parameters
        ----------
        parser: ArgumentParser
            command line argument parser
        """

        parser.add_argument(
            "--adjusted-statefile",
            default=None,
            help="File to store state between calls to algorithm",
        )

    def configure(self, arguments):
        """Configure algorithm using comand line arguments.
        Parameters
        ----------
        arguments: Namespace
            parsed command line arguments
        """
        Algorithm.configure(self, arguments)
        self.statefile = arguments.adjusted_statefile
        self.load_state()
