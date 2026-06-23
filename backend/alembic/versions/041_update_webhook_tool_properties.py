"""update webhook tool properties

Revision ID: 041
Revises: 039, 040
Create Date: 2026-06-06

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import json

revision: str = '041'
down_revision: Union[str, Sequence[str], None] = ('039', '040')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'

NEW_PROP_DEFS = {
    'url': {
        'label': 'URL',
        'type': 'text',
        'required': True,
        'placeholder': 'https://hooks.example.com/...'
    },
    'method': {
        'label': 'Método',
        'type': 'select',
        'required': True,
        'options': [
            {'value': 'POST', 'label': 'POST'},
            {'value': 'GET', 'label': 'GET'},
            {'value': 'PUT', 'label': 'PUT'},
            {'value': 'DELETE', 'label': 'DELETE'},
            {'value': 'PATCH', 'label': 'PATCH'}
        ],
        'default': 'POST'
    },
    'headers': {
        'label': 'Headers (JSON)',
        'type': 'textarea',
        'required': False,
        'description': 'HTTP headers in JSON format (e.g. {"Content-Type": "application/json"}), with template support',
        'placeholder': '{\n  "Content-Type": "application/json",\n  "Authorization": "Bearer {{ variables.token }}"\n}',
        'rows': 4
    },
    'query': {
        'label': 'Query Parameters (JSON)',
        'type': 'textarea',
        'required': False,
        'description': 'URL query parameters in JSON format, with template support',
        'placeholder': '{\n  "param1": "value1",\n  "param2": "{{ payload.id }}"\n}',
        'rows': 4
    },
    'body': {
        'label': 'Body (Payload)',
        'type': 'textarea',
        'required': False,
        'description': 'HTTP request body payload, with Jinja2/Nunjucks template support',
        'placeholder': '{\n  "event": "user_created",\n  "name": "{{ payload.name }}",\n  "timestamp": "{{ variables.now }}"\n}',
        'rows': 6
    },
    'trigger_on': {
        'label': 'Disparar en',
        'type': 'select',
        'required': True,
        'options': [
            {'value': 'success', 'label': 'Éxito'},
            {'value': 'error', 'label': 'Error'},
            {'value': 'always', 'label': 'Siempre'}
        ],
        'default': 'success'
    }
}

NEW_DEFAULT_PROPS = {
    'url': '',
    'method': 'POST',
    'headers': '',
    'query': '',
    'body': '',
    'trigger_on': 'success'
}

OLD_PROP_DEFS = {
    'url': {
        'label': 'URL',
        'type': 'text',
        'placeholder': 'https://hooks.example.com/...'
    },
    'method': {
        'label': 'Método',
        'type': 'select',
        'options': [
            {'value': 'POST', 'label': 'POST'},
            {'value': 'GET', 'label': 'GET'}
        ]
    },
    'trigger_on': {
        'label': 'Disparar en',
        'type': 'select',
        'options': [
            {'value': 'success', 'label': 'Éxito'},
            {'value': 'error', 'label': 'Error'},
            {'value': 'always', 'label': 'Siempre'}
        ]
    }
}

OLD_DEFAULT_PROPS = {
    'url': '',
    'method': 'POST',
    'trigger_on': 'success'
}


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            f"UPDATE {SCHEMA}.editor_tools "
            f"SET prop_defs = :prop_defs, default_props = :default_props "
            f"WHERE type = 'webhook'"
        ),
        {
            "prop_defs": json.dumps(NEW_PROP_DEFS),
            "default_props": json.dumps(NEW_DEFAULT_PROPS)
        }
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            f"UPDATE {SCHEMA}.editor_tools "
            f"SET prop_defs = :prop_defs, default_props = :default_props "
            f"WHERE type = 'webhook'"
        ),
        {
            "prop_defs": json.dumps(OLD_PROP_DEFS),
            "default_props": json.dumps(OLD_DEFAULT_PROPS)
        }
    )
