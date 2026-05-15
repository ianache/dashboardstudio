import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoints():
    print("--- Testing Execution History Endpoints ---")
    
    # 1. Listar flujos para obtener un ID
    print("\n[1] Fetching flows...")
    flows = requests.get(f"{BASE_URL}/integration-flows/").json()
    if not flows:
        print("No flows found to test.")
        return
    
    flow_id = flows[0]['id']
    print(f"Using Flow ID: {flow_id}")
    
    # 2. Consultar historial
    print(f"\n[2] Fetching history for {flow_id}...")
    history = requests.get(f"{BASE_URL}/execution-history/{flow_id}?limit=5").json()
    print(f"History count: {len(history)}")
    
    if history:
        exec_id = history[0]['id']
        print(f"Using Execution ID: {exec_id}")
        
        # 3. Consultar detalle
        print(f"\n[3] Fetching detail for {exec_id}...")
        detail = requests.get(f"{BASE_URL}/execution-history/detail/{exec_id}").json()
        print(f"Detail: {json.dumps(detail, indent=2)}")
    else:
        print("No execution history found for this flow.")

if __name__ == "__main__":
    test_endpoints()
