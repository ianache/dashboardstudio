import sys
import os

sys.path.append(os.getcwd())
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import get_current_user, TokenData

async def mock_get_current_user():
    return TokenData(sub="admin", roles=["admin"])

app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(app)
response = client.get("/api/v1/integration-flows/")
print("STATUS CODE:", response.status_code)
if response.status_code == 200:
    for f in response.json():
        print(f"Flow: {f['name']}, Progress: {f.get('progress')}, Last Run Success: {f.get('last_run_success')}")
else:
    print(response.text)
