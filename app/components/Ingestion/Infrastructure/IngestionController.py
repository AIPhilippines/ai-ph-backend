from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from app.components.Ingestion.Domain.IngestionModels import (
    WebsiteIngestionRequest,
    WebsiteSubroutesRequest,
    WebsiteSubroutesResponse,
    IngestionResponse,
    IngestedDocResponse
)
from app.components.Ingestion.Application.IngestionService import IngestionService

ingestion_router = APIRouter()
service = IngestionService()

@ingestion_router.post("/website", response_model=IngestionResponse)
async def ingest_website(request: WebsiteIngestionRequest):
    try:
        return service.ingest_website(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ingestion_router.post("/website/sub-routes", response_model=WebsiteSubroutesResponse)
async def get_website_sub_routes(request: WebsiteSubroutesRequest):
    try:
        sub_paths = service.discover_sub_routes(request.url)
        return WebsiteSubroutesResponse(url=request.url, sub_routes=sub_paths)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ingestion_router.post("/file", response_model=IngestionResponse)
async def ingest_file(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        return service.ingest_file(file.filename, file_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@ingestion_router.get("/documents", response_model=List[IngestedDocResponse])
async def get_documents():
    try:
        return service.get_ingested_documents()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
