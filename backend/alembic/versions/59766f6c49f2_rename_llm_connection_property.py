"""rename llm connection property

Revision ID: 59766f6c49f2
Revises: 038
Create Date: 2026-05-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import json

revision: str = '59766f6c49f2'
down_revision: Union[str, Sequence[str], None] = '038'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'

def upgrade() -> None:
    # 1. Update prop_defs to use 'CONNECTION' as key and label
    conn_prop = {
        "CONNECTION": { 
            "label": "CONNECTION", 
            "type": "connection", 
            "connection_type": "llm" 
        }
    }
    
    # We need to cast prop_defs to jsonb for the - operator
    op.execute(f"""
        UPDATE {SCHEMA}.editor_tools 
        SET prop_defs = (prop_defs::jsonb - 'connection_id' || '{json.dumps(conn_prop)}'::jsonb)::json
        WHERE type = 'llm'
    """)

def downgrade() -> None:
    # Revert to 'connection_id'
    old_prop = {
        "connection_id": { 
            "label": "Connection", 
            "type": "connection", 
            "connection_type": "llm" 
        }
    }
    op.execute(f"""
        UPDATE {SCHEMA}.editor_tools 
        SET prop_defs = (prop_defs::jsonb - 'CONNECTION' || '{json.dumps(old_prop)}'::jsonb)::json
        WHERE type = 'llm'
    """)
