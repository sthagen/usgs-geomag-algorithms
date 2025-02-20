#! /usr/bin/env python

"""Monitor """
import sys
from typing import List
import argparse
import sys

from obspy.core import UTCDateTime

from .. import TimeseriesUtility, edge


def calculate_warning_threshold(warning_threshold, interval):
    """Calculate warning_threshold for the giving interval
    Parameters
    ----------
    warning_threshold: int
        the warning_threshold from the command line.
    interval: string
        the interval being warned against
    """
    if interval == "minute":
        warning_threshold *= 60
    elif interval == "second":
        warning_threshold *= 3600
    return warning_threshold


def calculate_gap_percentage(total, trace):
    """Calculate the percentage of missing values
    Parameters
    ----------
    total: int
        Total number of missing values
    trace: obspy.core.Trace
        a stream containing a single channel of data
    """
    return (float(total) / float(trace.stats.npts)) * 100.0, trace.stats.npts


def format_time(date):
    """Print UTCDateTime in YYYY-MM-DD HH:MM:SS format
    Parameters
    ----------
    date: UTCDateTime
    """
    return date.datetime.strftime("%Y-%m-%d %H:%M:%S")


def get_gaps(gaps):
    """Print gaps for a given channel into a html string.
    gaps: array
        Array of gaps
    """
    gap_string = ""
    if len(gaps):
        for i in range(len(gaps)):
            if i < 10:
                gap_string += "&nbsp;&nbsp;&nbsp;&nbsp; %s to %s <br>\n" % (
                    format_time(gaps[i][0]),
                    format_time(gaps[i][1]),
                )
            else:
                if i == 10:
                    gap_string += "<details>\n"
                    gap_string += f"<summary>+ {len(gaps) - 10}</summary>\n"
                    gap_string += "<span>\n"
                else:
                    gap_string += "&nbsp;&nbsp;&nbsp;&nbsp; %s to %s <br>\n" % (
                        format_time(gaps[i][0]),
                        format_time(gaps[i][1]),
                    )
                if i == len(gaps) - 1:
                    gap_string += "</span>\n"
                    gap_string += "</details>\n"
    else:
        gap_string = "&nbsp;&nbsp;&nbsp;&nbsp;None<br>"
    return gap_string


def get_gap_total(gaps, interval):
    """Get total length of time for all gaps in a channel
    Parameters
    ----------
    gaps: array
        Array of gaps
    interval: string
        the interval being warned against
    """
    total = 0
    divisor = 1
    if interval == "minute":
        divisor = 60
    for gap in gaps:
        total += int(gap[2] - gap[0]) / divisor
    return total


def get_last_time(gaps, endtime):
    """Return the last time that a channel has in it.
    Parameters
    ----------
    gaps: array
        Array of gaps
    endtime: UTCDateTime
        The endtime specified in the arguments
    """
    length = len(gaps) - 1
    if length > -1 and gaps[length][2] >= endtime:
        return gaps[length][0]
    else:
        return endtime


def get_table_header():
    return (
        '<table style="border-collapse: collapse;">\n'
        + "<thead>\n"
        + "<tr>\n"
        + '<th style="border:1px solid black; padding: 2px;">'
        + "</th>\n"
        + '<th style="border:1px solid black; padding: 2px;">'
        + "</th>\n"
        + "<th colspan=3 "
        + 'style="border:1px solid black; padding: 2px;">'
        + "Gap</th>\n"
        + '<th style="border:1px solid black; padding: 2px;">'
        + "</th>\n"
        + "</tr>\n"
        + "<tr>\n"
        + '<th style="border:1px solid black; padding: 2px;">'
        + "Channel</th>\n"
        + '<th style="border:1px solid black; padding: 2px;">'
        + "Last Time Value</th>\n"
        + '<th style="border:1px solid black; padding: 2px;">'
        + "Count</th>\n"
        + '<th style="border:1px solid black; padding: 2px;">'
        + "Total Time</th>\n"
        + '<th style="border:1px solid black; padding: 2px;">'
        + "Percentage</th>\n"
        + '<th style="border:1px solid black; padding: 2px;">'
        + "Total Values</th>\n"
        + "</tr>\n"
        + "</thead>\n"
        + "<tbody>\n"
    )


