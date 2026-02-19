from fastapi import APIRouter
from app.services.example_service import get_hello_world

api_router = APIRouter()

@api_router.get("/hello")
async def hello():
    return get_hello_world()
