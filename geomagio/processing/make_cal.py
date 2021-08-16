#! /usr/bin/env python

"""
Usage:
    python make_cal.py OBSERVATORY YEAR
"""
from __future__ import print_function

from obspy import UTCDateTime
import typer

from .magproc import write_cal_file


def main():
    typer.run(make_cal)


def make_cal(observatory: str, year: int):
    write_cal_file(
        starttime=UTCDateTime(f"{year}-01-01"),
        endtime=UTCDateTime(f"{year+1}-01-01"),
        observatory=observatory,
        template="file://./{OBSERVATORY}{YEAR}WebAbsMaster.cal",
    )


"""
CAL format example:
- ordered by date
- within date, order by H, then D, then Z component
- component values order by start time
- D component values in minutes.


--2015 03 30 (H)
2140-2143 c    175.0  12531.3
2152-2156 c    174.9  12533.3
2205-2210 c    174.8  12533.1
2220-2223 c    174.9  12520.7
--2015 03 30 (D)
2133-2137 c   1128.3   1118.5
2145-2149 c   1128.4   1116.4
2159-2203 c   1128.3   1113.1
2212-2216 c   1128.4   1113.5
--2015 03 30 (Z)
2140-2143 c    -52.9  55403.4
2152-2156 c    -52.8  55403.8
2205-2210 c    -52.8  55404.0
2220-2223 c    -52.8  55410.5
--2015 07 27 (H)
2146-2151 c    173.5  12542.5
2204-2210 c    173.8  12542.5
2225-2229 c    173.8  12547.2
2240-2246 c    173.6  12538.7
--2015 07 27 (D)
2137-2142 c   1127.8   1109.2
2154-2158 c   1128.3   1106.3
2213-2220 c   1128.0   1106.3
2232-2237 c   1128.3   1104.7
--2015 07 27 (Z)
2146-2151 c    -53.9  55382.7
2204-2210 c    -54.0  55382.5
2225-2229 c    -54.1  55383.7
2240-2246 c    -54.1  55389.0
"""
