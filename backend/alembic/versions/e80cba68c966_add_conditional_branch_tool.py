"""add conditional_branch tool

Revision ID: e80cba68c966
Revises: 343f76959aa0
Create Date: 2026-05-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
import json

revision: str = 'e80cba68c966'
down_revision: Union[str, Sequence[str], None] = '343f76959aa0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'

def upgrade() -> None:
    # 1. Register conditional_branch tool
    tools_table = table(
        'editor_tools',
        column('id', sa.String),
        column('type', sa.String),
        column('name', sa.String),
        column('description', sa.Text),
        column('icon', sa.String),
        column('category', sa.String),
        column('prop_defs', sa.JSON),
        column('default_props', sa.JSON),
        column('applicable_diagram_types', sa.JSON),
        schema=SCHEMA
    )

    prop_defs = {
        "expression": {
            "label": "Boolean Expression",
            "type": "code",
            "language": "javascript",
            "placeholder": "payload.total > 100"
        }
    }

    op.bulk_insert(
        tools_table,
        [
            {
                'id': 'tool-branch-001',
                'type': 'conditional_branch',
                'name': 'Conditional',
                'description': 'Splits execution flow based on a boolean expression',
                'icon': 'call_split',
                'category': 'transform',
                'prop_defs': prop_defs,
                'default_props': {"expression": "true"},
                'applicable_diagram_types': ["data-integration", "process-flow"]
            }
        ]
    )

def downgrade() -> None:
    op.execute(f"DELETE FROM {SCHEMA}.editor_tools WHERE type = 'conditional_branch'")
