import os
from typing import Literal, Optional

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
    metadata_valid: Optional[bool] = True,
):
    query = MetadataQuery(
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
    factory = MetadataFactory(url=url)
    if action == "delete":
        factory.delete_metadata(query=query)
    elif action == "get":
        metadata = factory.get_metadata(query=query)
    if action == "post":
        factory.post_metadata(query=query)
    if action == "update":
        factory.update_metadata(query=query)
    return metadata
