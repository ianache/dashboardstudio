import smtplib
import httpx
import asyncpg
from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseConnectionStrategy(ABC):
    @abstractmethod
    async def test(self, config: Dict[str, Any]) -> bool:
        pass

class SmtpStrategy(BaseConnectionStrategy):
    async def test(self, config: Dict[str, Any]) -> bool:
        try:
            # We use a context manager to ensure connection is closed
            # SMTP test usually involves just connecting and login
            with smtplib.SMTP(config['host'], config['port'], timeout=10) as server:
                if config.get('use_ssl'):
                    server.starttls()
                server.login(config['email'], config['password'])
            return True
        except Exception as e:
            print(f"SMTP Test Error: {e}")
            return False

class DbStrategy(BaseConnectionStrategy):
    async def test(self, config: Dict[str, Any]) -> bool:
        try:
            conn = await asyncpg.connect(
                user=config['username'],
                password=config['password'],
                database=config['database'],
                host=config['host'],
                port=config['port'],
                timeout=10
            )
            await conn.close()
            return True
        except Exception as e:
            print(f"DB Test Error: {e}")
            return False

class HttpStrategy(BaseConnectionStrategy):
    async def test(self, config: Dict[str, Any]) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                auth = None
                if config.get('username') and config.get('password'):
                    auth = (config['username'], config['password'])
                
                response = await client.get(config['url'], auth=auth)
                return response.status_code < 400
        except Exception as e:
            print(f"HTTP Test Error: {e}")
            return False

class ConnectionTestingService:
    def __init__(self):
        self.strategies = {
            'smtp': SmtpStrategy(),
            'database': DbStrategy(),
            'http': HttpStrategy()
        }

    async def test_connection(self, config: Dict[str, Any]) -> bool:
        strategy = self.strategies.get(config.get('type'))
        if not strategy:
            raise ValueError(f"No test strategy for {config.get('type')}")
        return await strategy.test(config)

connection_testing_service = ConnectionTestingService()
