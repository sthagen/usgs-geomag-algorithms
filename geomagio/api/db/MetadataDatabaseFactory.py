from datetime import datetime
from typing import List, Optional

from databases import Database
from obspy import UTCDateTime
from sqlalchemy import or_

from ...metadata import Metadata, MetadataQuery
from .metadata_history_table import metadata_history
from .metadata_table import metadata


class MetadataDatabaseFactory(object):
    def __init__(self, database: Database):
        self.database = database

    async def create_metadata(self, meta: Metadata) -> Metadata:
        query = metadata.insert()
        meta.status = meta.status or "new"
        values = meta.datetime_dict(exclude={"id", "metadata_id"}, exclude_none=True)
        query = query.values(**values)
        meta.id = await self.database.execute(query)
        return meta

    async def get_metadata(
        self,
        params: MetadataQuery,
        history: bool = False,
    ) -> List[Metadata]:
        table = metadata
        if history:
            table = metadata_history
        query = table.select()
        (
            id,
            category,
            starttime,
            endtime,
            created_after,
            created_before,
            network,
            station,
            channel,
            location,
            data_valid,
            metadata_valid,
            status,
        ) = params.datetime_dict().values()
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
                or_(
                    table.c.endtime == None,
                    table.c.endtime > starttime,
                )
            )
        if endtime:
            query = query.where(
                or_(
                    table.c.starttime == None,
                    table.c.starttime < endtime,
                )
            )
        if created_after:
            query = query.where(table.c.created_time > created_after)
        if created_before:
            query = query.where(table.c.created_time < created_before)
        if data_valid is not None:
            query = query.where(table.c.data_valid == data_valid)
        if metadata_valid is not None:
            query = query.where(table.c.metadata_valid == metadata_valid)
        if status is not None:
            query = query.where(table.c.status.in_(status))
        rows = await self.database.fetch_all(query)
        return [Metadata(**row) for row in rows]

    async def get_metadata_by_id(self, id: int):
        meta = await self.get_metadata(MetadataQuery(id=id))
        if len(meta) != 1:
            raise ValueError(f"{len(meta)} records found")
        return meta[0]

    async def get_metadata_history_by_id(self, id: int) -> Optional[Metadata]:
        query = metadata_history.select()
        query = query.where(metadata_history.c.id == id)
        meta = await self.database.fetch_one(query)
        if meta is None:
            return meta
        return Metadata(**meta)

    async def get_metadata_history_by_metadata_id(
        self, metadata_id: int
    ) -> List[Metadata]:
        async with self.database.transaction() as transaction:
            query = metadata_history.select()
            query = query.where(metadata_history.c.metadata_id == metadata_id).order_by(
                metadata_history.c.updated_time
            )
            rows = await self.database.fetch_all(query)
            metadata = [Metadata(**row) for row in rows]
            current_metadata = await self.get_metadata_by_id(id=metadata_id)
            metadata.append(current_metadata)
            # return records in order of age(newest first)
            metadata.reverse()
            return metadata

    async def update_metadata(self, meta: Metadata, updated_by: str) -> Metadata:
        async with self.database.transaction() as transaction:
            # write current record to metadata history table
            original_metadata = await self.get_metadata_by_id(id=meta.id)
            original_metadata.metadata_id = original_metadata.id
            values = original_metadata.datetime_dict(exclude={"id"}, exclude_none=True)
            query = metadata_history.insert()
            query = query.values(**values)
            original_metadata.id = await self.database.execute(query)
            # update record in metadata table
            meta.updated_by = updated_by
            meta.updated_time = UTCDateTime()
            query = metadata.update().where(metadata.c.id == meta.id)
            values = meta.datetime_dict(exclude={"id", "metadata_id"})
            query = query.values(**values)
            await self.database.execute(query)
            return await self.get_metadata_by_id(id=meta.id)
