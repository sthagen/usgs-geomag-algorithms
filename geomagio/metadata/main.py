import sys
import json
import os
from typing import Dict, List, Optional

from obspy import UTCDateTime
import typer

from .Metadata import Metadata
from .MetadataCategory import MetadataCategory
from .MetadataFactory import MetadataFactory
from .MetadataQuery import MetadataQuery


GEOMAG_API_HOST = os.getenv("GEOMAG_API_HOST", "geomag.usgs.gov")
GEOMAG_API_URL = f"https://{GEOMAG_API_HOST}/ws/secure/metadata"
if "127.0.0.1" in GEOMAG_API_URL:
    GEOMAG_API_URL = GEOMAG_API_URL.replace("https://", "http://")


ENVIRONMENT_VARIABLE_HELP = """Environment variables:

      GITLAB_API_TOKEN

        (Required) Personal access token with "read_api" scope. Create at
        https://code.usgs.gov/profile/personal_access_tokens

      GEOMAG_API_HOST

        Default "geomag.usgs.gov"

      REQUESTS_CA_BUNDLE

        Use custom certificate bundle
    """


app = typer.Typer(
    help=f"""
    Command line interface for Metadata API

    {ENVIRONMENT_VARIABLE_HELP}
    """
)


def load_metadata(input_file: str) -> Optional[Dict]:
    if input_file is None:
        return None
    if input_file == "-":
        data = json.loads(sys.stdin.read())
        return data
    with open(input_file, "r") as file:
        data = json.load(file)
    return data


def main():
    """Command line interface for Metadata API.

    Registered as "geomag-metadata" console script in setup.py.
    """
    app()


@app.command(
    help=f"""
    Create new metadata.

    {ENVIRONMENT_VARIABLE_HELP}
    """
)
def create(
    category: MetadataCategory = None,
    channel: str = None,
    created_after: str = None,
    created_before: str = None,
    data_valid: bool = True,
    endtime: str = None,
    id: int = None,
    input_file: str = None,
    location: str = None,
    metadata_valid: bool = True,
    network: str = None,
    starttime: str = None,
    station: str = None,
    status: str = None,
    url: str = GEOMAG_API_URL,
    wrap: bool = True,
):
    input_metadata = load_metadata(input_file=input_file)
    if not wrap:
        metadata = Metadata(**input_metadata)
    else:
        metadata = Metadata(
            category=category,
            channel=channel,
            created_after=UTCDateTime(created_after) if created_after else None,
            created_before=UTCDateTime(created_before) if created_before else None,
            data_valid=data_valid,
            endtime=UTCDateTime(endtime) if endtime else None,
            id=id,
            location=location,
            metadata=input_metadata,
            metadata_valid=metadata_valid,
            network=network,
            starttime=UTCDateTime(starttime) if starttime else None,
            station=station,
            status=status or "new",
        )
    metadata = MetadataFactory(url=url).create_metadata(metadata=metadata)
    print(metadata.json())


@app.command(
    help=f"""
    Search existing metadata.

    {ENVIRONMENT_VARIABLE_HELP}
    """
)
def get(
    category: Optional[MetadataCategory] = None,
    channel: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    data_valid: Optional[bool] = None,
    endtime: Optional[str] = None,
    getone: bool = False,
    id: Optional[int] = None,
    location: Optional[str] = None,
    metadata_valid: Optional[bool] = None,
    network: Optional[str] = None,
    status: Optional[List[str]] = typer.Argument(None),
    starttime: Optional[str] = None,
    station: Optional[str] = None,
    url: str = GEOMAG_API_URL,
):
    query = MetadataQuery(
        category=category,
        channel=channel,
        created_after=UTCDateTime(created_after) if created_after else None,
        created_before=UTCDateTime(created_before) if created_before else None,
        data_valid=data_valid,
        endtime=UTCDateTime(endtime) if endtime else None,
        id=id,
        location=location,
        metadata_valid=metadata_valid,
        network=network,
        starttime=UTCDateTime(starttime) if starttime else None,
        station=station,
        status=status,
    )
    metadata = MetadataFactory(url=url).get_metadata(query=query)
    if getone:
        if len(metadata) != 1:
            raise ValueError(f"{len(metadata)} matching records")
        print(metadata[0].json())
    else:
        print("[" + ",\n".join([m.json() for m in metadata]) + "]")


@app.command(
    help=f"""
    Update an existing metadata.

    {ENVIRONMENT_VARIABLE_HELP}
    """
)
def update(
    input_file: str,
    url: str = GEOMAG_API_URL,
):
    metadata_dict = load_metadata(input_file=input_file)
    metadata = Metadata(**metadata_dict)
    response = MetadataFactory(url=url).update_metadata(metadata=metadata)
    print(response.json())
