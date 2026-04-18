"""add diagrams column to dimensional_models

Revision ID: 004
Revises: 003
Create Date: 2026-04-17

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema='biportal' AND table_name='dimensional_models' AND column_name='diagrams'"
    ))
    if not result.fetchone():
        op.add_column(
            'dimensional_models',
            sa.Column('diagrams', sa.JSON(), nullable=True, server_default='[]'),
            schema='biportal'
        )


def downgrade() -> None:
    op.drop_column('dimensional_models', 'diagrams', schema='biportal')
