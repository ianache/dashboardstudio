"""add email tool

Revision ID: 032
Revises: 202fd2be6265
Create Date: 2026-05-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
import json

revision: str = '032'
down_revision: Union[str, Sequence[str], None] = '202fd2be6265'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'


def upgrade() -> None:
    """Add email node tool definition with SMTP connection selector."""
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
    
    # Email tool property definitions
    # Supports SMTP connection selector, recipients, subject, body with templates
    prop_defs = {
        'connection_id': {
            'type': 'dynamic_select',
            'label': 'SMTP Connection',
            'required': True,
            'description': 'SMTP server connection to use',
            'endpoint': '/api/v1/data-sources?type=smtp',
            'placeholder': 'Select SMTP connection...'
        },
        'to': {
            'type': 'string',
            'label': 'To',
            'required': True,
            'description': 'Recipient email addresses (comma-separated)',
            'placeholder': 'user@example.com, admin@example.com'
        },
        'cc': {
            'type': 'string',
            'label': 'CC',
            'required': False,
            'description': 'CC email addresses (comma-separated)',
            'placeholder': 'cc@example.com'
        },
        'bcc': {
            'type': 'string',
            'label': 'BCC',
            'required': False,
            'description': 'BCC email addresses (comma-separated)',
            'placeholder': 'bcc@example.com'
        },
        'subject': {
            'type': 'string',
            'label': 'Subject',
            'required': True,
            'description': 'Email subject with {{variable}} template support',
            'placeholder': 'Welcome {{user.name}}!'
        },
        'body': {
            'type': 'textarea',
            'label': 'Body',
            'required': True,
            'description': 'Email body with {{variable}} and {% for %} template support',
            'placeholder': 'Hello {{user.name}},\n\nYour order #{{order.id}} is ready.',
            'rows': 10
        },
        'format': {
            'type': 'select',
            'label': 'Format',
            'required': True,
            'options': [
                {'value': 'html', 'label': 'HTML'},
                {'value': 'text', 'label': 'Plain Text'}
            ],
            'default': 'html'
        }
    }
    
    # Default property values
    default_props = {
        'connection_id': '',
        'to': '',
        'cc': '',
        'bcc': '',
        'subject': '',
        'body': '',
        'format': 'html'
    }
    
    # Applicable diagram types for email node
    applicable_types = ['data-integration', 'process-flow']
    
    # Delete existing email tool if present (idempotent upgrade)
    op.execute(
        tools_table.delete().where(tools_table.c.type == 'email')
    )
    
    # Insert new email tool definition
    op.execute(
        tools_table.insert().values(
            id='tool-email-001',
            type='email',
            category='destination',
            name='Email',
            description='Send emails with dynamic templates via SMTP',
            icon='email',
            prop_defs=prop_defs,
            default_props=default_props,
            applicable_diagram_types=applicable_types
        )
    )


def downgrade() -> None:
    """Remove email node tool definition."""
    tools_table = table(
        'editor_tools',
        column('id', sa.String),
        column('type', sa.String),
        schema=SCHEMA
    )
    
    op.execute(
        tools_table.delete().where(tools_table.c.type == 'email')
    )
