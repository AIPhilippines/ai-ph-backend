from pydantic import BaseModel
from typing import Optional, List

class WebsiteIngestionRequest(BaseModel):
    url: str
    category: Optional[str] = None
    industry: Optional[str] = None

class WebsiteSubroutesRequest(BaseModel):
    url: str

class WebsiteSubroutesResponse(BaseModel):
    url: str
    sub_routes: List[str]

class IngestionResponse(BaseModel):
    status: str
    message: str
    chunk_count: int
    logs: List[str]

class IngestedDocResponse(BaseModel):
    id: str
    content: str
    metadata: dict
