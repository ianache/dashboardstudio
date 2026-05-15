import asyncio
import os
import sys
import json

sys.path.append(os.getcwd())

from app.services.deno_service import deno_service

async def test_topological_sort():
    print("Testing Topological Sort Execution Order")
    print("Flow Structure: [A] -> [B] -> [D], [A] -> [C] -> [D]")
    print("Expected Order: A, then (B and C in any order), then D\n")
    
    flow_data = {
        "nodes": [
            {
                "id": "node_D", "toolType": "js_script", "category": "transform", "label": "Node D (End)",
                "props": { "code": "console.log('--- EXECUTING D ---'); return ctx.payload;" }
            },
            {
                "id": "node_B", "toolType": "js_script", "category": "transform", "label": "Node B",
                "props": { "code": "console.log('--- EXECUTING B ---'); return ctx.payload;" }
            },
            {
                "id": "node_A", "toolType": "js_script", "category": "source", "label": "Node A (Start)",
                "props": { "code": "console.log('--- EXECUTING A ---'); return { msg: 'start' };" }
            },
            {
                "id": "node_C", "toolType": "js_script", "category": "transform", "label": "Node C",
                "props": { "code": "console.log('--- EXECUTING C ---'); return ctx.payload;" }
            }
        ],
        "connections": [
            {"id": "c1", "from": "node_A", "to": "node_B"},
            {"id": "c2", "from": "node_A", "to": "node_C"},
            {"id": "c3", "from": "node_B", "to": "node_D"},
            {"id": "c4", "from": "node_C", "to": "node_D"}
        ],
        "metadata": {}
    }
    
    async for log in deno_service.run_flow_stream(flow_data):
        if log["type"] == "info":
            print(f"LOG: {log['message']}")
        elif log["type"] == "node_status":
             print(f"STATUS: Node {log['node_id']} is {log['status']}")

if __name__ == "__main__":
    asyncio.run(test_topological_sort())
