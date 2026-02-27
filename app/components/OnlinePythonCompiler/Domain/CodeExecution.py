from pydantic import BaseModel
from typing import Optional

class CodeExecutionRequest(BaseModel):
    code: str

class CodeExecutionResponse(BaseModel):
    stdout: str
    stderr: str
    execution_time: float
    exit_code: int
    error: Optional[str] = None
