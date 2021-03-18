import sys
import json
import os
from typing import Dict, Optional

from obspy import UTCDateTime
import typer

from ..api.secure.MetadataQuery import MetadataQuery
from ..metadata import Metadata, MetadataCategory
from .MetadataFactory import MetadataFactory


def load_metadata(input_file: str) -> Optional[Dict]:
    if input_file is None:
        return None
    if input_file == "-":
        data = json.loads(sys.stdin.read())
        return data
    with open(input_file, "r") as file:
        data = json.load(file)
    return data


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
    input_file: str = None,
    location: str = None,
    metadata_valid: bool = True,
    network: str = None,
    starttime: str = None,
    station: str = None,
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
            metadata = input_metadata["metadata"],
            metadata_valid=metadata_valid,
            network=network,
            starttime=UTCDateTime(starttime) if starttime else None,
            station=station,
        )
    metadata = MetadataFactory(url=url).create_metadata(metadata=metadata)
    print(metadata.json())


@app.command()
def delete(
    input_file: str,
    url: str = "http://{}/ws/secure/metadata".format(
        os.getenv("GEOMAG_API_HOST", "127.0.0.1:8000")
    ),
):
    metadata_dict = load_metadata(input_file=input_file)
    metadata = Metadata(**metadata_dict)
    deleted = MetadataFactory(url=url).delete_metadata(metadata=metadata)
    print(deleted)


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
    getone: bool = False,
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
    )
    metadata = MetadataFactory(url=url).get_metadata(query=query)
    if not metadata:
        print([])
        return

    if getone:
        if len(metadata) > 1:
            raise ValueError("More than one matching record")
        print(metadata[0].json())
        return
    print([m.json() for m in metadata])
    


@app.command()
def update(
    input_file: str,
    url: str = "http://{}/ws/secure/metadata".format(
        os.getenv("GEOMAG_API_HOST", "127.0.0.1:8000")
    ),
):
    metadata_dict = load_metadata(input_file=input_file)
    metadata = Metadata(**metadata_dict)
    response = MetadataFactory(url=url).update_metadata(metadata=metadata)
    print(response.json())


def main():
    app()
