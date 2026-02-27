import httpx
import os
from app.components.OnlinePythonCompiler.Domain.PythonExecution import ExecutionRequest, ExecutionResponse

class CodeExecutionService:
    def __init__(self):
        self.compiler_url = os.getenv("PYTHON_COMPILER_URL")
        self.timeout = float(os.getenv("COMPILER_TIMEOUT", 5.0))

    async def execute_python_code(self, request: ExecutionRequest) -> ExecutionResponse:
        if not self.compiler_url:
            return ExecutionResponse(
                stdout="",
                stderr="",
                exit_code=1,
                error="Compiler URL not configured in environment."
            )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.compiler_url,
                    json={"code": request.code},
                    timeout=self.timeout + 2.0
                )
                
                if response.status_code != 200:
                    return ExecutionResponse(
                        stdout="",
                        stderr="",
                        exit_code=1,
                        error=f"Compiler service returned error: {response.status_code} - {response.text}"
                    )
                
                data = response.json()
                return ExecutionResponse(
                    stdout=data.get("stdout", ""),
                    stderr=data.get("stderr", ""),
                    exit_code=data.get("exit_code", 1)
                )
            except httpx.TimeoutException:
                return ExecutionResponse(
                    stdout="",
                    stderr="Error: Execution timed out.",
                    exit_code=1,
                    error="Request to compiler service timed out."
                )
            except Exception as e:
                return ExecutionResponse(
                    stdout="",
                    stderr=str(e),
                    exit_code=1,
                    error=f"Unexpected error: {str(e)}"
                )
