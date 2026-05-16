"""update ods_pg tool for dynamic selectors

Revision ID: 030
Revises: fb3010eb1d9a
Create Date: 2026-05-16

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
import json

revision: str = '030'
down_revision: Union[str, None] = 'fb3010eb1d9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'

def upgrade() -> None:
    """Update ods_pg tool to support dynamic selectors and identity fields."""
    tools_table = table(
        'editor_tools',
        column('id', sa.String),
        column('type', sa.String),
        column('prop_defs', sa.JSON),
        column('default_props', sa.JSON),
        schema=SCHEMA
    )
    
    # New prop_defs with dynamic selectors
    new_prop_defs = {
        'connection_id': {
            'label': 'Conexión de Datos',
            'type': 'select',
            'options_source': 'data_sources',
            'filter_by_type': 'postgresql'
        },
        'schema': {
            'label': 'Schema destino',
            'type': 'text',
            'placeholder': 'ods',
            'default': 'ods'
        },
        'table': {
            'label': 'Tabla destino',
            'type': 'dynamic_select',
            'depends_on': ['connection_id', 'schema'],
            'refreshable': True,
            'placeholder': 'Seleccione una tabla...',
            'fetch_endpoint': '/api/v1/data-sources/{connection_id}/tables?schema={schema}'
        },
        'write_mode': {
            'label': 'Modo escritura',
            'type': 'select',
            'options': [
                {'value': 'append', 'label': 'Append'},
                {'value': 'upsert', 'label': 'Upsert'},
                {'value': 'overwrite', 'label': 'Overwrite'},
                {'value': 'merge', 'label': 'Merge (SCD2)'}
            ]
        },
        'identity_fields': {
            'label': 'Campos de Identidad (PK)',
            'type': 'multi_select',
            'show_if': {'field': 'write_mode', 'equals': 'upsert'},
            'depends_on': ['connection_id', 'table', 'schema'],
            'refreshable': True,
            'placeholder': 'Seleccione columnas...',
            'fetch_endpoint': '/api/v1/data-sources/{connection_id}/tables/{table}/columns?schema={schema}'
        },
        'batch_size': {
            'label': 'Tamaño de batch',
            'type': 'text',
            'placeholder': '1000',
            'default': '1000'
        }
    }
    
    # New default props with empty values for new fields
    new_default_props = {
        'connection_id': '',
        'schema': 'ods',
        'table': '',
        'write_mode': 'upsert',
        'identity_fields': [],
        'batch_size': '1000'
    }
    
    op.execute(
        tools_table.update()
        .where(tools_table.c.type == 'ods_pg')
        .values(
            prop_defs=new_prop_defs,
            default_props=new_default_props
        )
    )

def downgrade() -> None:
    """Restore original ods_pg tool definition."""
    tools_table = table(
        'editor_tools',
        column('id', sa.String),
        column('type', sa.String),
        column('prop_defs', sa.JSON),
        column('default_props', sa.JSON),
        schema=SCHEMA
    )
    
    old_prop_defs = {
        'schema': {'label': 'Schema destino', 'type': 'text', 'placeholder': 'ods'},
        'table': {'label': 'Tabla destino', 'type': 'text', 'placeholder': 'fact_ventas'},
        'write_mode': {
            'label': 'Modo escritura',
            'type': 'select',
            'options': [
                {'value': 'append', 'label': 'Append'},
                {'value': 'upsert', 'label': 'Upsert'},
                {'value': 'overwrite', 'label': 'Overwrite'},
                {'value': 'merge', 'label': 'Merge (SCD2)'}
            ]
        },
        'batch_size': {'label': 'Tamaño de batch', 'type': 'text', 'placeholder': '1000'}
    }
    
    old_default_props = {
        'schema': 'ods',
        'table': '',
        'write_mode': 'upsert',
        'batch_size': '1000'
    }
    
    op.execute(
        tools_table.update()
        .where(tools_table.c.type == 'ods_pg')
        .values(
            prop_defs=old_prop_defs,
            default_props=old_default_props
        )
    )
