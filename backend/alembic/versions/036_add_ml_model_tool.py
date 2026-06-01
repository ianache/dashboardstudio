"""add ml_models table and pickle_model tool

Revision ID: 036
Revises: 035
Create Date: 2026-05-31

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
import json

revision: str = '036'
down_revision: Union[str, Sequence[str], None] = '035'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'

def upgrade() -> None:
    # 1. Create machine_learning_models table
    op.create_table(
        'machine_learning_models',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('sklearn_version', sa.String(50), nullable=True),
        sa.Column('features', sa.JSON, nullable=True),
        sa.Column('created_by', sa.String(50), sa.ForeignKey(f"{SCHEMA}.users.id"), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        schema=SCHEMA
    )

    # 2. Register pickle_model tool
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
        "model_id": {
            "label": "ML Model",
            "type": "dynamic_select",
            "placeholder": "Seleccionar modelo...",
            "fetch_endpoint": "/api/v1/ml-models/",
            "value_field": "id",
            "label_field": "name"
        }
    }

    default_props = {}

    applicable_types = ['data-integration', 'process-flow']

    # Delete existing if present (idempotent)
    op.execute(
        tools_table.delete().where(tools_table.c.type == 'pickle_model')
    )

    # Insert new tool
    op.execute(
        tools_table.insert().values(
            id='tool-ml-pickle-001',
            type='pickle_model',
            category='source',  # Category is source because it's pre-executed
            name='Pickle Model Inference',
            description='Runs scikit-learn model prediction securely from the backend',
            icon='psychology',
            prop_defs=prop_defs,
            default_props=default_props,
            applicable_diagram_types=applicable_types
        )
    )

def downgrade() -> None:
    op.execute(f"DELETE FROM {SCHEMA}.editor_tools WHERE type = 'pickle_model'")
    op.drop_table('machine_learning_models', schema=SCHEMA)
