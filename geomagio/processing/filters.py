from enum import Enum
from typing import List, Optional

from typer import Argument, Option, Typer

from ..algorithm import Algorithm, FilterAlgorithm
from ..Controller import Controller, get_realtime_interval
from ..geomag_types import DataInterval
from ..TimeseriesFactory import TimeseriesFactory
from .factory import get_edge_factory, get_miniseed_factory


class DataFormat(str, Enum):
    OBSRIO = "OBSRIO"
    PCDCP = "PCDCP"


app = Typer(help="Filter geomagnetic timeseries data")


def main():
    app()


@app.command(
    name="day",
    help="Filter 1 day nT/temperature data",
)
def day_command(
    observatory: str = Argument(None, help="observatory id"),
    input_host: str = Option("127.0.0.1", help="host to request data from"),
    output_host: str = Option("127.0.0.1", help="host to write data to"),
    realtime_interval: int = Option(86400, help="length of update window (in seconds)"),
    update_limit: int = Option(7, help="number of update windows"),
):
    day_filter(
        observatory=observatory,
        input_factory=get_miniseed_factory(host=input_host),
        output_factory=get_miniseed_factory(host=output_host),
        realtime_interval=realtime_interval,
        update_limit=update_limit,
    )


@app.command(
    name="hour",
    help="Filter 1 hour nT/temperature data",
)
def hour_command(
    observatory: str = Argument(None, help="observatory id"),
    input_host: str = Option("127.0.0.1", help="host to request data from"),
    output_host: str = Option("127.0.0.1", help="host to write data to"),
    realtime_interval: int = Option(3600, help="length of update window (in seconds)"),
    update_limit: int = Option(24, help="number of update windows"),
):
    hour_filter(
        observatory=observatory,
        input_factory=get_miniseed_factory(host=input_host),
        output_factory=get_miniseed_factory(host=output_host),
        realtime_interval=realtime_interval,
        update_limit=update_limit,
    )


@app.command(
    name="realtime",
    short_help="Filter 1 second and 1 minute nT/temperature data",
    help="""
    ObsRIO:

        Filters 10Hz U,V,W miniseed to 1 second miniseed

        Filters 1 second U,V,W,F miniseed to 1 minute miniseed

        Filters 1 second T1-4 miniseed to 1 minute UK1-4 legacy

        Copies 1 second and 1 minute U,V,W,F miniseed to H,E,Z,F earthworm

    PCDCP:

        Copies 1 second H,E,Z,F earthworm to U,V,W,F miniseed

        Filters 1 second U,V,W,F miniseed to 1 minute miniseed

    """,
)
def realtime_command(
    observatory: str = Argument(None, help="observatory id"),
    input_host: str = Option("127.0.0.1", help="host to request data from"),
    output_host: str = Option("127.0.0.1", help="host to write data to"),
    data_format: DataFormat = Option(DataFormat.PCDCP, help="Data acquisition system"),
    realtime_interval: int = Option(600, help="length of update window (in seconds)"),
    update_limit: int = Option(10, help="number of update windows"),
):
    if data_format == DataFormat.OBSRIO:
        second_filter(
            observatory=observatory,
            input_factory=get_miniseed_factory(
                host=input_host, convert_channels=("U", "V", "W")
            ),
            output_factory=get_miniseed_factory(host=output_host),
            realtime_interval=realtime_interval,
            update_limit=update_limit,
        )
        _copy_channels(
            observatory=observatory,
            channels=(
                ("U", "H"),
                ("V", "E"),
                ("W", "Z"),
                ("F", "F"),
            ),
            interval="second",
            input_factory=get_miniseed_factory(host=input_host),
            output_factory=get_edge_factory(host=output_host),
            realtime_interval=realtime_interval,
            update_limit=update_limit,
        )
        temperature_filter(
            observatory=observatory,
            input_factory=get_miniseed_factory(host=input_host),
            output_factory=get_edge_factory(host=output_host),
            realtime_interval=realtime_interval,
            update_limit=update_limit,
        )
    else:
        _copy_channels(
            observatory=observatory,
            channels=(
                ("H", "U"),
                ("E", "V"),
                ("Z", "W"),
                ("F", "F"),
            ),
            interval="second",
            input_factory=get_edge_factory(host=input_host),
            output_factory=get_miniseed_factory(host=output_host),
            realtime_interval=realtime_interval,
            update_limit=update_limit,
        )
    minute_filter(
        observatory=observatory,
        channels=("U", "V", "W", "F"),
        input_factory=get_miniseed_factory(host=input_host),
        output_factory=get_miniseed_factory(host=output_host),
        realtime_interval=realtime_interval,
        update_limit=update_limit,
    )
    if data_format == DataFormat.OBSRIO:
        _copy_channels(
            observatory=observatory,
            channels=(
                ("U", "H"),
                ("V", "E"),
                ("W", "Z"),
                ("F", "F"),
            ),
            interval="minute",
            input_factory=get_miniseed_factory(host=input_host),
            output_factory=get_edge_factory(host=output_host),
            realtime_interval=realtime_interval,
            update_limit=update_limit,
        )


