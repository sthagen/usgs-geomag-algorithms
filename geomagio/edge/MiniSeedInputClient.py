from __future__ import absolute_import, print_function
import io
import socket
import sys
from typing import BinaryIO

from obspy.core import Stream

from ..TimeseriesUtility import encode_stream, split_stream


class MiniSeedInputClient(object):
    """Client to write MiniSeed formatted data to Edge.

    Connects on first call to send().
    Use close() to disconnect.

    Parameters
    ----------
    host: str
        MiniSeedServer hostname
    port: int
        MiniSeedServer port
    encoding: str
        Floating point precision for output data
    """

    def __init__(self, host, port=2061, encoding="float32"):
        self.host = host
        self.port = port
        self.encoding = encoding
        self.socket = None

    def close(self):
        """Close socket if open."""
        if self.socket is not None:
            try:
                self.socket.close()
            finally:
                self.socket = None

    def connect(self, max_attempts=2):
        """Connect to socket if not already open.

        Parameters
        ----------
        max_attempts: int
            number of times to try connecting when there are failures.
            default 2.
        """
        if self.socket is not None:
            return
        s = None
        attempts = 0
        while True:
            attempts += 1
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((self.host, self.port))
                break
            except socket.error as e:
                if attempts >= max_attempts:
                    raise
                print("Unable to connect (%s), trying again" % e, file=sys.stderr)
        self.socket = s

    def send(self, stream):
        """Send traces to EDGE in miniseed format.

        All traces in stream will be converted to MiniSeed, and sent as-is.

        Parameters
        ----------
        stream: Stream
            stream with trace(s) to send.
        """
        # connect if needed
        if self.socket is None:
            self.connect()
        buf = io.BytesIO()
        self._format_miniseed(stream=stream, buf=buf)
        # send data
        self.socket.sendall(buf.getvalue())

    def _format_miniseed(self, stream: Stream, buf: BinaryIO) -> io.BytesIO:
        """Processes and writes stream to buffer as miniseed

        Parameters:
        -----------
        stream: Stream
            stream with data to write
        buf: BinaryIO
            memory buffer for output data
        """
        processed = self._pre_process(stream=stream)
        for trace in processed:
            # convert stream to miniseed
            trace.write(buf, format="MSEED", reclen=512)

    def _pre_process(self, stream: Stream) -> Stream:
        """Encodes and splits streams at daily intervals

        Paramters:
        ----------
        stream: Stream
            stream of input data

        Returns:
        --------
        stream: Stream
            list of encoded trace split at daily intervals
        """
        stream = encode_stream(stream=stream, encoding=self.encoding)
        stream = split_stream(stream=stream, size=86400)
        return stream
