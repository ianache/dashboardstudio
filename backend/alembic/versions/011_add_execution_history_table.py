"""add integration_flow_executions table

Revision ID: 011
Revises: 010
Create Date: 2026-05-14

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'

def upgrade() -> None:
    op.create_table(
        'integration_flow_executions',
        sa.Column('id',          sa.String(50),  primary_key=True),
        sa.Column('flow_id',     sa.String(50),  sa.ForeignKey(f'{SCHEMA}.integration_flows.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status',      sa.String(20),  nullable=False),
        sa.Column('logs',        sa.JSON(),      nullable=False, server_default='[]'),
        sa.Column('result_data', sa.JSON(),      nullable=True),
        sa.Column('duration_ms', sa.Integer(),   nullable=True),
        sa.Column('executed_by', sa.String(50),  sa.ForeignKey(f'{SCHEMA}.users.id'), nullable=True),
        sa.Column('created_at',  sa.DateTime(),  nullable=False, server_default=sa.func.now()),
        schema=SCHEMA,
    )
    op.create_index('idx_if_exec_flow_id', 'integration_flow_executions', ['flow_id'], schema=SCHEMA)

def downgrade() -> None:
    op.drop_index('idx_if_exec_flow_id', table_name='integration_flow_executions', schema=SCHEMA)
    op.drop_table('integration_flow_executions', schema=SCHEMA)
