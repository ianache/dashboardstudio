import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent dir to path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load dotenv
load_dotenv(".env-ai-analyst", override=True)

from app.tools import cube

async def test():
    print("Testing CubeJS query with string filters:")
    
    # Simulate active filters
    cube._active_filters = [{"member": "fct_horasreportadas.area", "operator": "equals", "values": ["Desarrollo"]}]
    
    # 1. Test top-level filters parameter as a string
    try:
        res = await cube.query_data(
            measures=["fct_horasreportadas.total_hours"],
            dimensions=["fct_horasreportadas.area"],
            filters="fct_horasreportadas.area = Desarrollo"
        )
        print(f"Top-level string filters result: {res}")
    except Exception as e:
        print(f"Top-level string filters failed with exception: {type(e).__name__}: {e}")
        
    # 2. Test nested query filters as a string
    try:
        res = await cube.query_data(
            query={
                "measures": ["fct_horasreportadas.total_hours"],
                "dimensions": ["fct_horasreportadas.area"],
                "filters": "fct_horasreportadas.area = Desarrollo"
            }
        )
        print(f"Nested string filters result: {res}")
    except Exception as e:
        print(f"Nested string filters failed with exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test())
