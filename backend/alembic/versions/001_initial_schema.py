"""initial schema

Revision ID: 001
Revises: 
Create Date: 2025-04-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE SCHEMA IF NOT EXISTS biportal')

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names(schema='biportal')

    if 'users' not in existing_tables:
        op.create_table('users',
            sa.Column('id', sa.String(50), primary_key=True),
            sa.Column('email', sa.String(255), nullable=True),
            sa.Column('username', sa.String(100), nullable=True),
            sa.Column('full_name', sa.String(255), nullable=True),
            sa.Column('first_name', sa.String(100), nullable=True),
            sa.Column('last_name', sa.String(100), nullable=True),
            sa.Column('role', sa.String(20), nullable=False, server_default='viewer'),
            sa.Column('avatar', sa.String(10), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            schema='biportal'
        )

    if 'dashboards' not in existing_tables:
        op.create_table('dashboards',
            sa.Column('id', sa.String(50), primary_key=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_by', sa.String(50), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('filters', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['biportal.users.id']),
            schema='biportal'
        )

    if 'dashboard_assignments' not in existing_tables:
        op.create_table('dashboard_assignments',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('dashboard_id', sa.String(50), nullable=False),
            sa.Column('user_id', sa.String(50), nullable=False),
            sa.ForeignKeyConstraint(['dashboard_id'], ['biportal.dashboards.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['biportal.users.id'], ondelete='CASCADE'),
            schema='biportal'
        )

    if 'widgets' not in existing_tables:
        op.create_table('widgets',
            sa.Column('id', sa.String(50), primary_key=True),
            sa.Column('dashboard_id', sa.String(50), nullable=False),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('chart_type', sa.String(50), nullable=False, server_default='bar'),
            sa.Column('position_x', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('position_y', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('position_w', sa.Integer(), nullable=False, server_default='6'),
            sa.Column('position_h', sa.Integer(), nullable=False, server_default='3'),
            sa.Column('cube_query', sa.JSON(), nullable=True),
            sa.Column('chart_options', sa.JSON(), nullable=True),
            sa.Column('use_mock_data', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['dashboard_id'], ['biportal.dashboards.id'], ondelete='CASCADE'),
            schema='biportal'
        )

    if 'color_palettes' not in existing_tables:
        op.create_table('color_palettes',
            sa.Column('id', sa.String(50), primary_key=True),
            sa.Column('label', sa.String(100), nullable=False),
            sa.Column('colors', sa.JSON(), nullable=True),
            sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_by', sa.String(50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            schema='biportal'
        )

    if 'data_types' not in existing_tables:
        op.create_table('data_types',
            sa.Column('id', sa.String(50), primary_key=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('base_type', sa.String(50), nullable=False),
            sa.Column('size', sa.Integer(), nullable=True),
            sa.Column('precision', sa.Integer(), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_builtin', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            schema='biportal'
        )

    if 'dimensional_models' not in existing_tables:
        op.create_table('dimensional_models',
            sa.Column('id', sa.String(50), primary_key=True),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_global', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_by', sa.String(50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('nodes', sa.JSON(), nullable=True),
            sa.Column('relationships', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['biportal.users.id']),
            schema='biportal'
        )

    if 'cube_config' not in existing_tables:
        op.create_table('cube_config',
            sa.Column('id', sa.String(50), primary_key=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('api_url', sa.String(500), nullable=False),
            sa.Column('api_token', sa.String(500), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_by', sa.String(50), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['created_by'], ['biportal.users.id']),
            schema='biportal'
        )


def downgrade() -> None:
    op.drop_table('cube_config', schema='biportal')
    op.drop_table('dimensional_models', schema='biportal')
    op.drop_table('data_types', schema='biportal')
    op.drop_table('color_palettes', schema='biportal')
    op.drop_table('widgets', schema='biportal')
    op.drop_table('dashboard_assignments', schema='biportal')
    op.drop_table('dashboards', schema='biportal')
    op.drop_table('users', schema='biportal')
    op.execute('DROP SCHEMA IF EXISTS biportal CASCADE')