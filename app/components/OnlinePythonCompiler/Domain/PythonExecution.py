from pydantic import BaseModel
from typing import Optional

class ExecutionRequest(BaseModel):
    code: str

class ExecutionResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    error: Optional[str] = None
