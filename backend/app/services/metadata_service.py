from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import asyncpg
import logging

logger = logging.getLogger(__name__)

class BaseMetadataStrategy(ABC):
    @abstractmethod
    async def get_tables(self, config: Dict[str, Any], schema: str = "public") -> List[str]:
        pass

    @abstractmethod
    async def get_columns(self, config: Dict[str, Any], schema: str, table: str) -> List[Dict[str, str]]:
        pass

class PostgresMetadataStrategy(BaseMetadataStrategy):
    async def get_tables(self, config: Dict[str, Any], schema: str = "public") -> List[str]:
        """
        Fetch table names from a PostgreSQL database.
        """
        try:
            # Note: config uses 'username' instead of 'user' in some project parts
            user = config.get('username') or config.get('user')
            port = config.get('port', 5432)
            if isinstance(port, str) and port.isdigit():
                port = int(port)

            conn = await asyncpg.connect(
                user=user,
                password=config.get('password'),
                database=config.get('database'),
                host=config.get('host'),
                port=port,
                timeout=10
            )
            try:
                # SQL as specified in the plan
                query = "SELECT table_name FROM information_schema.tables WHERE table_schema = $1 AND table_type = 'BASE TABLE' ORDER BY table_name"
                rows = await conn.fetch(query, schema)
                return [row['table_name'] for row in rows]
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"PostgresMetadataStrategy.get_tables error: {e}")
            raise

    async def get_columns(self, config: Dict[str, Any], schema: str, table: str) -> List[Dict[str, str]]:
        """
        Fetch column names and types from a PostgreSQL table.
        """
        try:
            user = config.get('username') or config.get('user')
            port = config.get('port', 5432)
            if isinstance(port, str) and port.isdigit():
                port = int(port)

            conn = await asyncpg.connect(
                user=user,
                password=config.get('password'),
                database=config.get('database'),
                host=config.get('host'),
                port=port,
                timeout=10
            )
            try:
                # SQL as specified in the plan
                query = "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = $1 AND table_schema = $2 ORDER BY ordinal_position"
                rows = await conn.fetch(query, table, schema)
                return [{"name": row['column_name'], "type": row['data_type']} for row in rows]
            finally:
                await conn.close()
        except Exception as e:
            logger.error(f"PostgresMetadataStrategy.get_columns error: {e}")
            raise

class MetadataService:
    def __init__(self):
        self.strategies = {
            'postgresql': PostgresMetadataStrategy(),
            'postgres': PostgresMetadataStrategy(),
        }

    async def get_tables(self, config: Dict[str, Any], schema: str = "public") -> List[str]:
        strategy = self._get_strategy(config)
        return await strategy.get_tables(config, schema)

    async def get_columns(self, config: Dict[str, Any], schema: str, table: str) -> List[Dict[str, str]]:
        strategy = self._get_strategy(config)
        return await strategy.get_columns(config, schema, table)

    def _get_strategy(self, config: Dict[str, Any]) -> BaseMetadataStrategy:
        conn_type = config.get('type', '').lower()
        strategy = self.strategies.get(conn_type)
        if not strategy:
            # Fallback for generic 'database' type if it's actually postgres
            # In some parts of the code, 'type' might be 'database' and engine is elsewhere
            # But the plan specifies handling 'postgresql' and 'postgres'.
            raise ValueError(f"No metadata strategy for type '{conn_type}'. Supported: {list(self.strategies.keys())}")
        return strategy

metadata_service = MetadataService()
