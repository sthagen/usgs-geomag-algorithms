from sqlalchemy import Column, ForeignKey, Integer

from ...metadata import Metadata
from .common import database, sqlalchemy_metadata
from .metadata_table import metadata

# create copy of original metadata table and add to sqlalchemy metadata
metadata_history = metadata.tometadata(
    metadata=sqlalchemy_metadata, name="metadata_history"
)
metadata_history.append_column(
    Column(
        "metadata_id",
        Integer,
        ForeignKey("metadata.id"),
        nullable=False,
    ),
)
metadata_history.indexes.clear()


async def create_metadata(meta: Metadata) -> Metadata:
    query = metadata_history.insert()
    meta.metadata_id = meta.id
    values = meta.datetime_dict(exclude={"id"}, exclude_none=True)
    query = query.values(**values)
    meta.id = await database.execute(query)
    return meta


async def get_metadata(metadata_id: int):
    query = metadata_history.select()
    query = query.where(metadata_history.c.metadata_id == metadata_id)
    rows = await database.fetch_all(query)
    return [Metadata(**row) for row in rows]
