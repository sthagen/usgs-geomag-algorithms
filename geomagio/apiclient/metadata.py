import sys
import json
import os
from typing import Dict, Optional

from obspy import UTCDateTime
import typer

from ..api.secure.MetadataQuery import MetadataQuery
from ..metadata import Metadata, MetadataCategory
from .MetadataFactory import MetadataFactory


def load_metadata(input_file) -> Optional[Dict]:
    if input_file is None:
        return None
    if input_file == "-":
        data = json.loads(sys.stdin.read())
        return data
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
    category: MetadataCategory = None,
    channel: str = None,
    created_after: str = None,
    created_before: str = None,
    data_valid: bool = True,
    endtime: str = None,
    id: int = None,
    input_file: str = typer.Option(
        None,
        help="JSON formatted file containing non-shared metadata information",
    ),
    location: str = None,
    metadata_valid: bool = True,
    network: str = None,
    starttime: str = None,
    station: str = None,
    wrap: bool = True,
):

    if wrap == True:
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
    elif wrap == False:
        metadata_dict = load_metadata(input_file=input_file)
        metadata = Metadata(**metadata_dict)
    response = MetadataFactory(url=url).create_metadata(metadata=metadata)
    print(response.json())


@app.command()
def delete(
    url: str = "http://{}/ws/secure/metadata".format(
        os.getenv("GEOMAG_API_HOST", "127.0.0.1:8000")
    ),
    category: MetadataCategory = None,
    channel: str = None,
    created_after: str = None,
    created_before: str = None,
    data_valid: bool = True,
    endtime: str = None,
    id: int = None,
    input_file: str = typer.Option(
        None,
        help="JSON formatted file containing non-shared metadata information",
    ),
    location: str = None,
    metadata_valid: bool = True,
    network: str = None,
    starttime: str = None,
    station: str = None,
):
    if input_file is not None:
        metadata_dict = load_metadata(input_file=input_file)
        metadata = Metadata(**metadata_dict)
    else:
        metadata = Metadata(
            id=id,
            category=category,
            starttime=starttime,
            endtime=endtime,
            created_after=created_after,
            created_before=created_before,
            network=network,
            station=station,
            channel=channel,
            location=location,
            data_valid=data_valid,
            metadata_valid=metadata_valid,
        )
    response = MetadataFactory(url=url).delete_metadata(metadata=metadata)
    print(response.json())


@app.command()
def get(
    url: str = "http://{}/ws/secure/metadata".format(
        os.getenv("GEOMAG_API_HOST", "127.0.0.1:8000")
    ),
    category: Optional[MetadataCategory] = None,
    channel: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    data_valid: Optional[bool] = True,
    endtime: Optional[str] = None,
    id: Optional[int] = None,
    location: Optional[str] = None,
    metadata_valid: Optional[bool] = True,
    network: Optional[str] = None,
    starttime: Optional[str] = None,
    station: Optional[str] = None,
    unwrap: bool = False,
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
    if unwrap:
        metadata = [json.dumps(m.metadata) for m in metadata]
    else:
        metadata = [m.json() for m in metadata]
    if len(metadata) == 1:
        print(metadata[0])
        return
    print(metadata)


@app.command()
def update(
    url: str = "http://{}/ws/secure/metadata".format(
        os.getenv("GEOMAG_API_HOST", "127.0.0.1:8000")
    ),
    category: MetadataCategory = None,
    channel: str = None,
    created_after: str = None,
    created_before: str = None,
    data_valid: bool = True,
    endtime: str = None,
    id: int = None,
    input_file: str = typer.Option(
        None,
        help="JSON formatted file containing non-shared metadata information",
    ),
    location: str = None,
    metadata_valid: bool = True,
    network: str = None,
    starttime: str = None,
    station: str = None,
):
    if input_file is not None:
        metadata_dict = load_metadata(input_file=input_file)
        metadata = Metadata(**metadata_dict)

    else:
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
    print(response.json())


def main():
    app()
