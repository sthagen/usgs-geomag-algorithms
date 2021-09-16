from typing import List, Optional

import numpy

from ..adjusted import AdjustedMatrix
from ..algorithm import (
    AdjustedAlgorithm,
    AverageAlgorithm,
    SqDistAlgorithm,
)
from ..Controller import Controller, get_realtime_interval
from ..TimeseriesFactory import TimeseriesFactory
from .factory import get_edge_factory, get_miniseed_factory


def adjusted(
    observatory: str,
    input_factory: Optional[TimeseriesFactory] = None,
    input_channels: List[str] = ["H", "E", "Z", "F"],
    interval: str = "second",
    output_factory: Optional[TimeseriesFactory] = None,
    output_channels: List[str] = ["X", "Y", "Z", "F"],
    matrix: AdjustedMatrix = None,
    statefile: Optional[str] = None,
    realtime_interval: int = 600,
    update_limit: int = 10,
):
    """Run Adjusted algorithm.

    Parameters
    ----------
    observatory: observatory to calculate
    input_factory: where to read, should be configured with data_type
    input_channels: adjusted algorithm input channels
    interval: data interval
    output_factory: where to write, should be configured with data_type
    output_channels: adjusted algorithm output channels
    matrix: adjusted matrix
    statefile: adjusted statefile
    realtime_interval: window in seconds
    update_limit: maximum number of windows to backfill
    """
    if not statefile and not matrix:
        raise ValueError("Either statefile or matrix are required.")
    starttime, endtime = get_realtime_interval(realtime_interval)
    controller = Controller(
        algorithm=AdjustedAlgorithm(
            matrix=matrix,
            statefile=statefile,
            data_type="adjusted",
            location="A0",
            inchannels=input_channels,
            outchannels=output_channels,
        ),
        inputFactory=input_factory or get_edge_factory(data_type="variation"),
        inputInterval=interval,
        outputFactory=output_factory or get_edge_factory(data_type="adjusted"),
        outputInterval=interval,
    )
    controller.run_as_update(
        observatory=(observatory,),
        output_observatory=(observatory,),
        starttime=starttime,
        endtime=endtime,
        input_channels=input_channels,
        output_channels=output_channels,
        realtime=realtime_interval,
        update_limit=update_limit,
    )


def average(
    observatories: List[str],
    input_channel: str,
    input_factory: Optional[TimeseriesFactory] = None,
    interval: str = "second",
    output_channel: str = None,
    output_factory: Optional[TimeseriesFactory] = None,
    output_observatory: str = "USGS",
    realtime_interval: int = 600,
):
    """Run Average algorithm.

    Parameters
    ----------
    observatories: input observatories to calculate
    input_channel: channel from multiple observatories to average
    input_factory: where to read, should be configured with data_type and interval
    interval: data interval
    output_channel: channel to write (defaults to input_channel).
    output_factory: where to write, should be configured with data_type and interval
    output_observatory: observatory where output is written
    realtime_interval: window in seconds

    Uses update_limit=10.
    """
    starttime, endtime = get_realtime_interval(realtime_interval)
    controller = Controller(
        algorithm=AverageAlgorithm(observatories=observatories, channel=output_channel),
        inputFactory=input_factory or get_edge_factory(),
        inputInterval=interval,
        outputFactory=output_factory or get_edge_factory(),
        outputInterval=interval,
    )
    controller.run_as_update(
        observatory=observatories,
        output_observatory=(output_observatory,),
        starttime=starttime,
        endtime=endtime,
        output_channels=(output_channel or input_channel,),
        realtime=realtime_interval,
        update_limit=10,
    )


def sqdist_minute(
    observatory: str,
    statefile: str,
    input_factory: Optional[TimeseriesFactory] = None,
    output_factory: Optional[TimeseriesFactory] = None,
    realtime_interval: int = 1800,
):
    """Run SqDist algorithm.

    Only supports "minute" interval.

    Parameters
    ----------
    observatory: observatory to calculate
    statefile: sqdist statefile must already exist
    input_factory: where to read, should be configured with data_type and interval
    output_factory: where to write, should be configured with data_type and interval
    realtime_interval: window in seconds
    """
    if not statefile:
        raise ValueError("Statefile is required.")
    starttime, endtime = get_realtime_interval(realtime_interval)
    controller = Controller(
        algorithm=SqDistAlgorithm(
            alpha=2.3148e-5,
            gamma=3.3333e-2,
            m=1440,
            mag=True,
            smooth=180,
            statefile=statefile,
        ),
        inputFactory=input_factory or get_edge_factory(interval="minute"),
        inputInterval="minute",
        outputFactory=output_factory or get_edge_factory(interval="minute"),
        outputInterval="minute",
    )
    # sqdist is stateful, use run
    controller.run(
        observatory=(observatory,),
        output_observatory=(observatory,),
        starttime=starttime,
        endtime=endtime,
        input_channels=("X", "Y", "Z", "F"),
        output_channels=("MDT", "MSQ", "MSV"),
        realtime=realtime_interval,
        rename_output_channel=(("H_Dist", "MDT"), ("H_SQ", "MSQ"), ("H_SV", "MSV")),
        update_limit=10,
    )
