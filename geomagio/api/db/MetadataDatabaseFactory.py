from datetime import datetime
from enum import Enum
from typing import List, Union

from fastapi import Response
from obspy import UTCDateTime
from sqlalchemy import or_, Table

from ...metadata import Metadata, MetadataCategory
from .common import database
from .metadata_history_table import metadata_history
from .metadata_table import metadata


class TableType(str, Enum):
    METADATA = "metadata"
    HISTORY = "history"


class MetadataDatabaseFactory(object):
    def __init__(
        self, table: Table = metadata, history_table: Table = metadata_history
    ):
        self.table = table
        self.history_table = history_table

    async def create_metadata(
        self, meta: Metadata, table: TableType = TableType.METADATA
    ) -> Metadata:
        exclude = {"id"}
        if table is TableType.HISTORY:
            query = self.history_table.insert()
            meta.metadata_id = meta.id
        else:
            query = self.table.insert()
            exclude.add("metadata_id")
        values = meta.datetime_dict(exclude=exclude, exclude_none=True)
        query = query.values(**values)
        meta.id = await database.execute(query)
        return meta

    async def delete_metadata(self, id: int) -> None:
        query = self.table.delete().where(self.table.c.id == id)
        await database.execute(query)

    async def get_metadata_by_id(
        self, id: int, table: TableType = TableType.METADATA
    ) -> Union[Metadata, List[Metadata]]:
        if table == TableType.HISTORY:
            query = self.history_table.select()
            query = query.where(self.history_table.c.metadata_id == id)
            rows = await database.fetch_all(query)
            return [Metadata(**row) for row in rows]
        meta = await self.get_metadata(id=id)
        if len(meta) != 1:
            return Response(status_code=404)
        else:
            return meta[0]

    async def get_metadata(
        self,
        *,  # make all params keyword
        id: int = None,
        network: str = None,
        station: str = None,
        channel: str = None,
        location: str = None,
        category: MetadataCategory = None,
        starttime: datetime = None,
        endtime: datetime = None,
        created_after: datetime = None,
        created_before: datetime = None,
        data_valid: bool = None,
        metadata_valid: bool = None,
        reviewed: bool = None,
    ) -> List[Metadata]:
        table = self.table
        query = table.select()
        if id:
            query = query.where(table.c.id == id)
        if category:
            query = query.where(table.c.category == category)
        if network:
            query = query.where(table.c.network == network)
        if station:
            query = query.where(table.c.station == station)
        if channel:
            query = query.where(table.c.channel.like(channel))
        if location:
            query = query.where(table.c.location.like(location))
        if starttime:
            query = query.where(
                or_(table.c.endtime == None, table.c.endtime > starttime)
            )
        if endtime:
            query = query.where(
                or_(table.c.starttime == None, table.c.starttime < endtime)
            )
        if created_after:
            query = query.where(table.c.created_time > created_after)
        if created_before:
            query = query.where(table.c.created_time < created_before)
        if data_valid is not None:
            query = query.where(table.c.data_valid == data_valid)
        if metadata_valid is not None:
            query = query.where(table.c.metadata_valid == metadata_valid)
        if reviewed is not None:
            query = query.where(table.c.reviewed == reviewed)
        rows = await database.fetch_all(query)
        return [Metadata(**row) for row in rows]

    async def update_metadata(
        self,
        meta: Metadata,
        username: str,
    ) -> Metadata:
        original_metadata = await self.get_metadata_by_id(id=meta.id)
        await self.create_metadata(meta=original_metadata, table=TableType.HISTORY)
        meta.updated_by = username
        meta.updated_time = UTCDateTime()
        query = self.table.update().where(self.table.c.id == meta.id)
        values = meta.datetime_dict(exclude={"id", "metadata_id"})
        query = query.values(**values)
        await database.execute(query)
        updated_metadata = await self.get_metadata_by_id(id=meta.id)
        return updated_metadata
