import os

from obspy import UTCDateTime
import openpyxl
from typing import List

from .Absolute import Absolute
from . import Angle
from .Reading import Reading
from .SpreadsheetAbsolutesFactory import parse_relative_time


class SpreadsheetSummaryFactory(object):
    """Read absolutes from summary spreadsheets"""

    def __init__(self, base_directory: str):
        self.base_directory = base_directory

    def get_readings(
        self, observatory: str, starttime: UTCDateTime, endtime: UTCDateTime
    ) -> List[Reading]:
        """Gathers readings from factory's base directory

        Attributes
        ----------
        observatory: 3-letter observatory code
        starttime: beginning date of readings
        endtime: end date of readings
        """
        readings = []
        start_filename = f"{observatory}{starttime.datetime:%Y%j%H%M}.xlsm"
        end_filename = f"{observatory}{endtime.datetime:%Y%j%H%M}.xlsm"
        for year in range(starttime.year, endtime.year + 1):
            observatory_directory = os.path.join(
                self.base_directory, observatory, f"{year}"
            )
            for (dirpath, _, filenames) in os.walk(observatory_directory):
                filenames.sort()
                for filename in filenames:
                    if start_filename <= filename < end_filename:
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

    def _parse_metadata(self, sheet: openpyxl.worksheet, observatory: str) -> dict:
        """gather metadata from spreadsheet

        Attributes
        ----------
        sheet: excel sheet containing residual summary values
        observatory: 3-letter observatory code
        """
        date = sheet["I1"].value
        date = f"{date.year}{date.month:02}{date.day:02}"
        return {
            "observatory": observatory,
            "pier_correction": sheet["C5"].value,
            "instrument": sheet["B3"].value,
            "date": date,
            "observer": sheet["I10"].value,
        }

    def _parse_readings(self, sheet: openpyxl.worksheet, path: str) -> List[Reading]:
        """get list of readings from spreadsheet

        Attributes
        ----------
        sheet: excel sheet containing residual summary values
        path: spreadsheet's filepath

        Outputs
        -------
        List of valid readings from spreadsheet.
        If all readings are valid, 4 readings are returned
        """
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
