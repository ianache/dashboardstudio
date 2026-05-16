"""
Patch tool catalog:
  1. Update rest_api tool -> pure HTTP REST (remove graphql fields from prop_defs)
  2. Create graphql tool -> dedicated GraphQL node with query editor

Run: uv run python patch_add_graphql_tool.py
"""
import sys, os, json, random, string
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.models import models

def gen_id():
    return "tool-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=9))

def patch():
    db = SessionLocal()
    try:
        # ── 1. Clean up rest_api: remove graphql fields, keep pure HTTP ──────────
        rest = db.query(models.EditorTool).filter(models.EditorTool.id == 'tool-rest-api').first()
        if rest:
            rest.prop_defs = {
                "url":      {"label": "URL",             "type": "text",     "placeholder": "https://api.example.com/data"},
                "method":   {"label": "Metodo HTTP",     "type": "select",   "options": [
                                {"value": "GET",    "label": "GET"},
                                {"value": "POST",   "label": "POST"},
                                {"value": "PUT",    "label": "PUT"},
                                {"value": "PATCH",  "label": "PATCH"},
                                {"value": "DELETE", "label": "DELETE"},
                ]},
                "auth_type": {"label": "Autenticacion", "type": "select", "options": [
                                {"value": "none",    "label": "Ninguna"},
                                {"value": "bearer",  "label": "Bearer Token"},
                                {"value": "basic",   "label": "Basic Auth"},
                                {"value": "api_key", "label": "API Key (header)"},
                ]},
                "api_key":   {"label": "Token / API Key", "type": "password", "placeholder": "sk-..."},
                "headers":   {"label": "Headers (JSON)",  "type": "textarea", "placeholder": '{"X-Custom": "value"}', "rows": 3},
                "body":      {"label": "Body (JSON)",     "type": "textarea", "placeholder": '{"key": "value"}',     "rows": 4,
                              "help": "Cuerpo para POST/PUT. Si se omite, se usa el payload del nodo anterior."},
            }
            rest.default_props = {
                "url": "", "method": "GET", "auth_type": "none",
                "api_key": "", "headers": "", "body": "",
            }
            rest.name = "HTTP REST"
            rest.description = "Consume un endpoint HTTP/REST (GET, POST, PUT, PATCH, DELETE)"
            rest.subtitle = "Peticion HTTP/REST"
            print("OK: tool-rest-api actualizado (HTTP REST puro).")

        # ── 2. Create/update graphql tool ─────────────────────────────────────────
        gql = db.query(models.EditorTool).filter(models.EditorTool.type == 'graphql').first()
        if not gql:
            gql = models.EditorTool(id=gen_id())
            db.add(gql)

        gql.type        = "graphql"
        gql.name        = "GraphQL"
        gql.description = "Ejecuta una query o mutation GraphQL contra cualquier endpoint"
        gql.subtitle    = "Query / Mutation GraphQL"
        gql.icon        = "hub"
        gql.category    = "source"
        gql.applicable_diagram_types = ["data-integration"]
        gql.prop_defs   = {
            "url": {"label": "URL del Endpoint", "type": "text", "placeholder": "https://api.example.com/graphql"},
            "auth_type": {"label": "Autenticacion", "type": "select", "options": [
                {"value": "none",   "label": "Ninguna"},
                {"value": "bearer", "label": "Bearer Token"},
                {"value": "basic",  "label": "Basic Auth"},
            ]},
            "api_key":            {"label": "Bearer Token",            "type": "password", "placeholder": "eyJ..."},
            "headers":            {"label": "Headers extra (JSON)",    "type": "textarea", "placeholder": '{"X-App": "studio"}', "rows": 2},
            "graphql_query":      {"label": "Query / Mutation",        "type": "textarea", "rows": 10,
                                   "placeholder": "query {\n  currentUser {\n    name\n    email\n  }\n}",
                                   "help": "Escribe tu query o mutation GraphQL aqui. El endpoint siempre se llama con POST y Content-Type: application/json."},
            "graphql_variables":  {"label": "Variables (JSON)",        "type": "textarea", "rows": 3,
                                   "placeholder": '{"userId": 1}',
                                   "help": "Variables opcionales para la operacion GraphQL"},
        }
        gql.default_props = {
            "url": "", "auth_type": "none", "api_key": "",
            "headers": "", "graphql_query": "", "graphql_variables": "",
        }

        db.commit()
        print("OK: tool-graphql creado/actualizado (id=" + gql.id + ").")

    finally:
        db.close()

if __name__ == '__main__':
    patch()
