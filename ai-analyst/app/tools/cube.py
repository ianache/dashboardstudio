import httpx
import jwt
import time
import logging
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Module-level variable set per request by main.py
_active_filters: list | None = None


async def query_data(
    query: dict | None = None,
    measures: list | str | None = None,
    dimensions: list | str | None = None,
    timeDimensions: list | dict | None = None,
    filters: list | dict | None = None,
    limit: int | str | None = None,
    offset: int | str | None = None,
    order: dict | list | str | None = None,
):
    """
    Fetches business data from CubeJS using the provided JSON query format.
    
    Use this tool to explore data beyond the current screen context or to get
    detailed metrics and dimensions from the database.
    
    You can either pass the entire query object in the 'query' argument, OR
    pass the individual query properties (measures, dimensions, filters, etc.)
    directly as top-level arguments.
    
    Example queries (as direct arguments):
    - Total hours and cost: measures=["fct_horasreportadas.total_hours", "fct_horasreportadas.cost"]
    - Hours by product: measures=["fct_horasreportadas.total_hours"], dimensions=["fct_horasreportadas.product"]
    
    Args:
        query (dict): Optional. A complete CubeJS JSON query object.
        measures (list or str): Optional. The list of measures or single measure, e.g. ["fct_horasreportadas.total_hours"]
        dimensions (list or str): Optional. The list of dimensions or single dimension, e.g. ["fct_horasreportadas.product"]
        timeDimensions (list or dict): Optional. Time dimensions config.
        filters (list or dict): Optional. Filter conditions (can be a list of filters or a single filter object).
        limit (int or str): Optional. Max number of rows to return.
        offset (int or str): Optional. Number of rows to skip.
        order (dict or list or str): Optional. Ordering configuration.
        
    Returns:
        list: The 'data' array from CubeJS response.
    """
    if query is None:
        query = {}
        if measures is not None:
            query["measures"] = [measures] if isinstance(measures, str) else measures
        if dimensions is not None:
            query["dimensions"] = [dimensions] if isinstance(dimensions, str) else dimensions
        if timeDimensions is not None:
            query["timeDimensions"] = [timeDimensions] if isinstance(timeDimensions, dict) else timeDimensions
        if filters is not None:
            query["filters"] = [filters] if isinstance(filters, dict) else filters
        if limit is not None:
            query["limit"] = int(limit) if isinstance(limit, str) else limit
        if offset is not None:
            query["offset"] = int(offset) if isinstance(offset, str) else offset
        if order is not None:
            query["order"] = order
    else:
        # Standardize nested query fields if they were passed inside the 'query' object
        if "measures" in query and isinstance(query["measures"], str):
            query["measures"] = [query["measures"]]
        if "dimensions" in query and isinstance(query["dimensions"], str):
            query["dimensions"] = [query["dimensions"]]
        if "timeDimensions" in query and isinstance(query["timeDimensions"], dict):
            query["timeDimensions"] = [query["timeDimensions"]]
        if "filters" in query and isinstance(query["filters"], dict):
            query["filters"] = [query["filters"]]
        if "limit" in query and isinstance(query["limit"], str):
            query["limit"] = int(query["limit"])
        if "offset" in query and isinstance(query["offset"], str):
            query["offset"] = int(query["offset"])

    # Merge active dashboard filters into the query
    if _active_filters:
        existing = query.get("filters", [])
        if isinstance(existing, dict):
            existing = [existing]
        query = {**query, "filters": existing + _active_filters}
    else:
        # Just normalize filters in query if no active filters
        if "filters" in query and isinstance(query["filters"], dict):
            query["filters"] = [query["filters"]]

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
