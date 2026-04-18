"""add currencies table

Revision ID: 005
Revises: 004
Create Date: 2026-04-17

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'currencies',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('code', sa.String(10), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        schema='biportal'
    )


def downgrade() -> None:
    op.drop_table('currencies', schema='biportal')