def day_filter(
    observatory: str,
    channels: List[str] = ["U", "V", "W", "F", "T1", "T2", "T3", "T4"],
    input_factory: Optional[TimeseriesFactory] = None,
    output_factory: Optional[TimeseriesFactory] = None,
    realtime_interval: int = 86400,
    update_limit: int = 7,
):
    """Filter 1 second miniseed channels to 1 day

    Parameters:
    -----------
    observatory: str
        observatory id
    channels: array
        list of channels to filter
    input_factory: TimeseriesFactory
        factory to request data
    output_factory: TimeseriesFactory
        factory to write data
    realtime_interval: int
        length of update window (in seconds)
    update_limit: int
        number of update windows
    """
    starttime, endtime = get_realtime_interval(realtime_interval)
    controller = Controller(
        inputFactory=input_factory or get_miniseed_factory(),
        inputInterval="minute",
        outputFactory=output_factory or get_miniseed_factory(),
        outputInterval="day",
    )
    for channel in channels:
        controller.run_as_update(
            algorithm=FilterAlgorithm(
                input_sample_period=60.0,
                output_sample_period=86400.0,
                inchannels=(channel,),
                outchannels=(channel,),
            ),
            observatory=(observatory,),
            output_observatory=(observatory,),
            starttime=starttime,
            endtime=endtime,
            input_channels=(channel,),
            output_channels=(channel,),
            realtime=realtime_interval,
            update_limit=update_limit,
        )


def hour_filter(
    observatory: str,
    channels: List[str] = ["U", "V", "W", "F", "T1", "T2", "T3", "T4"],
    input_factory: Optional[TimeseriesFactory] = None,
    output_factory: Optional[TimeseriesFactory] = None,
    realtime_interval: int = 600,
    update_limit: int = 10,
):
    """Filter 1 minute miniseed channels to 1 hour

    Parameters:
    -----------
    observatory: str
        observatory id
    channels: array
        list of channels to filter
    input_factory: TimeseriesFactory
        factory to request data
    output_factory: TimeseriesFactory
        factory to write data
    realtime_interval: int
        length of update window (in seconds)
    update_limit: int
        number of update windows
    """
    starttime, endtime = get_realtime_interval(realtime_interval)
    controller = Controller(
        inputFactory=input_factory or get_miniseed_factory(),
        inputInterval="minute",
        outputFactory=output_factory or get_miniseed_factory(),
        outputInterval="hour",
    )
    for channel in channels:
        controller.run_as_update(
            algorithm=FilterAlgorithm(
                input_sample_period=60.0,
                output_sample_period=3600.0,
                inchannels=(channel,),
                outchannels=(channel,),
            ),
            observatory=(observatory,),
            output_observatory=(observatory,),
            starttime=starttime,
            endtime=endtime,
            input_channels=(channel,),
            output_channels=(channel,),
            realtime=realtime_interval,
            update_limit=update_limit,
        )


def minute_filter(
    observatory: str,
    channels: List[str] = ["U", "V", "W", "F"],
    input_factory: Optional[TimeseriesFactory] = None,
    output_factory: Optional[TimeseriesFactory] = None,
    realtime_interval: int = 600,
    update_limit: int = 10,
):
    """Filter 1 second miniseed channels to 1 minute

    Parameters:
    -----------
    observatory: str
        observatory id
    channels: array
        list of channels to filter
    input_factory: TimeseriesFactory
        factory to request data
    output_factory: TimeseriesFactory
        factory to write data
    realtime_interval: int
        length of update window (in seconds)
    update_limit: int
        number of update windows
    """
    starttime, endtime = get_realtime_interval(realtime_interval)
    controller = Controller(
        inputFactory=input_factory or get_miniseed_factory(),
        inputInterval="second",
        outputFactory=output_factory or get_miniseed_factory(),
        outputInterval="minute",
    )
    for channel in channels:
        controller.run_as_update(
            algorithm=FilterAlgorithm(
                input_sample_period=1,
                output_sample_period=60,
                inchannels=(channel,),
                outchannels=(channel,),
            ),
            observatory=(observatory,),
            output_observatory=(observatory,),
            starttime=starttime,
            endtime=endtime,
            input_channels=(channel,),
            output_channels=(channel,),
            realtime=realtime_interval,
            update_limit=update_limit,
        )


