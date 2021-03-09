import json
from obspy import UTCDateTime
from typing import Optional
import typer

from ..adjusted.Affine import Affine
from ..residual import SpreadsheetSummaryFactory, WebAbsolutesFactory


def main():
    typer.run(generate_matrix)


def generate_matrix(
    observatory: str,
    starttime: str,
    endtime: str,
    readings_starttime: str,
    readings_endtime: str,
    output_file: str,
    input_factory: str = "webabsolutes",
    spreadsheet_directory: Optional[str] = None,
    webabsolutes_url: Optional[
        str
    ] = "https://geomag.usgs.gov/baselines/observation.json.php",
):
    if input_factory == "spreadsheet":
        readings = SpreadsheetSummaryFactory(
            base_directory=spreadsheet_directory
        ).get_readings(
            observatory=observatory,
            starttime=UTCDateTime(readings_starttime),
            endtime=UTCDateTime(readings_endtime),
        )
    elif input_factory == "webabsolutes":
        readings = WebAbsolutesFactory(url=webabsolutes_url).get_readings(
            observatory=observatory,
            starttime=UTCDateTime(readings_starttime),
            endtime=UTCDateTime(readings_endtime),
        )
    else:
        readings = []

    result = Affine(
        observatory=observatory,
        starttime=UTCDateTime(starttime),
        endtime=UTCDateTime(endtime),
    ).calculate(readings=readings)[0]
    result.matrix = result.matrix.tolist()

    with open(output_file, "w") as file:
        json.dump(result.dict(), file)
