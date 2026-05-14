"""add ai_assist_prompt to diagram_types

Revision ID: 009
Revises: 008
Create Date: 2026-04-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'biportal'

PROMPTS = {
    'data-integration': (
        "Eres un experto en ingeniería de datos e integración ETL/ELT.\n\n"
        "Se te proporcionará la definición completa de un diagrama de integración de datos en JSON, "
        "incluyendo los nodos (fuentes, transformaciones, destinos) y sus conexiones.\n\n"
        "Tu tarea es generar el código Python necesario para implementar este flujo de integración.\n\n"
        "Analiza cada nodo:\n"
        "- SOURCE: genera código de conexión y extracción (sqlalchemy, psycopg2, requests, pandas)\n"
        "- TRANSFORM: genera lógica de transformación (pandas, SQL)\n"
        "- DESTINATION: genera código de carga (sqlalchemy, connectors cloud)\n"
        "- NOTIFICATION: genera código de alerta (requests para webhook, smtplib para email)\n\n"
        "Responde ÚNICAMENTE con un bloque JSON válido con este formato EXACTO:\n"
        "{\n"
        '  "title": "nombre descriptivo del flujo implementado",\n'
        '  "description": "descripción breve de lo que hace el script",\n'
        '  "artifacts": [\n'
        "    {\n"
        '      "filename": "main.py",\n'
        '      "language": "python",\n'
        '      "description": "descripción del archivo",\n'
        '      "code": "código completo y funcional"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Genera código completo, funcional y listo para producción. "
        "No incluyas texto, explicaciones ni markdown fuera del bloque JSON. "
        "El JSON debe ser estrictamente válido (escapa caracteres especiales dentro de las cadenas)."
    ),
    'process-flow': (
        "Eres un experto en modelado de procesos de negocio (BPM) y arquitectura de software.\n\n"
        "Se te proporcionará la definición de un diagrama de proceso en JSON.\n\n"
        "Genera los siguientes activos:\n"
        "1. BPMN 2.0 XML del proceso\n"
        "2. Pseudocódigo/descripción técnica de cada paso\n"
        "3. Guía de implementación en markdown\n\n"
        "Responde ÚNICAMENTE con un bloque JSON válido con este formato EXACTO:\n"
        "{\n"
        '  "title": "nombre del proceso",\n'
        '  "description": "descripción del proceso de negocio",\n'
        '  "artifacts": [\n'
        "    {\n"
        '      "filename": "process.bpmn",\n'
        '      "language": "xml",\n'
        '      "description": "Definición BPMN 2.0 del proceso",\n'
        '      "code": "<?xml version=\'1.0\'..."\n'
        "    },\n"
        "    {\n"
        '      "filename": "implementation-guide.md",\n'
        '      "language": "markdown",\n'
        '      "description": "Guía de implementación técnica",\n'
        '      "code": "# Proceso..."\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "No incluyas texto fuera del bloque JSON. El JSON debe ser estrictamente válido."
    ),
    'data-quality': (
        "Eres un experto en calidad de datos, validación y gobierno de datos.\n\n"
        "Se te proporcionará la definición de un diagrama de calidad de datos en JSON, "
        "incluyendo las fuentes, reglas de validación y destinos de los resultados.\n\n"
        "Genera un script de validación completo usando pandas y/o Great Expectations.\n\n"
        "El script debe:\n"
        "1. Conectarse a cada fuente de datos definida\n"
        "2. Implementar cada regla de validación de los nodos transform/validator\n"
        "3. Generar un reporte de calidad\n"
        "4. Enviar alertas si hay nodos de notificación configurados\n\n"
        "Responde ÚNICAMENTE con un bloque JSON válido con este formato EXACTO:\n"
        "{\n"
        '  "title": "nombre del proceso de validación",\n'
        '  "description": "descripción de las reglas de calidad implementadas",\n'
        '  "artifacts": [\n'
        "    {\n"
        '      "filename": "data_quality.py",\n'
        '      "language": "python",\n'
        '      "description": "Script principal de validación",\n'
        '      "code": "código completo"\n'
        "    },\n"
        "    {\n"
        '      "filename": "quality_report.md",\n'
        '      "language": "markdown",\n'
        '      "description": "Plantilla del reporte de calidad",\n'
        '      "code": "# Reporte de Calidad..."\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "No incluyas texto fuera del bloque JSON. El JSON debe ser estrictamente válido."
    ),
}


def upgrade() -> None:
    op.add_column(
        'diagram_types',
        sa.Column('ai_assist_prompt', sa.Text(), nullable=True),
        schema=SCHEMA,
    )

    conn = op.get_bind()
    for dt_id, prompt in PROMPTS.items():
        conn.execute(
            text(f"UPDATE {SCHEMA}.diagram_types SET ai_assist_prompt = :p WHERE id = :id"),
            {"p": prompt, "id": dt_id},
        )


def downgrade() -> None:
    op.drop_column('diagram_types', 'ai_assist_prompt', schema=SCHEMA)
