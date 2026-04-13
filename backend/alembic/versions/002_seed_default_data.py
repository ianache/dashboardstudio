"""seed default data

Revision ID: 002
Revises: 001
Create Date: 2025-04-07

"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Insert default data types (matching frontend DEFAULT_TYPES)
    data_types_table = sa.table(
        'data_types',
        sa.column('id', sa.String(50)),
        sa.column('name', sa.String(100)),
        sa.column('base_type', sa.String(50)),
        sa.column('size', sa.Integer),
        sa.column('precision', sa.Integer),
        sa.column('description', sa.Text),
        sa.column('is_builtin', sa.Boolean),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
        schema='biportal'
    )
    
    default_data_types = [
        {
            'id': 'dt-serial',
            'name': 'Serial',
            'base_type': 'SERIAL',
            'size': None,
            'precision': None,
            'description': 'Auto-incrementing integer primary key',
            'is_builtin': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'dt-int',
            'name': 'Entero',
            'base_type': 'INTEGER',
            'size': None,
            'precision': None,
            'description': 'Standard integer type',
            'is_builtin': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'dt-bigint',
            'name': 'Entero grande',
            'base_type': 'BIGINT',
            'size': None,
            'precision': None,
            'description': 'Large integer for big numbers',
            'is_builtin': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'dt-numeric',
            'name': 'Decimal',
            'base_type': 'NUMERIC',
            'size': 18,
            'precision': 4,
            'description': 'Decimal number with precision',
            'is_builtin': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'dt-money',
            'name': 'Moneda',
            'base_type': 'NUMERIC',
            'size': 18,
            'precision': 2,
            'description': 'Currency/monetary values',
            'is_builtin': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'dt-pct',
            'name': 'Porcentaje',
            'base_type': 'NUMERIC',
            'size': 5,
            'precision': 2,
            'description': 'Percentage values (0-100)',
            'is_builtin': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'dt-varchar',
            'name': 'Texto',
            'base_type': 'VARCHAR',
            'size': 255,
            'precision': None,
            'description': 'Variable length text up to 255 characters',
            'is_builtin': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'dt-text',
            'name': 'Texto largo',
            'base_type': 'TEXT',
            'size': None,
            'precision': None,
            'description': 'Unlimited length text',
            'is_builtin': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'dt-bool',
            'name': 'Booleano',
            'base_type': 'BOOLEAN',
            'size': None,
            'precision': None,
            'description': 'True/False boolean value',
            'is_builtin': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'dt-date',
            'name': 'Fecha',
            'base_type': 'DATE',
            'size': None,
            'precision': None,
            'description': 'Calendar date without time',
            'is_builtin': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'dt-ts',
            'name': 'Timestamp',
            'base_type': 'TIMESTAMP',
            'size': None,
            'precision': None,
            'description': 'Date and time without timezone',
            'is_builtin': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'dt-tstz',
            'name': 'Timestamp TZ',
            'base_type': 'TIMESTAMPTZ',
            'size': None,
            'precision': None,
            'description': 'Date and time with timezone',
            'is_builtin': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'dt-uuid',
            'name': 'UUID',
            'base_type': 'UUID',
            'size': None,
            'precision': None,
            'description': 'Universally unique identifier',
            'is_builtin': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'dt-jsonb',
            'name': 'JSONB',
            'base_type': 'JSONB',
            'size': None,
            'precision': None,
            'description': 'Binary JSON data with indexing support',
            'is_builtin': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    op.bulk_insert(data_types_table, default_data_types)
    
    # Insert default color palettes (matching frontend built-in palettes)
    color_palettes_table = sa.table(
        'color_palettes',
        sa.column('id', sa.String(50)),
        sa.column('label', sa.String(100)),
        sa.column('colors', sa.JSON),
        sa.column('is_default', sa.Boolean),
        sa.column('created_by', sa.String(50)),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
        schema='biportal'
    )
    
    default_palettes = [
        {
            'id': 'default',
            'label': 'Predeterminada',
            'colors': [
                '#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de',
                '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#2f4554'
            ],
            'is_default': True,
            'created_by': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'ocean',
            'label': 'Océano',
            'colors': [
                '#006994', '#0096c7', '#48cae4', '#90e0ef', '#ade8f4',
                '#0077b6', '#023e8a', '#03045e', '#caf0f8', '#00b4d8'
            ],
            'is_default': False,
            'created_by': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'sunset',
            'label': 'Atardecer',
            'colors': [
                '#ff6b35', '#f7931e', '#ffd23f', '#ee4266', '#540d6e',
                '#f7b801', '#f18701', '#d95d39', '#c73e1d', '#2e1a47'
            ],
            'is_default': False,
            'created_by': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'forest',
            'label': 'Bosque',
            'colors': [
                '#2d6a4f', '#40916c', '#52b788', '#74c69d', '#95d5b2',
                '#1b4332', '#081c15', '#b7e4c7', '#d8f3dc', '#40916c'
            ],
            'is_default': False,
            'created_by': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'pastel',
            'label': 'Pastel',
            'colors': [
                '#ffb3ba', '#ffdfba', '#ffffba', '#baffc9', '#bae1ff',
                '#eecbff', '#ffccf9', '#c4faf8', '#fdc5f5', '#85e3ff'
            ],
            'is_default': False,
            'created_by': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'vivid',
            'label': 'Vívida',
            'colors': [
                '#ff006e', '#fb5607', '#ffbe0b', '#8338ec', '#3a86ff',
                '#06ffa5', '#ff4365', '#00d9ff', '#bd00ff', '#ff9f1c'
            ],
            'is_default': False,
            'created_by': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'earth',
            'label': 'Tierra',
            'colors': [
                '#8b4513', '#d2691e', '#cd853f', '#deb887', '#f4a460',
                '#a0522d', '#bc8f8f', '#f5deb3', '#daa520', '#8b7355'
            ],
            'is_default': False,
            'created_by': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        },
        {
            'id': 'mono',
            'label': 'Monocromática',
            'colors': [
                '#1a1a2e', '#16213e', '#0f3460', '#533483', '#e94560',
                '#162447', '#1f4068', '#1b1b2f', '#4f3b78', '#9d65c9'
            ],
            'is_default': False,
            'created_by': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
    ]
    
    op.bulk_insert(color_palettes_table, default_palettes)
    
    # Insert global dimensional model (system-wide)
    dimensional_models_table = sa.table(
        'dimensional_models',
        sa.column('id', sa.String(50)),
        sa.column('name', sa.String(255)),
        sa.column('description', sa.Text),
        sa.column('is_global', sa.Boolean),
        sa.column('created_by', sa.String(50)),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
        sa.column('nodes', sa.JSON),
        sa.column('relationships', sa.JSON),
        schema='biportal'
    )
    
    global_model = {
        'id': 'global',
        'name': 'Global',
        'description': 'Dimensiones compartidas entre todos los modelos dimensionales',
        'is_global': True,
        'created_by': None,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'nodes': [],
        'relationships': []
    }
    
    op.bulk_insert(dimensional_models_table, [global_model])


def downgrade() -> None:
    # Remove seeded data
    op.execute("DELETE FROM biportal.dimensional_models WHERE id = 'global'")
    op.execute("DELETE FROM biportal.color_palettes WHERE id IN ('default', 'ocean', 'sunset', 'forest', 'pastel', 'vivid', 'earth', 'mono')")
    op.execute("DELETE FROM biportal.data_types WHERE is_builtin = true")
