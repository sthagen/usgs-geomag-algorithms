import json
import os
from typing import Optional

from obspy import UTCDateTime
import typer

from ..api.secure.MetadataQuery import MetadataQuery
from ..metadata import Metadata, MetadataCategory
from .MetadataFactory import MetadataFactory


def main():
    typer.run(client)


def client(
    action: str,
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

    factory = MetadataFactory(url=url, token=os.getenv("GITLAB_API_TOKEN"))
    if action == "delete":
        response = factory.delete_metadata(metadata=metadata)
    elif action == "get":
        response = factory.get_metadata(
            query=MetadataQuery(
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
        )
    elif action in ["create", "update"]:
        try:
            with open(input_file, "r") as file:
                data = json.load(file)
        except (FileNotFoundError, TypeError):
            data = None
        metadata.metadata = data
        if action == "create":
            response = factory.create_metadata(metadata=metadata)
        elif action == "update":
            response = factory.update_metadata(metadata=metadata)
    else:
        raise ValueError("Invalid action")
    return response
