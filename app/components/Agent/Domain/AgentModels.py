from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class AgentPromptRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = "default"

class AgentPromptResponse(BaseModel):
    response: str
    steps: List[Dict[str, Any]]
    special_event: Optional[str] = None
