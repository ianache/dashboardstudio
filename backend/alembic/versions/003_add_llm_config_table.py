"""add llm_config table

Revision ID: 003
Revises: 002
Create Date: 2025-04-07

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('llm_config',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('api_key', sa.String(500), nullable=False),
        sa.Column('created_by', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['biportal.users.id']),
        schema='biportal'
    )
    
    # Create index on provider for faster lookups
    op.create_index(
        'idx_llm_config_provider',
        'llm_config',
        ['provider'],
        unique=False,
        schema='biportal'
    )


def downgrade() -> None:
    op.drop_index('idx_llm_config_provider', table_name='llm_config', schema='biportal')
    op.drop_table('llm_config', schema='biportal')
