"""Add params jsonb field to requests table

Revision ID: add_params_to_requests
Revises: cfa0981297b8
Create Date: 2025-08-03 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_params_to_requests'
down_revision: Union[str, Sequence[str], None] = 'cfa0981297b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add params JSONB field to requests table."""
    op.add_column('requests', sa.Column('params', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    """Remove params field from requests table."""
    op.drop_column('requests', 'params') 