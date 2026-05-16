import sys
import os
from unittest.mock import MagicMock, patch

# Ensure we can import from the backend directory
sys.path.append(os.path.join(os.getcwd(), "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user, TokenData
from app.core.database import get_db

# Mock authentication
async def mock_get_current_user():
    return TokenData(sub="testuser", roles=["admin"])

app.dependency_overrides[get_current_user] = mock_get_current_user

# Mock database model
class MockDS:
    def __init__(self, id, type, connection_url):
        self.id = id
        self.type = type
        self.connection_url = connection_url
        self.name = "Test DS"
        self.description = "Test Description"
        self.is_active = True
        self.created_by = "testuser"
        self.created_at = None
        self.updated_at = None

# Mock DB session
def get_mock_db():
    db = MagicMock()
    mock_query = db.query.return_value
    mock_filter = mock_query.filter.return_value
    
    # Mock data source instance
    # Note: connection_url in the model is used to store encoded JSON config
    import json
    config = {"host": "localhost", "database": "testdb"}
    ds = MockDS("ds-123", "postgresql", json.dumps(config))
    
    mock_filter.first.return_value = ds
    return db

app.dependency_overrides[get_db] = get_mock_db

client = TestClient(app)

def test_metadata_api():
    print("--- Testing Metadata API ---")

    # 1. Test GET /tables
    # We patch the service method to avoid actual DB connection attempt
    with patch("app.services.metadata_service.MetadataService.get_tables") as mock_get_tables:
        mock_get_tables.return_value = ["table1", "table2"]
        
        response = client.get("/api/v1/data-sources/ds-123/tables")
        print(f"GET /tables status: {response.status_code}")
        print(f"GET /tables body: {response.json()}")
        
        if response.status_code != 200:
            print(f"Error detail: {response.text}")
            sys.exit(1)
            
        assert response.json() == ["table1", "table2"]
        # Verify it was called with correctly decoded config and schema
        args, kwargs = mock_get_tables.call_args
        assert args[0]["host"] == "localhost"
        assert args[0]["type"] == "postgresql"
        assert args[1] == "public"

    # 2. Test GET /columns
    with patch("app.services.metadata_service.MetadataService.get_columns") as mock_get_columns:
        mock_get_columns.return_value = [{"name": "col1", "type": "integer"}]
        
        response = client.get("/api/v1/data-sources/ds-123/tables/table1/columns")
        print(f"GET /columns status: {response.status_code}")
        print(f"GET /columns body: {response.json()}")
        
        if response.status_code != 200:
            print(f"Error detail: {response.text}")
            sys.exit(1)
            
        assert response.json() == [{"name": "col1", "type": "integer"}]
        # Verify it was called with correctly decoded config, schema, and table
        args, kwargs = mock_get_columns.call_args
        assert args[0]["host"] == "localhost"
        assert args[1] == "public"
        assert args[2] == "table1"

    print("--- All tests passed! ---")

if __name__ == "__main__":
    test_metadata_api()
