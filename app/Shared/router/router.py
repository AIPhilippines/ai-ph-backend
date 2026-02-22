from fastapi import APIRouter
from typing import Any

api_router = APIRouter()

@api_router.get("/sample")
async def sample():
    return {"message": "Sample"}


