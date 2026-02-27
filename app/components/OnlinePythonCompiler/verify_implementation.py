import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.components.OnlinePythonCompiler.Application.CodeExecutionService import CodeExecutionService
from app.components.OnlinePythonCompiler.Domain.PythonExecution import ExecutionRequest

async def verify_service():
    service = CodeExecutionService()
    
    # Test Success Case
    print("Testing CodeExecutionService.execute_python_code (Success Case)...")
    request = ExecutionRequest(code="print('Verification success')")
    response = await service.execute_python_code(request)
    print(f"Response: {response}")
    assert "Verification success" in response.stdout
    print("Success Case PASSED\n")

    # Test Error Case
    print("Testing CodeExecutionService.execute_python_code (Error Case)...")
    request = ExecutionRequest(code="import sys; sys.exit(1)")
    response = await service.execute_python_code(request)
    print(f"Response: {response}")
    assert response.exit_code == 1
    print("Error Case PASSED\n")

if __name__ == "__main__":
    try:
        asyncio.run(verify_service())
        print("All tests passed!")
    except Exception as e:
        print(f"Tests failed: {e}")
        sys.exit(1)
