"""fix pickle_model prop_defs: endpoint -> fetch_endpoint

Revision ID: 039
Revises: 038
Create Date: 2026-06-01

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import json

revision: str = '039'
down_revision: Union[str, Sequence[str], None] = '038'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'

CORRECT_PROP_DEFS = {
    "model_id": {
        "label": "ML Model",
        "type": "dynamic_select",
        "placeholder": "Seleccionar modelo...",
        "fetch_endpoint": "/api/v1/ml-models/",
        "value_field": "id",
        "label_field": "name"
    }
}

ORIGINAL_PROP_DEFS = {
    "model_id": {
        "label": "ML Model",
        "type": "dynamic_select",
        "endpoint": "/api/v1/ml-models"
    }
}


def upgrade() -> None:
    op.execute(
        f"UPDATE {SCHEMA}.editor_tools "
        f"SET prop_defs = '{json.dumps(CORRECT_PROP_DEFS)}' "
        f"WHERE type = 'pickle_model'"
    )


def downgrade() -> None:
    op.execute(
        f"UPDATE {SCHEMA}.editor_tools "
        f"SET prop_defs = '{json.dumps(ORIGINAL_PROP_DEFS)}' "
        f"WHERE type = 'pickle_model'"
    )
