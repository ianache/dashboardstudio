# Let's bypass the inspector completely and just check directly using sqlalchemy or psycopg2

import psycopg2
from sqlalchemy import create_engine, text
import subprocess
import sys
import os

os.chdir("D:\\01-CROSSNET\\01-PROJECTS\\dashboardstudio\\backend")
sys.path.insert(0, "D:\\01-CROSSNET\\01-PROJECTS\\dashboardstudio\\backend")

from app.core.config import get_settings
settings = get_settings()

# Clean up any existing
print("=== Full cleanup ===")
conn = psycopg2.connect(host="192.168.1.43", port=5432, database="biportal", user="biportal", password="biportal_password")
conn.autocommit = True
c = conn.cursor()
c.execute("DROP SCHEMA IF EXISTS biportal CASCADE")
conn.commit()
print("Schema dropped")

# Now run alembic 
print("\n=== Running alembic (fresh start) ===")
result = subprocess.run(
    [sys.executable, "-m", "alembic", "upgrade", "head"],
    capture_output=True,
    text=True,
    cwd="D:\\01-CROSSNET\\01-PROJECTS\\dashboardstudio\\backend"
)
print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)

# Check ALLL relations
print("\n=== After fresh alembic run ===")
c.execute("""
    SELECT n.nspname, c.relname, c.relkind
    FROM pg_catalog.pg_class c
    JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
    WHERE n.nspname IN ('biportal', 'public')
    AND c.relkind IN ('r', 'v', 'm')
""")
print(f"All relations: {c.fetchall()}")

# Check schema
c.execute("SELECT nspname FROM pg_catalog.pg_namespace WHERE nspname = 'biportal'")
print(f"biportal schema: {c.fetchone()}")

c.close()
conn.close()