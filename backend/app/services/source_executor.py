from sqlalchemy import create_engine, text
from app.core.encryption import process_sensitive_fields
from app.models.models import DataSource
from app.core.database import SessionLocal

def get_db_engine(data_source: DataSource):
    config = process_sensitive_fields(data_source.connection_config, action="decrypt")
    
    # Generic connection string builder based on type
    # Supports: postgresql, mysql, mssql, sqlite
    if config['type'] == 'database':
        # Connection string format: dialect+driver://username:password@host:port/database
        # Assuming postgresql for now if not specified, but flexible
        url = f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        return create_engine(url)
    
    raise ValueError(f"Unsupported DB type: {config['type']}")

def execute_sql(connection_id: str, query: str):
    db = SessionLocal()
    try:
        ds = db.query(DataSource).filter(DataSource.id == connection_id).first()
        if not ds:
            raise ValueError("Connection not found")
            
        engine = get_db_engine(ds)
        with engine.connect() as conn:
            result = conn.execute(text(query))
            if result.returns_rows:
                return [dict(row._mapping) for row in result]
            conn.commit()
            return {"status": "success"}
    finally:
        db.close()
