import sqlalchemy

from .common import database, sqlalchemy_metadata

# register models with sqlalchemy_metadata by importing
from .metadata_history_table import metadata_history
from .metadata_table import metadata
from .session_table import session


def create_db():
    """Create the database using sqlalchemy."""
    database_url = str(database.url).replace("mysql://", "mysql+pymysql://")
    engine = sqlalchemy.create_engine(database_url)
    sqlalchemy_metadata.create_all(engine)


if __name__ == "__main__":
    create_db()
