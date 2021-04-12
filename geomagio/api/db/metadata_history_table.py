from sqlalchemy import Column, ForeignKey, Integer

from .common import sqlalchemy_metadata
from .metadata_table import metadata

# create copy of original metadata table and add to sqlalchemy metadata
metadata_history = metadata.tometadata(
    metadata=sqlalchemy_metadata, name="metadata_history"
)
metadata_history.indexes.clear()
metadata_history.append_column(
    Column(
        "metadata_id",
        Integer,
        ForeignKey("metadata.id"),
        nullable=False,
    ),
)
