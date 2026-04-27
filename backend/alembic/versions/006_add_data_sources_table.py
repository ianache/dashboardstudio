"""add data_sources table

Revision ID: 006
Revises: 005
Create Date: 2026-04-26

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime


revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create data_sources table
    op.create_table(
        'data_sources',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('connection_url', sa.String(500), nullable=False),
        sa.Column('username', sa.String(100), nullable=True),
        sa.Column('password', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', sa.String(50), sa.ForeignKey('biportal.users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        schema='biportal'
    )
    
    # Create index on name for faster lookups
    op.create_index(
        'idx_data_sources_name',
        'data_sources',
        ['name'],
        unique=False,
        schema='biportal'
    )
    
    # Insert default data sources
    op.bulk_insert(
        sa.table(
            'data_sources',
            sa.column('id', sa.String(50)),
            sa.column('name', sa.String(100)),
            sa.column('type', sa.String(50)),
            sa.column('connection_url', sa.String(500)),
            sa.column('username', sa.String(100)),
            sa.column('password', sa.String(500)),
            sa.column('description', sa.Text()),
            sa.column('is_active', sa.Boolean()),
            sa.column('created_by', sa.String(50)),
            sa.column('created_at', sa.DateTime()),
            sa.column('updated_at', sa.DateTime()),
            schema='biportal'
        ),
        [
            {
                'id': 'ds-qdrant-demo',
                'name': 'QDrant Vector DB',
                'type': 'qdrant',
                'connection_url': 'http://localhost:6333',
                'username': None,
                'password': None,
                'description': 'Vector database for semantic search and embeddings',
                'is_active': True,
                'created_by': None,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            },
            {
                'id': 'ds-neo4j-demo',
                'name': 'Neo4j Graph DB',
                'type': 'neo4j',
                'connection_url': 'bolt://localhost:7687',
                'username': 'neo4j',
                'password': 'password123',
                'description': 'Graph database for relationship analytics',
                'is_active': True,
                'created_by': None,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        ]
    )


def downgrade() -> None:
    op.drop_index('idx_data_sources_name', table_name='data_sources', schema='biportal')
    op.drop_table('data_sources', schema='biportal')
