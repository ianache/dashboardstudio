import asyncio
import os
import sys

# Add parent dir to path so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.tools import cube

def test_resolve_member_with_custom_mappings():
    print("=== Test 1: set_custom_mappings_from_context and resolve_member ===")
    
    # 1. Simulate screen context
    screen_ctx = {
        "dashboard": {"name": "Test Dashboard"},
        "widgets": [
            {
                "title": "Colaboradores horas",
                "type": "bar",
                "cubeQuery": {
                    "measures": [
                        {
                            "key": "Colaborador.duracionJornada",
                            "label": "jornada"
                        }
                    ],
                    "dimensions": [
                        {
                            "key": "Colaborador.nombre",
                            "label": "Nombre Colaborador"
                        }
                    ]
                }
            }
        ]
    }
    
    # Extract and set mappings
    cube.set_custom_mappings_from_context(screen_ctx)
    
    # Test cases
    test_cases = [
        ("jornada", "Colaborador.duracionJornada"),
        ("Jornada", "Colaborador.duracionJornada"),
        ("Colaborador.jornada", "Colaborador.duracionJornada"),
        ("colaborador.jornada", "Colaborador.duracionJornada"),
        ("Nombre Colaborador", "Colaborador.nombre"),
        ("nombre colaborador", "Colaborador.nombre"),
        ("nombre_colaborador", "Colaborador.nombre"),
        ("Colaborador.Nombre Colaborador", "Colaborador.nombre"),
        ("Colaborador.nombre_colaborador", "Colaborador.nombre"),
        # Try to resolve something not customized but in static mappings
        ("role", "Colaborador.role"),
        ("Colaborador.role", "Colaborador.role"),
    ]
    
    success = True
    for input_val, expected in test_cases:
        resolved = cube.resolve_member(input_val)
        if resolved == expected:
            print(f"PASS: {input_val!r} -> {resolved!r}")
        else:
            print(f"FAIL: {input_val!r} -> expected {expected!r}, got {resolved!r}")
            success = False
            
    assert success, "Some resolve_member test cases failed!"
    print("=== Test 1 PASSED ===\n")


async def test_query_normalization():
    print("=== Test 2: query_data argument resolution ===")
    
    # Build a query structure
    raw_query = {
        "measures": ["jornada"],
        "dimensions": ["nombre colaborador"],
        "filters": [
            {
                "member": "nombre_colaborador",
                "operator": "equals",
                "values": ["Juan Perez"]
            }
        ]
    }
    
    # Let's mock the actual CubeJS HTTP request by overriding httpx.AsyncClient.post
    # so we can inspect the query payload sent to CubeJS
    import httpx
    original_post = httpx.AsyncClient.post
    
    captured_query = None
    
    async def mock_post(self, url, json=None, **kwargs):
        nonlocal captured_query
        if json and "query" in json:
            captured_query = json["query"]
        # Return a dummy response
        resp = httpx.Response(200, json={"data": [{"Colaborador.duracionJornada": 40, "Colaborador.nombre": "Juan Perez"}]})
        resp.request = httpx.Request("POST", url)
        return resp
        
    httpx.AsyncClient.post = mock_post
    
    try:
        res = await cube.query_data(query=raw_query)
        print("Mocked query_data executed successfully.")
        print(f"Captured Query: {captured_query}")
        
        # Verify normalization
        assert captured_query is not None
        assert "Colaborador.duracionJornada" in captured_query["measures"]
        assert "Colaborador.nombre" in captured_query["dimensions"]
        assert captured_query["filters"][0]["member"] == "Colaborador.nombre"
        print("PASS: query_data resolved metrics, dimensions, and filters correctly!")
        print("=== Test 2 PASSED ===\n")
    finally:
        httpx.AsyncClient.post = original_post


async def test_order_normalization():
    print("=== Test 3: order normalization ===")
    
    # 1. Test dict format with custom label and placeholder
    query_context = {
        "measures": ["Colaborador.duracionJornada"],
        "dimensions": ["Colaborador.nombre"]
    }
    
    # Custom label sorting
    res_dict = cube.normalize_order({"jornada": "desc"}, query_context)
    print(f"Dict custom mapping result: {res_dict}")
    assert res_dict == {"Colaborador.duracionJornada": "desc"}
    
    # Placeholder sorting
    res_placeholder = cube.normalize_order({"dimensions": "asc"}, query_context)
    print(f"Dict placeholder mapping result: {res_placeholder}")
    assert res_placeholder == {"Colaborador.nombre": "asc"}
    
    # 2. Test list format
    res_list = cube.normalize_order([["jornada", "desc"], ["dimensions", "asc"]], query_context)
    print(f"List format mapping result: {res_list}")
    assert res_list == [["Colaborador.duracionJornada", "desc"], ["Colaborador.nombre", "asc"]]
    
    # 3. Test list of dicts format
    res_list_dict = cube.normalize_order([{"id": "jornada", "desc": True}, {"id": "dimensions", "desc": False}], query_context)
    print(f"List of dicts mapping result: {res_list_dict}")
    assert res_list_dict == [{"id": "Colaborador.duracionJornada", "desc": True}, {"id": "Colaborador.nombre", "desc": False}]
    
    # 4. Test string format
    res_string = cube.normalize_order("jornada desc", query_context)
    print(f"String format mapping result: {res_string}")
    assert res_string == "Colaborador.duracionJornada desc"
    
    print("PASS: order normalization test cases passed successfully!")
    print("=== Test 3 PASSED ===")


if __name__ == "__main__":
    test_resolve_member_with_custom_mappings()
    asyncio.run(test_query_normalization())
    asyncio.run(test_order_normalization())
