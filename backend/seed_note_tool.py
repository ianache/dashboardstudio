
import sys
import os
from sqlalchemy.orm import Session

# Add the current directory to sys.path to import app
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
from app.models import models

def seed_note_tool():
    print("Registering 'Note' tool...")
    db = SessionLocal()
    try:
        # Check if already exists
        existing = db.query(models.EditorTool).filter(models.EditorTool.type == 'note').first()
        
        tool_data = {
            'id': 'tool-note',
            'type': 'note',
            'name': 'Note',
            'subtitle': 'Markdown Sticky Note',
            'icon': 'sticky_note_2',
            'category': 'Annotations',
            'applicable_diagram_types': ['data-integration', 'process-flow', 'data-quality'],
            'prop_defs': {
                'content': { 'label': 'Contenido', 'type': 'textarea', 'placeholder': '# Título\nContenido aquí...' },
                'color': { 'label': 'Color', 'type': 'select', 'options': [
                    { 'value': '#fef9c3', 'label': 'Amarillo' },
                    { 'value': '#dbeafe', 'label': 'Azul' },
                    { 'value': '#dcfce7', 'label': 'Verde' },
                    { 'value': '#fce7f3', 'label': 'Rosa' },
                    { 'value': '#f1f5f9', 'label': 'Gris' }
                ]}
            },
            'default_props': { 'content': '# Nueva Nota', 'color': '#fef9c3' }
        }

        if existing:
            print(f"Tool 'note' already exists. Updating...")
            for key, value in tool_data.items():
                setattr(existing, key, value)
        else:
            print(f"Creating new 'note' tool...")
            new_tool = models.EditorTool(**tool_data)
            db.add(new_tool)
        
        db.commit()
        print("Success: Note tool registered.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_note_tool()