def has_gaps(gaps):
    """Returns True if gaps dictionary has gaps in it.
    Parameters
    ----------
    gaps: dictionary
        Dictionary of Channel:gaps arrays
    """
    for channel in gaps:
        if len(gaps[channel]):
            return True
    return False


def print_html_header(starttime, endtime, title):
    """Prints the html header, and title
    Parameters
    ----------
    starttime: UTCDateTime
        The starttime of the data we are analyzing
    endtime: UTCDateTime
        The endtime of the data we are analyzing
    title: string
        The title passed in by the user
    """
    print(
        "<!DOCTYPE html>\n"
        + "<html>\n"
        + "<head>\n"
        + "<title> %s \n to %s \n</title>"
        % (format_time(starttime), format_time(endtime))
        + "</head>\n"
        + "<body>\n"
        + '<style type="text/css">\n'
        + "table {border-collapse: collapse;}\n"
        + "th {border:1px solid black; padding: 2px;}\n"
        + "td {text-align:center;}\n"
        + "</style>\n"
        + title
        + "<br>\n"
        "%s to %s " % (format_time(starttime), format_time(endtime))
    )


def print_observatories(
    starttime: UTCDateTime,
    endtime: UTCDateTime,
    observatories: List[str],
    edge_host: str,
    channels: List[str],
    data_type: str,
    gaps_only: bool,
    intervals: List[str],
    location_code: str,
    warning_threshold: int,
):
    """Print all the observatories

    Returns
    -------
    Boolean: if a warning was issued.

    """
    intervals = intervals
    channels = channels
    starttime = starttime
    endtime = endtime
    host = edge_host
    table_header = get_table_header()
    warning_issued = False
    table_end = "</tbody>\n" + "</table>\n"

    for observatory in observatories:
        summary_table = ""
        gap_details = ""
        print_it = False
        summary_header = "<p>Observatory: %s </p>\n" % observatory
        summary_table += table_header
        for interval in intervals:
            factory = edge.EdgeFactory(
                host=host,
                port=2060,
                observatory=observatory,
                type=data_type,
                channels=channels,
                locationCode=location_code,
                interval=interval,
            )

            timeseries = factory.get_timeseries(starttime=starttime, endtime=endtime)
            gaps = TimeseriesUtility.get_stream_gaps(timeseries)
            if gaps_only and not has_gaps(gaps):
                continue
            else:
                print_it = True

            warning = ""
            warning_threshold = calculate_warning_threshold(warning_threshold, interval)

            summary_table += "<tr>"
            summary_table += '<td style="text-align:center;">'
            summary_table += " %sS \n </td></tr>\n" % interval.upper()
            gap_details += "&nbsp;&nbsp;%sS <br>\n" % interval.upper()
            for channel in channels:
                gap = gaps[channel]
                trace = timeseries.select(channel=channel)[0]
                total = get_gap_total(gap, interval)
                percentage, count = calculate_gap_percentage(total, trace)
                last = get_last_time(gap, endtime)
                summary_table += "<tr>\n"
                summary_table += '<td style="text-align:center;">%s</td>' % channel
                summary_table += '<td style="text-align:center;">%s</td>' % format_time(
                    last
                )
                summary_table += '<td style="text-align:center;">%d</td>' % len(gap)
                summary_table += '<td style="text-align:center;">%d %s</td>' % (
                    total,
                    interval,
                )
                summary_table += (
                    '<td style="text-align:center;">%0.2f%%</td>' % percentage
                )
                summary_table += '<td style="text-align:center;">%d</td>' % count
                summary_table += "</tr>\n"
                if endtime - last > warning_threshold:
                    warning += "%s " % channel
                    warning_issued = True
                # Gap Detail
                gap_details += "&nbsp;&nbsp;Channel: %s <br>\n" % channel
                gap_details += get_gaps(gap) + "\n"
            if len(warning):
                summary_header += (
                    "Warning: Channels older then "
                    + "warning-threshold "
                    + "%s %ss<br>\n" % (warning, interval)
                )
        summary_table += table_end
        if print_it:
            print(summary_header)
            print(summary_table)
            print(gap_details)

    return warning_issued


