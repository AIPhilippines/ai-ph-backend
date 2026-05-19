from fastapi import APIRouter, HTTPException
from app.components.Agent.Domain.AgentModels import AgentPromptRequest, AgentPromptResponse
from app.components.Agent.Application.AgentService import AgentService

agent_router = APIRouter()
service = AgentService()

@agent_router.post("/prompt", response_model=AgentPromptResponse)
async def prompt_agent(request: AgentPromptRequest):
    try:
        return service.prompt_agent(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
