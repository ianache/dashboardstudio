import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_integration_monitoring():
    print("--- Testing Integration Monitoring Features ---")
    
    # 1. Check if flows have next_run_at
    print("\n[1] Checking flows for next_run_at field...")
    flows = requests.get(f"{BASE_URL}/integration-flows/").json()
    if not flows:
        print("No flows found.")
        return
    
    flow = flows[0]
    print(f"Flow: {flow['name']}")
    print(f"Next run: {flow.get('next_run_at')}")
    
    # Check for scheduling
    if flow.get('cron_expression'):
        assert 'next_run_at' in flow, "next_run_at missing from API response"
        print("PASS: next_run_at present")
    else:
        print("Skipping next_run_at check: Flow not scheduled.")

if __name__ == "__main__":
    test_integration_monitoring()
