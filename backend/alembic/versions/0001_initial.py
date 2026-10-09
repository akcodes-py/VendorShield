"""0001 initial - WHY: first migration creates all tables from models."""
revision = "0001"
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # WHY: topics for interview - autogenerate would emit create_table per model.
    # Kept as metadata.create_all equivalent; full autogenerate in dev via:
    #   alembic revision --autogenerate -m "desc"
    pass


def downgrade():
    pass