def second_filter(
    observatory: str,
    input_factory: Optional[TimeseriesFactory] = None,
    output_factory: Optional[TimeseriesFactory] = None,
    realtime_interval: int = 600,
    update_limit: int = 10,
):
    """Filter 10Hz miniseed U,V,W to 1 second

    Parameters:
    -----------
    observatory: str
        observatory id
    input_factory: TimeseriesFactory
        factory to request data
    output_factory: TimeseriesFactory
        factory to write data
    realtime_interval: int
        length of update window (in seconds)
    update_limit: int
        number of update windows
    """
    starttime, endtime = get_realtime_interval(realtime_interval)
    controller = Controller(
        inputFactory=input_factory
        or get_miniseed_factory(convert_channels=("U", "V", "W")),
        inputInterval="tenhertz",
        outputFactory=output_factory or get_miniseed_factory(),
        outputInterval="second",
    )
    for channel in ("U", "V", "W"):
        controller.run_as_update(
            algorithm=FilterAlgorithm(
                input_sample_period=0.1,
                output_sample_period=1,
                inchannels=(channel,),
                outchannels=(channel,),
            ),
            observatory=(observatory,),
            output_observatory=(observatory,),
            starttime=starttime,
            endtime=endtime,
            input_channels=(channel,),
            output_channels=(channel,),
            realtime=realtime_interval,
            update_limit=update_limit,
        )


def temperature_filter(
    observatory: str,
    input_factory: Optional[TimeseriesFactory] = None,
    output_factory: Optional[TimeseriesFactory] = None,
    realtime_interval: int = 600,
    update_limit: int = 10,
):
    """Filter temperatures 1Hz miniseed (LK1-4) to 1 minute legacy (UK1-4)."""
    starttime, endtime = get_realtime_interval(realtime_interval)
    controller = Controller(
        inputFactory=input_factory or get_miniseed_factory(),
        inputInterval="second",
        outputFactory=output_factory or get_edge_factory(),
        outputInterval="minute",
    )
    renames = {"LK1": "UK1", "LK2": "UK2", "LK3": "UK3", "LK4": "UK4"}
    for input_channel in renames.keys():
        output_channel = renames[input_channel]
        controller.run_as_update(
            algorithm=FilterAlgorithm(
                input_sample_period=1,
                output_sample_period=60,
                inchannels=(input_channel,),
                outchannels=(output_channel,),
            ),
            observatory=(observatory,),
            output_observatory=(observatory,),
            starttime=starttime,
            endtime=endtime,
            input_channels=(input_channel,),
            output_channels=(output_channel,),
            realtime=realtime_interval,
            rename_output_channel=((input_channel, output_channel),),
            update_limit=update_limit,
        )


def _copy_channels(
    observatory: str,
    channels: List[List[str]],
    interval: DataInterval,
    input_factory: Optional[TimeseriesFactory],
    output_factory: Optional[TimeseriesFactory],
    realtime_interval: int = 600,
    update_limit: int = 10,
):
    """copy channels between earthworm and miniseed formats

    Parameters:
    -----------
    observatory: str
        observatory id
    channels: array
        list of channel conversions
        format: ((input_channel_1, output_channel_1), ...)
    interval: {tenhertz, second, minute, hour, day}
        data interval
    input_factory: TimeseriesFactory
        factory to request data
    output_factory: TimeseriesFactory
        factory to write data
    realtime_interval: int
        length of update window (in seconds)
    update_limit: int
        number of update windows
    """
    starttime, endtime = get_realtime_interval(interval_seconds=realtime_interval)
    controller = Controller(
        inputFactory=input_factory or get_miniseed_factory(),
        inputInterval=interval,
        outputFactory=output_factory or get_edge_factory(),
        outputInterval=interval,
    )
    for input_channel, output_channel in channels:
        controller.run_as_update(
            algorithm=Algorithm(
                inchannels=(input_channel,),
                outchannels=(output_channel,),
            ),
            observatory=(observatory,),
            output_observatory=(observatory,),
            starttime=starttime,
            endtime=endtime,
            input_channels=(input_channel,),
            output_channels=(output_channel,),
            rename_output_channel=((input_channel, output_channel),),
            realtime=realtime_interval,
            update_limit=update_limit,
        )
