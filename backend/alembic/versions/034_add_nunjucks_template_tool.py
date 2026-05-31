"""add nunjucks_template tool

Revision ID: 034
Revises: 033
Create Date: 2026-05-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
import json

revision: str = '034'
down_revision: Union[str, Sequence[str], None] = '033'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'

def upgrade() -> None:
    """Add nunjucks_template node tool definition."""
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
        "template": {
            "label": "Template",
            "type": "code",
            "language": "jinja2",
            "placeholder": "Hello {{ name }}!"
        }
    }

    default_props = {
        "template": "Hello {{ name }}!"
    }

    applicable_types = ['data-integration', 'process-flow']

    # Delete existing if present (idempotent)
    op.execute(
        tools_table.delete().where(tools_table.c.type == 'nunjucks_template')
    )

    # Insert new tool
    op.execute(
        tools_table.insert().values(
            id='tool-nunjucks-template-001',
            type='nunjucks_template',
            category='transform',
            name='Templating',
            description='Renders a Nunjucks template string against the flow payload',
            icon='description',
            prop_defs=prop_defs,
            default_props=default_props,
            applicable_diagram_types=applicable_types
        )
    )

def downgrade() -> None:
    """Remove nunjucks_template node tool definition."""
    tools_table = table(
        'editor_tools',
        column('id', sa.String),
        column('type', sa.String),
        schema=SCHEMA
    )
    op.execute(
        tools_table.delete().where(tools_table.c.type == 'nunjucks_template')
    )
