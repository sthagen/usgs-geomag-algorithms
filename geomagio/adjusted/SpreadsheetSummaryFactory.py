import os

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
            # TODO: Change to current year when 2020 absolutes are moved into folder
            if year != UTCDateTime().year - 1:
                observatory_directory = os.path.join(
                    self.base_directory, observatory, f"{year}"
                )
            else:
                observatory_directory = self.base_directory
            for (dirpath, _, filenames) in os.walk(observatory_directory):
                for filename in filenames:
                    if filename.split(".")[-1] != "xlsm":
                        continue
                    year = int(filename[3:7])
                    yd = int(filename[7:10])
                    file_date = UTCDateTime(f"{year}-01-01") + (yd * 86400)
                    if starttime <= file_date < endtime:
                        readings.append(
                            self.parse_spreadsheet(
                                os.path.join(dirpath, filename),
                            )
                        )
        return readings

    def parse_spreadsheet(self, path: str) -> Reading:
        sheet = openpyxl.load_workbook(path, data_only=True)["Sheet1"]
        metadata = self._parse_metadata(sheet, path.split("/")[-1][0:3])
        return Reading(
            metadata=metadata,
            absolutes=self._parse_absolutes(sheet),
            pier_correction=metadata["pier_correction"],
        )

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

    def _parse_absolutes(self, sheet):
        date = sheet["I1"].value
        base_date = f"{date.year}{date.month:02}{date.day:02}"

        return [
            Absolute(
                element="D",
                absolute=np.average(
                    [
                        Angle.from_dms(
                            degrees=sheet[f"C{n}"].value, minutes=sheet[f"D{n}"].value
                        )
                        for n in range(10, 14)
                        if sheet[f"J{n}"].value != "Rejected"
                    ]
                ),
                baseline=sheet["H16"].value,
                starttime=parse_relative_time(
                    base_date, "{0:04d}".format(sheet["B10"].value)
                ),
                endtime=parse_relative_time(
                    base_date, "{0:04d}".format(sheet["B13"].value)
                ),
            ),
            Absolute(
                element="H",
                absolute=np.average(
                    [
                        sheet[f"D{n}"].value
                        for n in range(24, 28)
                        if sheet[f"J{n}"].value != "Rejected"
                    ]
                ),
                baseline=sheet["H30"].value,
                starttime=parse_relative_time(
                    base_date, "{0:04d}".format(sheet["B24"].value)
                ),
                endtime=parse_relative_time(
                    base_date, "{0:04d}".format(sheet["B27"].value)
                ),
            ),
            Absolute(
                element="Z",
                absolute=np.average(
                    [
                        sheet[f"D{n}"].value
                        for n in range(38, 42)
                        if sheet[f"J{n}"].value != "Rejected"
                    ]
                ),
                baseline=sheet["H44"].value,
                starttime=parse_relative_time(
                    base_date, "{0:04d}".format(sheet["B38"].value)
                ),
                endtime=parse_relative_time(
                    base_date, "{0:04d}".format(sheet["B41"].value)
                ),
            ),
        ]
