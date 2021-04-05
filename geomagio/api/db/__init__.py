"""geomagio.api.db package.

This package manages the database connection, data models,
and provides methods for data access from other parts of the api.

Modules outside the api should not access the database directly.
"""

from .common import database, sqlalchemy_metadata
from .MetadataDatabaseFactory import MetadataDatabaseFactory

__all__ = [
    "database",
    "sqlalchemy_metadata",
    "MetadataDatabaseFactory",
]
