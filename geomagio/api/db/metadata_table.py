from sqlalchemy import Boolean, Column, Index, Integer, JSON, String, Table, Text
import sqlalchemy_utc

from .common import sqlalchemy_metadata


"""Metadata database model.

See pydantic model geomagio.metadata.Metadata
"""
metadata = Table(
    "metadata",
    sqlalchemy_metadata,
    ## COLUMNS
    Column("id", Integer, primary_key=True),
    # author
    Column("created_by", String(length=255), index=True),
    Column(
        "created_time",
        sqlalchemy_utc.UtcDateTime,
        default=sqlalchemy_utc.utcnow(),
        index=True,
    ),
    # editor
    Column("updated_by", String(length=255), index=True, nullable=True),
    Column("updated_time", sqlalchemy_utc.UtcDateTime, index=True, nullable=True),
    # time range
    Column("starttime", sqlalchemy_utc.UtcDateTime, index=True, nullable=True),
    Column("endtime", sqlalchemy_utc.UtcDateTime, index=True, nullable=True),
    # what data metadata references, null for wildcard
    Column("network", String(length=255), nullable=True),  # indexed below
    Column("station", String(length=255), nullable=True),  # indexed below
    Column("channel", String(length=255), nullable=True),  # indexed below
    Column("location", String(length=255), nullable=True),  # indexed below
    # category (flag, matrix, etc)
    Column("category", String(length=255)),  # indexed below
    # higher priority overrides lower priority
    Column("priority", Integer, default=1),
    # whether data is valid (primarily for flags)
    Column("data_valid", Boolean, default=True, index=True),
    # whether metadata is valid (based on review)
    Column("metadata_valid", Boolean, default=True, index=True),
    # whether metadata has been reviewed
    Column("reviewed", Boolean, default=True, index=True),
    # metadata json blob
    Column("metadata", JSON, nullable=True),
    # general comment
    Column("comment", Text, nullable=True),
    # review specific comment
    Column("review_comment", Text, nullable=True),
    ## INDICES
    Index(
        "index_station_metadata",
        # sncl
        "network",
        "station",
        "channel",
        "location",
        # type
        "category",
        # date
        "starttime",
        "endtime",
        # valid
        "metadata_valid",
        "data_valid",
        "reviewed",
    ),
    Index(
        "index_category_time",
        # type
        "category",
        # date
        "starttime",
        "endtime",
    ),
)
