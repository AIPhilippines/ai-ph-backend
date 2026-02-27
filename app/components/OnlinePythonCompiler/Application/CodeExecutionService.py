import subprocess
import time
import tempfile
import os
from app.components.OnlinePythonCompiler.Domain.CodeExecution import CodeExecutionRequest, CodeExecutionResponse
from app.settings import settings

class CodeExecutionService:
    def __init__(self):
        self.timeout = float(os.getenv("COMPILER_TIMEOUT", 5))

    def execute_python_code(self, request: CodeExecutionRequest) -> CodeExecutionResponse:
        start_time = time.time()

        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w') as tmp:
            tmp.write(request.code)
            tmp_path = tmp.name

        try:
            process = subprocess.Popen(
                ["python", tmp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return CodeExecutionResponse(
                    stdout=stdout,
                    stderr=stderr,
                    execution_time=time.time() - start_time,
                    exit_code=-1,
                    error="Execution timed out"
                )

            execution_time = time.time() - start_time
            
            return CodeExecutionResponse(
                stdout=stdout,
                stderr=stderr,
                execution_time=round(execution_time, 4),
                exit_code=exit_code
            )

        except Exception as e:
            return CodeExecutionResponse(
                stdout="",
                stderr=str(e),
                execution_time=time.time() - start_time,
                exit_code=1,
                error=f"Unexpected error: {str(e)}"
            )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
