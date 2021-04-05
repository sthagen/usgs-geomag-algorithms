"""Module for metadata service.

Uses login.py for user management.

Anyone can access metadata.
Logged in users can create new metadata.
Update and delete are restricted based on group membership.


Configuration:
    uses environment variables:

    ADMIN_GROUP           - delete is restricted the admin group.
    REVIEWER_GROUP        - update is restricted the reviewer group.
"""
import os
from typing import List

from fastapi import APIRouter, Body, Depends, Request, Response
from obspy import UTCDateTime

from ...metadata import Metadata, MetadataCategory, MetadataQuery
from ... import pydantic_utcdatetime
from ..db import MetadataDatabaseFactory
from .login import require_user, User

# routes for login/logout
router = APIRouter()


@router.post("/metadata", response_model=Metadata)
async def create_metadata(
    request: Request,
    metadata: Metadata,
    user: User = Depends(require_user()),
):
    metadata = await MetadataDatabaseFactory().create_metadata(metadata)
    return Response(metadata.json(), status_code=201, media_type="application/json")


@router.delete("/metadata/{id}")
async def delete_metadata(
    id: int, user: User = Depends(require_user([os.getenv("ADMIN_GROUP", "admin")]))
):
    await MetadataDatabaseFactory().delete_metadata(id)


@router.get("/metadata/{id}/history", response_model=List[Metadata])
async def get_metadata_history(
    id: int,
):
    return await MetadataDatabaseFactory().get_metadata_by_id(id=id, table="history")


@router.get("/metadata", response_model=List[Metadata])
async def get_metadata(
    category: MetadataCategory = None,
    starttime: UTCDateTime = None,
    endtime: UTCDateTime = None,
    created_after: UTCDateTime = None,
    created_before: UTCDateTime = None,
    network: str = None,
    station: str = None,
    channel: str = None,
    location: str = None,
    data_valid: bool = None,
    metadata_valid: bool = True,
    reviewed: bool = None,
):
    query = MetadataQuery(
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
        reviewed=reviewed,
    )
    metas = await MetadataDatabaseFactory().get_metadata(
        **query.datetime_dict(exclude={"id"})
    )
    return metas


@router.get("/metadata/{id}", response_model=Metadata)
async def get_metadata_by_id(id: int):
    return await MetadataDatabaseFactory().get_metadata_by_id(id=id)


@router.put("/metadata/{id}", response_model=Metadata)
async def update_metadata(
    id: int,
    metadata: Metadata = Body(...),
    user: User = Depends(require_user([os.getenv("REVIEWER_GROUP", "reviewer")])),
):
    return await MetadataDatabaseFactory().update_metadata(
        meta=metadata,
        username=user.nickname,
    )