def generate_report(
    starttime: UTCDateTime,
    endtime: UTCDateTime,
    observatories: List[str],
    edge_host: str = "127.0.0.1",
    channels: List[str] = ["H", "E", "Z", "F"],
    data_type: str = "variation",
    gaps_only: bool = True,
    intervals: List[str] = ("minute",),
    location_code: str = "R0",
    title: str = "",
    warning_threshold: int = 60,
):
    print_html_header(starttime=starttime, endtime=endtime, title=title)
    warning_issued = print_observatories(
        starttime=starttime,
        endtime=endtime,
        observatories=observatories,
        edge_host=edge_host,
        channels=channels,
        data_type=data_type,
        gaps_only=gaps_only,
        intervals=intervals,
        location_code=location_code,
        warning_threshold=warning_threshold,
    )
    print("</body>\n" + "</html>\n")

    sys.exit(warning_issued)


def main(args=None):
    """command line tool for building geomag monitoring reports

    Inputs
    ------
    use monitor.py --help to see inputs, or see parse_args.

    Notes
    -----
    parses command line options using argparse
    Output is in HTML.
    """
    if args is None:
        args = parse_args(sys.argv[1:])
    generate_report(
        starttime=args.starttime,
        endtime=args.endtime,
        observatories=args.observatories,
        edge_host=args.edge_host,
        channels=args.channels,
        data_type=args.type,
        gaps_only=args.gaps_only,
        intervals=args.intervals,
        location_code=args.locationcode,
        title=args.title,
        warning_threshold=args.warning_threshold,
    )


def parse_args(args):
    """parse input arguments

    Parameters
    ----------
    args : list of strings

    Returns
    -------
    argparse.Namespace
        dictionary like object containing arguments.
    """
    parser = argparse.ArgumentParser(
        description="Use @ to read commands from a file.", fromfile_prefix_chars="@"
    )

    parser.add_argument(
        "--starttime",
        required=True,
        type=UTCDateTime,
        default=None,
        help="UTC date YYYY-MM-DD HH:MM:SS",
    )
    parser.add_argument(
        "--endtime",
        required=True,
        type=UTCDateTime,
        default=None,
        help="UTC date YYYY-MM-DD HH:MM:SS",
    )
    parser.add_argument(
        "--edge-host",
        required=False,
        default="127.0.0.1",
        help="IP/URL for edge connection",
    )
    parser.add_argument(
        "--observatories",
        required=True,
        nargs="*",
        help="Observatory code ie BOU, CMO, etc",
    )
    parser.add_argument(
        "--channels",
        nargs="*",
        default=["H", "E", "Z", "F"],
        help="Channels H, E, Z, etc",
    )
    parser.add_argument(
        "--intervals",
        nargs="*",
        default=["minute"],
        choices=["hourly", "minute", "second"],
    )
    parser.add_argument(
        "--locationcode", default="R0", choices=["R0", "R1", "RM", "Q0", "D0", "C0"]
    )
    parser.add_argument(
        "--type",
        default="variation",
        choices=["variation", "quasi-definitive", "definitive"],
    )
    parser.add_argument(
        "--warning-threshold",
        type=int,
        default=60,
        help="How many time slices should pass before a warning is issued",
    )
    parser.add_argument(
        "--gaps-only",
        action="store_true",
        default=True,
        help="Only print Observatories with gaps.",
    )
    parser.add_argument("--title", default="", help="Title for the top of the report")

    return parser.parse_args(args)


if __name__ == "__main__":
    main()
