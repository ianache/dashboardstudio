"""add knowledge_spaces table

Revision ID: 007
Revises: 006
Create Date: 2026-04-26

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime


revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create knowledge_spaces table
    op.create_table(
        'knowledge_spaces',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_by', sa.String(50), sa.ForeignKey('biportal.users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        schema='biportal'
    )
    
    # Create index on name for faster lookups
    op.create_index(
        'idx_knowledge_spaces_name',
        'knowledge_spaces',
        ['name'],
        unique=True,
        schema='biportal'
    )


def downgrade() -> None:
    op.drop_index('idx_knowledge_spaces_name', table_name='knowledge_spaces', schema='biportal')
    op.drop_table('knowledge_spaces', schema='biportal')
