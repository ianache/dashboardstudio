"""change llm and pickle_model to transform category

Revision ID: 038
Revises: 037
Create Date: 2026-05-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '038'
down_revision: Union[str, Sequence[str], None] = '036'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'

def upgrade() -> None:
    # Update categories to 'transform'
    op.execute(f"UPDATE {SCHEMA}.editor_tools SET category = 'transform' WHERE type IN ('llm', 'pickle_model')")

def downgrade() -> None:
    # Revert to 'source'
    op.execute(f"UPDATE {SCHEMA}.editor_tools SET category = 'source' WHERE type IN ('llm', 'pickle_model')")
