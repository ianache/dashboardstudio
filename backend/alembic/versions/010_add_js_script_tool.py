"""add js_script tool

Revision ID: 010
Revises: 009
Create Date: 2026-05-14

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import json

revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'
NOW = datetime.utcnow()

def upgrade() -> None:
    tools_table = sa.table(
        'editor_tools',
        sa.column('id', sa.String), sa.column('type', sa.String),
        sa.column('name', sa.String), sa.column('description', sa.Text),
        sa.column('subtitle', sa.String), sa.column('icon', sa.String),
        sa.column('category', sa.String),
        sa.column('applicable_diagram_types', sa.JSON),
        sa.column('prop_defs', sa.JSON), sa.column('default_props', sa.JSON),
        sa.column('created_at', sa.DateTime), sa.column('updated_at', sa.DateTime),
        schema=SCHEMA,
    )

    op.bulk_insert(tools_table, [
        {
            'id': 'tool-js-script',
            'type': 'js_script',
            'name': 'JS Script',
            'description': 'Ejecuta lógica personalizada en JavaScript/TypeScript usando Deno',
            'subtitle': 'Script personalizado',
            'icon': 'javascript',
            'category': 'transform',
            'applicable_diagram_types': ['data-integration', 'process-flow'],
            'prop_defs': {
                'code': {
                    'label': 'Código JS',
                    'type': 'code',
                    'placeholder': 'export default async function(ctx) { ... }'
                }
            },
            'default_props': {
                'code': 'export default async function(ctx) {\n  const { payload } = ctx;\n  console.log("Procesando datos en JS...");\n  \n  // Tu lógica aquí\n  \n  return payload;\n}'
            },
            'created_at': NOW,
            'updated_at': NOW,
        }
    ])

def downgrade() -> None:
    op.execute(f"DELETE FROM {SCHEMA}.editor_tools WHERE type = 'js_script'")
