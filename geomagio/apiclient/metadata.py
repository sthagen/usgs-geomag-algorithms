import json
import os
from typing import Dict, Optional

from obspy import UTCDateTime
import typer

from ..api.secure.MetadataQuery import MetadataQuery
from ..metadata import Metadata, MetadataCategory
from .MetadataFactory import MetadataFactory


def load_metadata(input_file) -> Optional[Dict]:
    try:
        with open(input_file, "r") as file:
            data = json.load(file)
        return data
    except (FileNotFoundError, TypeError):
        return None


app = typer.Typer()


@app.command()
def create(
    url: str = "http://{}/ws/secure/metadata".format(
        os.getenv("GEOMAG_API_HOST", "127.0.0.1:8000")
    ),
    id: Optional[int] = None,
    category: Optional[MetadataCategory] = None,
    starttime: Optional[str] = None,
    endtime: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    network: Optional[str] = None,
    station: Optional[str] = None,
    channel: Optional[str] = None,
    location: Optional[str] = None,
    data_valid: Optional[bool] = True,
    metadata_valid: Optional[bool] = True,
    input_file: Optional[str] = typer.Option(
        None,
        help="JSON formatted file containing non-shared metadata information",
    ),
):
    metadata = Metadata(
        id=id,
        category=category,
        starttime=UTCDateTime(starttime) if starttime else None,
        endtime=UTCDateTime(endtime) if endtime else None,
        created_after=UTCDateTime(created_after) if created_after else None,
        created_before=UTCDateTime(created_before) if created_before else None,
        network=network,
        station=station,
        channel=channel,
        location=location,
        data_valid=data_valid,
        metadata_valid=metadata_valid,
    )
    metadata.metadata = load_metadata(input_file=input_file)
    response = MetadataFactory(url=url).create_metadata(metadata=metadata)
    return response


@app.command()
def delete(
    id: int,
    url: str = "http://{}/ws/secure/metadata".format(
        os.getenv("GEOMAG_API_HOST", "127.0.0.1:8000")
    ),
):
    response = MetadataFactory(url=url).delete_metadata(metadata=Metadata(id=id))
    return response


@app.command()
def get(
    url: str = "http://{}/ws/secure/metadata".format(
        os.getenv("GEOMAG_API_HOST", "127.0.0.1:8000")
    ),
    id: Optional[int] = None,
    category: Optional[MetadataCategory] = None,
    starttime: Optional[str] = None,
    endtime: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    network: Optional[str] = None,
    station: Optional[str] = None,
    channel: Optional[str] = None,
    location: Optional[str] = None,
    data_valid: Optional[bool] = None,
    metadata_valid: Optional[bool] = None,
):
    query = MetadataQuery(
        id=id,
        category=category,
        starttime=UTCDateTime(starttime) if starttime else None,
        endtime=UTCDateTime(endtime) if endtime else None,
        created_after=UTCDateTime(created_after) if created_after else None,
        created_before=UTCDateTime(created_before) if created_before else None,
        network=network,
        station=station,
        channel=channel,
        location=location,
        data_valid=data_valid,
        metadata_valid=metadata_valid,
    )
    metadata = MetadataFactory(url=url).get_metadata(query=query)
    return metadata


@app.command()
def update(
    id: int,
    url: str = "http://{}/ws/secure/metadata".format(
        os.getenv("GEOMAG_API_HOST", "127.0.0.1:8000")
    ),
    category: Optional[MetadataCategory] = None,
    starttime: Optional[str] = None,
    endtime: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    network: Optional[str] = None,
    station: Optional[str] = None,
    channel: Optional[str] = None,
    location: Optional[str] = None,
    data_valid: Optional[bool] = True,
    metadata_valid: Optional[bool] = True,
    input_file: Optional[str] = typer.Option(
        None,
        help="JSON formatted file containing non-shared metadata information",
    ),
):
    metadata = Metadata(
        id=id,
        category=category,
        starttime=UTCDateTime(starttime) if starttime else None,
        endtime=UTCDateTime(endtime) if endtime else None,
        created_after=UTCDateTime(created_after) if created_after else None,
        created_before=UTCDateTime(created_before) if created_before else None,
        network=network,
        station=station,
        channel=channel,
        location=location,
        data_valid=data_valid,
        metadata_valid=metadata_valid,
    )
    metadata.metadata = load_metadata(input_file=input_file)
    response = MetadataFactory(url=url).update_metadata(metadata=metadata)
    return response


def main():
    app()
