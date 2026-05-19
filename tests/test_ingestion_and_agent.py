import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.components.Ingestion.Domain.IngestionModels import IngestionResponse, WebsiteSubroutesResponse, IngestedDocResponse
from app.components.Agent.Domain.AgentModels import AgentPromptResponse

@pytest.fixture
def client():
    return TestClient(app)

@patch('app.components.Ingestion.Infrastructure.IngestionController.service')
def test_ingest_website_success(mock_service, client):
    mock_service.ingest_website.return_value = IngestionResponse(
        status="success",
        message="Website ingested successfully",
        chunk_count=3,
        logs=["Scraped website", "Saved manifest"]
    )
    
    payload = {
        "url": "https://www.vaco.com/resources/case-studies/call-center",
        "category": "case-study",
        "industry": "general"
    }
    
    response = client.post("/api/v1/ingestion/website", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["chunk_count"] == 3
    mock_service.ingest_website.assert_called_once()

@patch('app.components.Ingestion.Infrastructure.IngestionController.service')
def test_get_website_sub_routes(mock_service, client):
    mock_service.discover_sub_routes.return_value = [
        "https://www.vaco.com/about",
        "https://www.vaco.com/blog"
    ]
    
    payload = {
        "url": "https://www.vaco.com"
    }
    
    response = client.post("/api/v1/ingestion/website/sub-routes", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == "https://www.vaco.com"
    assert len(data["sub_routes"]) == 2
    assert "https://www.vaco.com/about" in data["sub_routes"]
    mock_service.discover_sub_routes.assert_called_once_with("https://www.vaco.com")

@patch('app.components.Ingestion.Infrastructure.IngestionController.service')
def test_ingest_file_success(mock_service, client):
    mock_service.ingest_file.return_value = IngestionResponse(
        status="success",
        message="File test.pptx ingested successfully",
        chunk_count=5,
        logs=["Uploaded to storage", "PPTX parsed"]
    )
    
    file_content = b"fake presentation file content"
    files = {"file": ("test.pptx", file_content, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
    
    response = client.post("/api/v1/ingestion/file", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "test.pptx" in data["message"]
    assert data["chunk_count"] == 5
    mock_service.ingest_file.assert_called_once()

@patch('app.components.Ingestion.Infrastructure.IngestionController.service')
def test_get_documents(mock_service, client):
    mock_service.get_ingested_documents.return_value = [
        IngestedDocResponse(id="doc-1", content="chunk 1 content", metadata={"source": "test.pdf"}),
        IngestedDocResponse(id="doc-2", content="chunk 2 content", metadata={"source": "test.pdf"})
    ]
    
    response = client.get("/api/v1/ingestion/documents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "doc-1"
    assert data[1]["content"] == "chunk 2 content"
    mock_service.get_ingested_documents.assert_called_once()

@patch('app.components.Agent.Infrastructure.AgentController.service')
def test_prompt_agent(mock_service, client):
    mock_service.prompt_agent.return_value = AgentPromptResponse(
        response="This is a synthesized response about call center case studies.",
        steps=[{"type": "status", "content": "Node 'agent' finished."}],
        special_event=None
    )
    
    payload = {
        "prompt": "Tell me about outbound call centers",
        "session_id": "test-session"
    }
    
    response = client.post("/api/v1/agent/prompt", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "synthesized response" in data["response"]
    assert len(data["steps"]) == 1
    mock_service.prompt_agent.assert_called_once()
