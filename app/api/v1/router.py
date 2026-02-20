from fastapi import APIRouter
from app.services.example_service import get_hello_world, compute_flames
from typing import Any

api_router = APIRouter()

@api_router.get("/hello")
async def hello(number: int):
    return get_hello_world(number)

@api_router.post("/compute-flames")
async def flames(name_1: str, name_2: str) -> dict[str, Any]:
    return compute_flames(name_1, name_2)