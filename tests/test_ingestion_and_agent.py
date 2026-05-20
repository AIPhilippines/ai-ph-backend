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

def test_agent_service_widget_preservation_and_events():
    from app.components.Agent.Application.AgentService import AgentService
    
    service = AgentService()
    
    # Test depth-tracking custom tag extraction inside synthesize_final_response
    raw_response_with_flashcards = "Here is an explanation. [FLASHCARDS:{\"topic\":\"ML\",\"cards\":[{\"front\":\"Q\",\"back\":\"A\"}]}]"
    synthesized = service.synthesize_final_response(
        user_query="give me cards",
        retrieved_sources=[],
        raw_agent_response=raw_response_with_flashcards
    )
    assert "[FLASHCARDS:{\"topic\":\"ML\",\"cards\":[{\"front\":\"Q\",\"back\":\"A\"}]}]" in synthesized

    raw_response_with_minigame = "Let's play a game. [MINIGAME:{\"game_type\":\"guessing_game\",\"topic\":\"AI\",\"data\":{\"word\":\"A\",\"clue\":\"B\"}}]"
    synthesized_game = service.synthesize_final_response(
        user_query="let's play guessing game",
        retrieved_sources=[],
        raw_agent_response=raw_response_with_minigame
    )
    assert "[MINIGAME:{\"game_type\":\"guessing_game\",\"topic\":\"AI\",\"data\":{\"word\":\"A\",\"clue\":\"B\"}}]" in synthesized_game


def test_agent_service_memory_retrieval():
    from app.components.Agent.Application.AgentService import AgentService
    from app.components.Agent.Domain.AgentModels import AgentPromptRequest
    from langchain_core.messages import HumanMessage, AIMessage
    
    service = AgentService()
    
    # Mock supabase client
    mock_execute = MagicMock()
    # Let's say we have 3 logs in DB, returned in descending order of ID (newest first)
    mock_execute.data = [
        {"id": 3, "user_query": "Third user query", "agent_response": "Third agent response"},
        {"id": 2, "user_query": "Second user query", "agent_response": "Second agent response"},
        {"id": 1, "user_query": "First user query", "agent_response": "First agent response"}
    ]
    
    # Set up supabase mock query builder
    query_builder = MagicMock()
    query_builder.select.return_value = query_builder
    query_builder.eq.return_value = query_builder
    query_builder.order.return_value = query_builder
    query_builder.limit.return_value = query_builder
    query_builder.execute.return_value = mock_execute
    
    service.supabase.client.table = MagicMock(return_value=query_builder)
    
    # Mock the langgraph app_graph stream to prevent real LLM call
    mock_stream = MagicMock(return_value=[])
    with patch("app.components.Agent.Application.AgentService.app_graph.stream", mock_stream):
        # We also patch synthesize_final_response and log_query to keep the test clean
        with patch.object(service, "synthesize_final_response", return_value="Response"):
            with patch.object(service, "log_query") as mock_log:
                request = AgentPromptRequest(prompt="Current query", session_id="test-session-123")
                service.prompt_agent(request)
                
                # Check that supabase query was built correctly with order desc=True and limit=30
                service.supabase.client.table.assert_called_with("query_logs")
                query_builder.select.assert_called_with("user_query, agent_response, id")
                query_builder.eq.assert_called_with("session_id", "test-session-123")
                query_builder.order.assert_called_with("id", desc=True)
                query_builder.limit.assert_called_with(30)
                
                # Check stream input to see if history messages were reversed to chronological order
                called_args, _ = mock_stream.call_args
                initial_state = called_args[0]
                messages = initial_state["messages"]
                
                # Find HumanMessage and AIMessage inside messages
                hist_msgs = [m for m in messages if isinstance(m, (HumanMessage, AIMessage))]
                # The last message is the current query (HumanMessage("Current query"))
                # The preceding ones should be the chronological history (First -> Second -> Third)
                assert len(hist_msgs) == 7 # 3 pairs of Q&A + 1 current prompt
                assert hist_msgs[0].content == "First user query"
                assert hist_msgs[1].content == "First agent response"
                assert hist_msgs[2].content == "Second user query"
                assert hist_msgs[3].content == "Second agent response"
                assert hist_msgs[4].content == "Third user query"
                assert hist_msgs[5].content == "Third agent response"
                assert hist_msgs[6].content == "Current query"

