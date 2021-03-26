import json
from obspy import UTCDateTime
from typing import Optional
import typer

from ..adjusted.Affine import Affine
from ..residual import Reading, SpreadsheetSummaryFactory, WebAbsolutesFactory
from ..metadata import (
    GEOMAG_API_URL,
    Metadata,
    MetadataCategory,
    MetadataFactory,
    MetadataQuery,
)


def main():
    typer.run(generate_matrix)


def generate_matrix(
    observatory: str,
    starttime: str,
    endtime: str,
    readings_starttime: str,
    readings_endtime: str,
    input_factory: str = "webabsolutes",
    metadata_url: str = GEOMAG_API_URL,
    output_file: Optional[str] = None,
    output_metadata: bool = False,
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
    elif input_factory == "metadata":
        metadata = MetadataFactory(url=metadata_url).get_metadata(
            query=MetadataQuery(
                station=observatory,
                starttime=readings_starttime,
                endtime=readings_endtime,
                category=MetadataCategory.READING,
                data_valid=True,
                metadata_valid=True,
            )
        )
        readings = [Reading(**m.metadata) for m in metadata]
    else:
        readings = []

    result = Affine(
        observatory=observatory,
        starttime=UTCDateTime(starttime),
        endtime=UTCDateTime(endtime),
    ).calculate(readings=readings)[0]

    if output_metadata:
        MetadataFactory(url=metadata_url).create_metadata(
            metadata=Metadata(
                station=observatory,
                created_by="generate_matrix",
                metadata=result.dict(),
                starttime=result.starttime,
                endtime=result.endtime,
                network="NT",
                category=MetadataCategory.ADJUSTED_MATRIX,
                comment=f"calculated from {readings_starttime} to {readings_endtime}",
            )
        )

    if output_file:
        with open(output_file, "w") as file:
            file.write(result.json())

    if not output_file and not output_metadata:
        print(result.json(indent=2))
