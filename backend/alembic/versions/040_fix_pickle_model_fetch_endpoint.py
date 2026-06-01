"""fix pickle_model prop_defs fetch_endpoint (migration 039 was on divergent branch)

Revision ID: 040
Revises: e80cba68c966
Create Date: 2026-05-31

"""
from typing import Sequence, Union
from alembic import op
import json

revision: str = '040'
down_revision: Union[str, Sequence[str], None] = 'e80cba68c966'
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
