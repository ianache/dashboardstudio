import httpx
import jwt
import time
import logging
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Module-level variable set per request by main.py
_active_filters: list | None = None


async def query_data(query: dict):
    """
    Fetches business data from CubeJS using the provided JSON query format.
    
    Use this tool to explore data beyond the current screen context or to get
    detailed metrics and dimensions from the database.
    
    Example queries:
    - Total orders: {"measures": ["Orders.count"]}
    - Orders by status: {"measures": ["Orders.count"], "dimensions": ["Orders.status"]}
    - Sales by month: {"measures": ["Orders.total_amount"], "dimensions": ["Orders.createdAt.month"]}
    
    Args:
        query (dict): A valid CubeJS JSON query object.
        
    Returns:
        list: The 'data' array from CubeJS response.
    """
    # Merge active dashboard filters into the query
    if _active_filters:
        existing = query.get("filters", [])
        query = {**query, "filters": existing + _active_filters}

    payload = {
        "sub": "ai-analyst",
        "iat": int(time.time()),
        "exp": int(time.time()) + (1 * 60 * 60)  # 1 hour
    }
    
    token = jwt.encode(payload, settings.cubejs_api_secret, algorithm="HS256")
    
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Querying CubeJS at {settings.cubejs_url} with query: {query}")
            response = await client.post(
                settings.cubejs_url,
                json={"query": query},
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                logger.error(f"CubeJS error in response: {result['error']}")
                return f"CubeJS error: {result['error']}"
                
            return result.get("data", [])
            
        except httpx.HTTPStatusError as e:
            logger.error(f"CubeJS HTTP error: {e.response.status_code} - {e.response.text}")
            return f"Error querying data: {e.response.text}"
        except Exception as e:
            logger.error(f"CubeJS unexpected error: {str(e)}")
            return f"Error querying data: {str(e)}"
