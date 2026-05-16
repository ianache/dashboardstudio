import smtplib
import httpx
import asyncpg
from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple

class BaseConnectionStrategy(ABC):
    @abstractmethod
    async def test(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        pass

class SmtpStrategy(BaseConnectionStrategy):
    async def test(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        try:
            with smtplib.SMTP(config['host'], config['port'], timeout=10) as server:
                if config.get('use_ssl'):
                    server.starttls()
                server.login(config['email'], config['password'])
            return True, "Conexión exitosa"
        except Exception as e:
            print(f"SMTP Test Error: {e}")
            return False, f"Error SMTP: {str(e)}"

class DbStrategy(BaseConnectionStrategy):
    async def test(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        try:
            conn = await asyncpg.connect(
                user=config.get('username'),
                password=config.get('password'),
                database=config.get('database'),
                host=config.get('host'),
                port=int(config.get('port', 5432)),
                timeout=10
            )
            await conn.close()
            return True, "Conexión a BD exitosa"
        except Exception as e:
            print(f"DB Test Error: {e}")
            return False, f"Error de Base de Datos: {str(e)}"

class HttpStrategy(BaseConnectionStrategy):
    async def test(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                auth = None
                if config.get('username') and config.get('password'):
                    auth = (config['username'], config['password'])
                
                response = await client.get(config.get('url', ''), auth=auth)
                if response.status_code < 400:
                    return True, f"HTTP {response.status_code} OK"
                else:
                    return False, f"HTTP Status {response.status_code}"
        except Exception as e:
            print(f"HTTP Test Error: {e}")
            return False, f"Error de red: {str(e)}"

class ConnectionTestingService:
    def __init__(self):
        self.strategies = {
            # Generic keys
            'smtp':       SmtpStrategy(),
            'database':   DbStrategy(),
            'http':       HttpStrategy(),
            'jwt':        HttpStrategy(),
            'rest_api':   HttpStrategy(),
            # Specific DB engines
            'postgresql': DbStrategy(),
            'postgres':   DbStrategy(),
            'mysql':      DbStrategy(),
            'mariadb':    DbStrategy(),
            'mssql':      DbStrategy(),
            'sqlserver':  DbStrategy(),
            'oracle':     DbStrategy(),
        }

    async def test_connection(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        conn_type = config.get('type')
        strategy = self.strategies.get(conn_type)
        if not strategy:
            raise ValueError(f"No test strategy for type '{conn_type}'. Supported: {list(self.strategies.keys())}")
        return await strategy.test(config)

connection_testing_service = ConnectionTestingService()
