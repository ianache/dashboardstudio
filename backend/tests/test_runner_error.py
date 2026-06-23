import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.deno_service import DenoService
from app.api.endpoints.execution_history import get_execution_detail
from app.api.endpoints.integration_flows import get_execution_logs

@pytest.mark.asyncio
async def test_deno_runner_logs_error_message():
    """Verify that when a node execution fails, DenoService yields the error log with error_message."""
    flow_data = {
        "nodes": [
            {
                "id": "node-fail",
                "toolType": "js_script",
                "category": "transform",
                "label": "Failing Script Node",
                "props": {
                    "code": "throw new Error('intentional test failure message');"
                }
            }
        ],
        "connections": [],
        "metadata": {}
    }

    deno_service = DenoService()
    logs = []
    
    async for log in deno_service.run_flow_stream(flow_data, payload={}):
        logs.append(log)

    # Find the node log corresponding to the failing node
    node_logs = [l for l in logs if l.get("type") == "node_log"]
    assert len(node_logs) > 0, "No node logs found in the stream output"
    
    fail_log = next((l for l in node_logs if l.get("node_id") == "node-fail" and l.get("status") == "error"), None)
    assert fail_log is not None, "Failed node log with status 'error' not found"
    
    assert fail_log.get("error_message") == "intentional test failure message", f"Expected error message not found. Got: {fail_log.get('error_message')}"


@pytest.mark.asyncio
async def test_get_execution_detail_returns_error_message():
    """Verify that get_execution_detail maps and returns the error_message from database logs."""
    # Mock models and database query
    mock_history = MagicMock()
    mock_history.id = "exec-1"
    mock_history.flow_id = "flow-1"
    mock_history.status = "error"
    mock_history.start_time = None
    mock_history.end_time = None
    mock_history.duration = 100
    mock_history.flow = None

    mock_log = MagicMock()
    mock_log.node_id = "node-1"
    mock_log.status = "error"
    mock_log.start_time = None
    mock_log.end_time = None
    mock_log.duration = 50
    mock_log.input_data = {"x": 1}
    mock_log.output_data = {}
    mock_log.error_message = "Test node failed"

    mock_history.node_logs = [mock_log]

    mock_db = MagicMock()
    # Mock db.query().filter().first() to return mock_history
    mock_db.query.return_value.filter.return_value.first.return_value = mock_history
    # Mock db.query().all() for EditorTool lookup
    mock_db.query.return_value.all.return_value = []

    res = await get_execution_detail(execution_id="exec-1", db=mock_db)

    assert res["id"] == "exec-1"
    assert len(res["node_logs"]) == 1
    assert res["node_logs"][0]["node_id"] == "node-1"
    assert res["node_logs"][0]["error_message"] == "Test node failed"


@pytest.mark.asyncio
async def test_get_execution_logs_returns_error_message():
    """Verify that get_execution_logs maps and returns the error_message from database logs."""
    mock_history = MagicMock()
    mock_history.flow_id = "flow-1"
    mock_history.status = "error"
    mock_history.start_time = None
    mock_history.end_time = None
    mock_history.duration = 100

    mock_log = MagicMock()
    mock_log.node_id = "node-1"
    mock_log.status = "error"
    mock_log.input_data = {"x": 1}
    mock_log.output_data = {}
    mock_log.error_message = "Test node failure"
    mock_log.duration = 50
    mock_log.start_time = None
    mock_log.end_time = None

    mock_db = MagicMock()
    # First query for ExecutionHistory
    # Second query for NodeExecutionLogs
    mock_db.query.return_value.filter.return_value.first.return_value = mock_history
    mock_db.query.return_value.filter.return_value.all.return_value = [mock_log]

    # Patch ensure_user_exists to pass without actual auth/user logic
    with patch("app.api.endpoints.integration_flows.ensure_user_exists", new_callable=AsyncMock) as mock_ensure:
        res = await get_execution_logs(exec_id="exec-1", db=mock_db, current_user=MagicMock())
        assert res["status"] == "error"
        assert len(res["logs"]) == 1
        assert res["logs"][0]["node_id"] == "node-1"
        assert res["logs"][0]["error_message"] == "Test node failure"
