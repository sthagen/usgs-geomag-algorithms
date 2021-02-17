import json
import os
from typing import Dict, Optional

from obspy import UTCDateTime
import typer

from ..api.secure.MetadataQuery import MetadataQuery
from ..metadata import MetadataCategory, MetadataFactory


def main():
    typer.run(client)


def client(
    action: str,
    url: str = "http://{}/ws/secure/metadata".format(
        os.getenv("EDGE_HOST", "127.0.0.1:8000")
    ),
    id: Optional[int] = typer.Option(
        None,
        help="Database id required for deleting and updating metadata. NOTE: Metadata requests by id ignore additional parameters",
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
    token: Optional[str] = typer.Option(
        os.getenv("GITLAB_API_TOKEN"), help="Gitlab account access token"
    ),
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
    factory = MetadataFactory(url=url, token=token)
    if action == "delete":
        response = factory.delete_metadata(id=query.id)
    elif action == "get":
        response = factory.get_metadata(query=query)
    elif action in ["post", "update"]:
        try:
            with open(input_file, "r") as file:
                data = json.load(file)
        except (FileNotFoundError, TypeError):
            raise ValueError("Input file invalid or not provided")
        if action == "post":
            response = factory.post_metadata(query=query, data=data)
        elif action == "update":
            response = factory.update_metadata(id=query.id, query=query, data=data)
    else:
        raise ValueError("Invalid action")
    return response
