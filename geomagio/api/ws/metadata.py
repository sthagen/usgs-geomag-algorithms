from typing import List

from fastapi import APIRouter, Query
from obspy import UTCDateTime

from ...metadata import Metadata, MetadataCategory, MetadataQuery
from ..db.common import database
from ..db import MetadataDatabaseFactory

router = APIRouter()


@router.get("/metadata", response_model=List[Metadata])
async def get_metadata(
    category: MetadataCategory = None,
    starttime: UTCDateTime = None,
    endtime: UTCDateTime = None,
    network: str = None,
    station: str = None,
    channel: str = None,
    location: str = None,
    data_valid: bool = None,
    metadata_valid: bool = True,
    status: List[str] = Query(None),
):
    query = MetadataQuery(
        category=category,
        starttime=starttime,
        endtime=endtime,
        network=network,
        station=station,
        channel=channel,
        location=location,
        data_valid=data_valid,
        metadata_valid=metadata_valid,
        status=status,
    )
    metas = await MetadataDatabaseFactory(database=database).get_metadata(
        **query.datetime_dict(exclude={"id"})
    )
    return metas
