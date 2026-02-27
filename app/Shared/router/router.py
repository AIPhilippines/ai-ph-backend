from fastapi import APIRouter
from typing import Any
from app.components.Posts.Application.PostHandlingService import PostHandlingService
from app.components.Posts.Domain.Post import PostRequest, Post
from app.components.OnlinePythonCompiler.Application.CodeExecutionService import CodeExecutionService
from app.components.OnlinePythonCompiler.Domain.PythonExecution import ExecutionRequest
from uuid import UUID

api_router = APIRouter()

@api_router.post("/make-post")
async def make_post(post: PostRequest):
    post_handling_service = PostHandlingService()
    try:
        post_handling_service.create_post(post)
        return {"message": "Post created successfully."}
    except Exception as e:
        return {"message": str(e)}

@api_router.get("/get-post/{id}")
async def get_post(id: UUID):
    post_handling_service = PostHandlingService()
    try:
        return post_handling_service.get_post(id)
    except Exception as e:
        return {"message": str(e)}

@api_router.get("/get-all-posts")
async def get_all_posts():
    post_handling_service = PostHandlingService()
    try:
        return post_handling_service.get_all_posts()
    except Exception as e:
        return {"message": str(e)}

@api_router.put("/update-post")
async def update_post(post: Post):
    post_handling_service = PostHandlingService()
    try:
        post_handling_service.update_post(post)
        return {"message": "Post updated successfully."}
    except Exception as e:
        return {"message": str(e)}

@api_router.delete("/delete-post/{id}")
async def delete_post(id: UUID):
    post_handling_service = PostHandlingService()
    try:
        post_handling_service.delete_post(id)
        return {"message": "Post deleted successfully."}
    except Exception as e:
        return {"message": str(e)}

@api_router.post("/compile-python")
async def compile_python(request: ExecutionRequest):
    code_execution_service = CodeExecutionService()
    try:
        return await code_execution_service.execute_python_code(request)
    except Exception as e:
        return {"message": str(e)}

