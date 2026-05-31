"""add llm tool

Revision ID: 035
Revises: 034
Create Date: 2026-05-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
import json

revision: str = '035'
down_revision: Union[str, Sequence[str], None] = '034'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'

def upgrade() -> None:
    """Add llm node tool definition."""
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
        "connection_id": { 
            "label": "Connection", 
            "type": "connection", 
            "connection_type": "llm" 
        },
        "model": {
            "label": "Model Override",
            "type": "text",
            "placeholder": "e.g. gpt-4-turbo, llama3 (optional)"
        },
        "system_prompt": { 
            "label": "System Prompt", 
            "type": "textarea", 
            "placeholder": "You are a helpful assistant..." 
        },
        "user_prompt": { 
            "label": "User Prompt", 
            "type": "textarea", 
            "placeholder": "Summarize this: {{payload.text}}" 
        },
        "temperature": { 
            "label": "Temperature", 
            "type": "number", 
            "default": 0.7 
        },
        "max_tokens": { 
            "label": "Max Tokens", 
            "type": "number", 
            "default": 1024 
        }
    }

    default_props = {
        "temperature": 0.7,
        "max_tokens": 1024,
        "system_prompt": "You are a helpful assistant.",
        "user_prompt": "{{payload}}"
    }

    applicable_types = ['data-integration', 'process-flow']

    # Delete existing if present (idempotent)
    op.execute(
        tools_table.delete().where(tools_table.c.type == 'llm')
    )

    # Insert new tool
    op.execute(
        tools_table.insert().values(
            id='tool-llm-001',
            type='llm',
            category='source',  # Category is source because it's pre-executed
            name='LLM Completion',
            description='Calls an OpenAI-compatible LLM endpoint securely from the backend',
            icon='psychology',
            prop_defs=prop_defs,
            default_props=default_props,
            applicable_diagram_types=applicable_types
        )
    )

def downgrade() -> None:
    """Remove llm node tool definition."""
    tools_table = table(
        'editor_tools',
        column('id', sa.String),
        column('type', sa.String),
        schema=SCHEMA
    )
    op.execute(
        tools_table.delete().where(tools_table.c.type == 'llm')
    )
