import os
from typing import List

from obspy import UTCDateTime
import openpyxl
import numpy as np

from ..residual import Absolute, Angle, Reading
from ..residual.SpreadsheetAbsolutesFactory import parse_relative_time


class SpreadsheetSummaryFactory(object):
    def __init__(
        self, base_directory=r"Volumes/geomag/pub/Caldata/Checked Baseline Data"
    ):
        self.base_directory = base_directory

    def get_readings(
        self, observatory: str, starttime: UTCDateTime, endtime: UTCDateTime
    ):
        readings = []
        for year in range(starttime.year, endtime.year + 1):
            for (dirpath, _, filenames) in os.walk(self.base_directory):
                for filename in filenames:
                    if (
                        filename.split(".")[-1] != "xlsm"
                        or filename[0:3] != observatory
                    ):
                        continue
                    year = int(filename[3:7])
                    yd = int(filename[7:10])
                    file_date = UTCDateTime(f"{year}-01-01") + (yd * 86400)
                    if starttime <= file_date < endtime:
                        rs = self.parse_spreadsheet(
                            os.path.join(dirpath, filename),
                        )
                        for r in rs:
                            readings.append(r)
        return readings

    def parse_spreadsheet(self, path: str) -> List[Reading]:
        sheet = openpyxl.load_workbook(path, data_only=True)["Sheet1"]
        readings = self._parse_readings(sheet, path)
        return readings

    def _parse_metadata(self, sheet, observatory) -> dict:
        date = sheet["I1"].value
        date = f"{date.year}{date.month:02}{date.day:02}"
        return {
            "observatory": observatory,
            "pier_correction": sheet["C5"].value,
            "instrument": sheet["B3"].value,
            "date": date,
            "observer": sheet["I10"].value,
        }

    def _parse_readings(self, sheet, path):
        metadata = self._parse_metadata(sheet, path.split("/")[-1][0:3])
        date = sheet["I1"].value
        base_date = f"{date.year}{date.month:02}{date.day:02}"
        readings = []
        for d_n in range(10, 14):
            h_n = d_n + 14
            v_n = d_n + 28
            absolutes = [
                Absolute(
                    element="D",
                    absolute=Angle.from_dms(
                        degrees=sheet[f"C{d_n}"].value, minutes=sheet[f"D{d_n}"].value
                    ),
                    baseline=sheet[f"H{d_n}"].value / 60,
                    starttime=parse_relative_time(
                        base_date, "{0:04d}".format(sheet[f"B{v_n}"].value)
                    ),
                    endtime=parse_relative_time(
                        base_date, "{0:04d}".format(sheet[f"B{d_n}"].value)
                    ),
                ),
                Absolute(
                    element="H",
                    absolute=sheet[f"D{h_n}"].value,
                    baseline=sheet[f"H{h_n}"].value,
                    starttime=parse_relative_time(
                        base_date, "{0:04d}".format(sheet[f"B{v_n}"].value)
                    ),
                    endtime=parse_relative_time(
                        base_date, "{0:04d}".format(sheet[f"B{h_n}"].value)
                    ),
                ),
                Absolute(
                    element="Z",
                    absolute=sheet[f"D{v_n}"].value,
                    baseline=sheet[f"H{v_n}"].value,
                    starttime=parse_relative_time(
                        base_date, "{0:04d}".format(sheet[f"B{v_n}"].value)
                    ),
                    endtime=parse_relative_time(
                        base_date, "{0:04d}".format(sheet[f"B{v_n}"].value)
                    ),
                ),
            ]
            valid = [
                sheet[f"J{d_n}"].value,
                sheet[f"J{h_n}"].value,
                sheet[f"J{d_n}"].value,
            ]
            if valid == [None, None, None]:
                readings.append(
                    Reading(
                        metadata=metadata,
                        absolutes=absolutes,
                        pier_correction=metadata["pier_correction"],
                    ),
                )
        return readings
