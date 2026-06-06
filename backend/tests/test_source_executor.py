import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.source_executor import pre_execute_flow_nodes

@pytest.mark.asyncio
async def test_all_pre_executable_flow():
    """If all nodes are pre-executable, they should all be pre-executed."""
    flow_data = {
        "nodes": [
            {"id": "node-1", "toolType": "postgresql", "category": "source", "props": {}},
            {"id": "node-2", "toolType": "ods_pg", "category": "destination", "props": {}}
        ],
        "connections": [
            {"from": "node-1", "to": "node-2"}
        ],
        "metadata": {}
    }
    
    db_mock = MagicMock()
    websocket_mock = AsyncMock()

    with patch("app.services.source_executor.execute_source_node", new_callable=AsyncMock) as mock_exec_src, \
         patch("app.services.source_executor._pre_execute_ods_node", new_callable=AsyncMock) as mock_exec_ods:
        
        mock_exec_src.return_value = {"success": True, "rows": [{"col": "val"}], "count": 1}
        mock_exec_ods.return_value = {"success": True, "rows": [{"col": "val"}]}

        pre_exec_ok, result_flow = await pre_execute_flow_nodes(flow_data, db_mock, websocket_mock)

        assert pre_exec_ok is True
        assert result_flow["nodes"][0]["__pre_executed"] is True
        assert result_flow["nodes"][1]["__pre_executed"] is True
        mock_exec_src.assert_called_once()
        mock_exec_ods.assert_called_once()


@pytest.mark.asyncio
async def test_mixed_flow_skips_downstream_ods():
    """In a mixed flow (source -> script -> ODS), the ODS node should NOT be pre-executed."""
    flow_data = {
        "nodes": [
            {"id": "node-source", "toolType": "postgresql", "category": "source", "props": {}},
            {"id": "node-script", "toolType": "js_script", "category": "transform", "props": {}},
            {"id": "node-ods", "toolType": "ods_pg", "category": "destination", "props": {}}
        ],
        "connections": [
            {"from": "node-source", "to": "node-script"},
            {"from": "node-script", "to": "node-ods"}
        ],
        "metadata": {}
    }
    
    db_mock = MagicMock()
    websocket_mock = AsyncMock()

    with patch("app.services.source_executor.execute_source_node", new_callable=AsyncMock) as mock_exec_src, \
         patch("app.services.source_executor._pre_execute_ods_node", new_callable=AsyncMock) as mock_exec_ods:
        
        mock_exec_src.return_value = {"success": True, "rows": [{"col": "val"}], "count": 1}
        # mock_exec_ods shouldn't be called because the ODS node is not pre-executable

        pre_exec_ok, result_flow = await pre_execute_flow_nodes(flow_data, db_mock, websocket_mock)

        assert pre_exec_ok is True
        assert result_flow["nodes"][0].get("__pre_executed") is True
        # The script and ODS nodes should not be pre-executed
        assert result_flow["nodes"][1].get("__pre_executed") is None
        assert result_flow["nodes"][2].get("__pre_executed") is None
        mock_exec_src.assert_called_once()
        mock_exec_ods.assert_not_called()


@pytest.mark.asyncio
async def test_circular_reference_handled():
    """Circular references shouldn't cause infinite recursion and should be marked not pre-executable."""
    flow_data = {
        "nodes": [
            {"id": "node-1", "toolType": "postgresql", "category": "source", "props": {}},
            {"id": "node-2", "toolType": "ods_pg", "category": "destination", "props": {}}
        ],
        "connections": [
            {"from": "node-1", "to": "node-2"},
            {"from": "node-2", "to": "node-1"}  # Circular connection!
        ],
        "metadata": {}
    }
    
    db_mock = MagicMock()
    websocket_mock = AsyncMock()

    # Pre-execution should safely exit without infinite recursion.
    # Because of the cycle, node-1 has node-2 as parent, which has node-1 as parent,
    # making both not pre-executable.
    with patch("app.services.source_executor.execute_source_node", new_callable=AsyncMock) as mock_exec_src, \
         patch("app.services.source_executor._pre_execute_ods_node", new_callable=AsyncMock) as mock_exec_ods:
         
        pre_exec_ok, result_flow = await pre_execute_flow_nodes(flow_data, db_mock, websocket_mock)
        
        assert pre_exec_ok is True
        assert result_flow["nodes"][0].get("__pre_executed") is None
        assert result_flow["nodes"][1].get("__pre_executed") is None
        mock_exec_src.assert_not_called()
        mock_exec_ods.assert_not_called()
