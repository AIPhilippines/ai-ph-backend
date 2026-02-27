import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.components.OnlinePythonCompiler.Domain.PythonExecution import ExecutionRequest

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_compile_python_endpoint_success(client):
    payload = {"code": "print('Clean Code Test')"}
    response = client.post("/api/v1/compile-python", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "stdout" in data
    assert "Clean Code Test" in data["stdout"]
    assert data["exit_code"] == 0

@pytest.mark.asyncio
async def test_compile_python_endpoint_syntax_error(client):
    payload = {"code": "invalid code"}
    response = client.post("/api/v1/compile-python", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["exit_code"] != 0
    assert "stderr" in data

@pytest.mark.asyncio
async def test_compile_python_endpoint_runtime_error(client):
    payload = {"code": "raise Exception('Runtime Error')"}
    response = client.post("/api/v1/compile-python", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["exit_code"] != 0
    assert "Runtime Error" in data["stderr"]
