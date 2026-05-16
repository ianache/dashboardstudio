"""
Patch the rest_api editor tool to add graphql_query and graphql_variables fields.
Run once with: uv run python patch_rest_api_tool.py
"""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models import models

def patch():
    db = SessionLocal()
    try:
        tool = db.query(models.EditorTool).filter(models.EditorTool.id == 'tool-rest-api').first()
        if not tool:
            print("ERROR: tool-rest-api not found in DB")
            return

        current_props = tool.prop_defs or {}
        current_defaults = tool.default_props or {}

        # Add GraphQL fields if not already present
        if 'graphql_query' not in current_props:
            current_props['graphql_query'] = {
                'label': 'Query GraphQL',
                'type': 'textarea',
                'placeholder': '{ currentUser { name email } }',
                'rows': 6,
                'help': 'Si se especifica, el método se forzará a POST y el cuerpo será {"query": "..."}'
            }
            current_defaults['graphql_query'] = ''

        if 'graphql_variables' not in current_props:
            current_props['graphql_variables'] = {
                'label': 'Variables GraphQL (JSON)',
                'type': 'textarea',
                'placeholder': '{"userId": 1}',
                'rows': 3,
                'help': 'Variables opcionales para la query GraphQL'
            }
            current_defaults['graphql_variables'] = ''

        if 'body' not in current_props:
            current_props['body'] = {
                'label': 'Body (JSON string)',
                'type': 'textarea',
                'placeholder': '{"key": "value"}',
                'rows': 4,
                'help': 'Cuerpo de la petición para POST/PUT (ignora el payload previo si se especifica)'
            }
            current_defaults['body'] = ''

        tool.prop_defs = current_props
        tool.default_props = current_defaults
        db.commit()
        print("OK: tool-rest-api actualizado correctamente.")
        print("   Campos: " + str(list(current_props.keys())))
    finally:
        db.close()

if __name__ == '__main__':
    patch()
