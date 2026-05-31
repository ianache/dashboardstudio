"""revert llm to transform category

Revision ID: 343f76959aa0
Revises: fea5aebba9bd
Create Date: 2026-05-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '343f76959aa0'
down_revision: Union[str, Sequence[str], None] = 'fea5aebba9bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'

def upgrade() -> None:
    # Revert LLM tool to 'transform' category
    op.execute(f"UPDATE {SCHEMA}.editor_tools SET category = 'transform' WHERE type = 'llm'")

def downgrade() -> None:
    # Back to 'source'
    op.execute(f"UPDATE {SCHEMA}.editor_tools SET category = 'source' WHERE type = 'llm'")
