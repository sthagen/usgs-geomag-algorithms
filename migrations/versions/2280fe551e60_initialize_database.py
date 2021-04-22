"""initialize database

Revision ID: 2280fe551e60
Revises:
Create Date: 2021-04-22 13:06:28.852803

"""
from alembic import op

from geomagio.api.db.create import create_db


# revision identifiers, used by Alembic.
revision = "2280fe551e60"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    create_db()


def downgrade():
    # ### start Alembic commands ###
    op.drop_table("metadata_history")
    op.drop_index(op.f("ix_session_updated"), table_name="session")
    op.drop_index(op.f("ix_session_session_id"), table_name="session")
    op.drop_table("session")
    op.drop_index(op.f("ix_metadata_updated_time"), table_name="metadata")
    op.drop_index(op.f("ix_metadata_updated_by"), table_name="metadata")
    op.drop_index(op.f("ix_metadata_starttime"), table_name="metadata")
    op.drop_index(op.f("ix_metadata_metadata_valid"), table_name="metadata")
    op.drop_index(op.f("ix_metadata_endtime"), table_name="metadata")
    op.drop_index(op.f("ix_metadata_data_valid"), table_name="metadata")
    op.drop_index(op.f("ix_metadata_created_time"), table_name="metadata")
    op.drop_index(op.f("ix_metadata_created_by"), table_name="metadata")
    op.drop_index("index_station_metadata", table_name="metadata")
    op.drop_index("index_category_time", table_name="metadata")
    op.drop_table("metadata")
    # ### end Alembic commands ###
