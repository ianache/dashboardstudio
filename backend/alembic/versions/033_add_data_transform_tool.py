"""add data_transform tool

Revision ID: 033
Revises: 032
Create Date: 2026-05-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
import json

revision: str = '033'
down_revision: Union[str, Sequence[str], None] = '032'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'

def upgrade() -> None:
    """Add data_transform node tool definition."""
    tools_table = table(
        'editor_tools',
        column('id', sa.String),
        column('type', sa.String),
        column('category', sa.String),
        column('name', sa.String),
        column('description', sa.String),
        column('icon', sa.String),
        column('prop_defs', sa.JSON),
        column('default_props', sa.JSON),
        column('applicable_diagram_types', sa.JSON),
        schema=SCHEMA
    )

    prop_defs = {
        "code": {
            "label": "Transform Function",
            "type": "code",
            "language": "javascript",
            "placeholder": "// receives data (payload) and ctx (context)\nreturn data;"
        }
    }

    default_props = {
        "code": "return data;"
    }

    applicable_types = ['data-integration', 'process-flow']

    # Delete existing if present (idempotent)
    op.execute(
        tools_table.delete().where(tools_table.c.type == 'data_transform')
    )

    # Insert new tool
    op.execute(
        tools_table.insert().values(
            id='tool-data-transform-001',
            type='data_transform',
            category='transform',
            name='Data Transform',
            description='Reshapes, filters, or maps the flow payload using a JS function body',
            icon='transform',
            prop_defs=prop_defs,
            default_props=default_props,
            applicable_diagram_types=applicable_types
        )
    )

def downgrade() -> None:
    """Remove data_transform node tool definition."""
    tools_table = table(
        'editor_tools',
        column('id', sa.String),
        column('type', sa.String),
        schema=SCHEMA
    )
    op.execute(
        tools_table.delete().where(tools_table.c.type == 'data_transform')
    )
