import os
import sys

# Add the backend directory to sys.path so we can import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import get_settings

def run_migration():
    settings = get_settings()
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        print("Adding flow_notes column to biportal.integration_flows table...")
        try:
            # Using text() for raw SQL and conn.execute()
            # PostgreSQL specific syntax for ADD COLUMN IF NOT EXISTS
            conn.execute(text("ALTER TABLE biportal.integration_flows ADD COLUMN IF NOT EXISTS flow_notes JSONB DEFAULT '[]' NOT NULL;"))
            conn.commit()
            print("Migration completed successfully.")
        except Exception as e:
            print(f"Error during migration: {e}")
            sys.exit(1)

if __name__ == "__main__":
    run_migration()
