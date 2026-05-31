"""align llm tool with ods_pg connection selection

Revision ID: fea5aebba9bd
Revises: 59766f6c49f2
Create Date: 2026-05-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import json

revision: str = 'fea5aebba9bd'
down_revision: Union[str, Sequence[str], None] = '59766f6c49f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'

def upgrade() -> None:
    # 1. Update LLM tool: category source, remove CONNECTION from prop_defs, add connection_type to default_props
    op.execute(f"""
        UPDATE {SCHEMA}.editor_tools 
        SET category = 'source',
            prop_defs = prop_defs::jsonb - 'CONNECTION' - 'connection_id',
            default_props = default_props::jsonb || '{{"connection_type": "llm", "connection_id": ""}}'::jsonb
        WHERE type = 'llm'
    """)
    
    # 2. Update ODS_PG tool: remove connection_id from prop_defs (it's handled by standard block), add connection_type to default_props
    op.execute(f"""
        UPDATE {SCHEMA}.editor_tools 
        SET prop_defs = prop_defs::jsonb - 'connection_id',
            default_props = default_props::jsonb || '{{"connection_type": "postgresql", "connection_id": ""}}'::jsonb
        WHERE type = 'ods_pg'
    """)

def downgrade() -> None:
    # Revert LLM tool
    op.execute(f"""
        UPDATE {SCHEMA}.editor_tools 
        SET category = 'transform',
            prop_defs = prop_defs::jsonb || '{{"CONNECTION": {{"label": "CONNECTION", "type": "connection", "connection_type": "llm"}}}}'::jsonb
        WHERE type = 'llm'
    """)
    
    # Revert ODS_PG tool
    op.execute(f"""
        UPDATE {SCHEMA}.editor_tools 
        SET prop_defs = prop_defs::jsonb || '{{"connection_id": {{"label": "Conexión de Datos", "type": "select", "options_source": "data_sources", "filter_by_type": "postgresql"}}}}'::jsonb
        WHERE type = 'ods_pg'
    """)
