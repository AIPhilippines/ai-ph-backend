from dataclasses import dataclass
from uuid import UUID
from datetime import datetime

@dataclass
class Post:
    id: UUID
    title: str
    slug: str
    author: str
    description: str
    tags: list[str]
    cover_image: str
    content: str
    created_at: datetime
    updated_at: datetime


@dataclass
class PostRequest:
    title: str
    slug: str
    author: str
    description: str
    tags: list[str]
    cover_image: str
    content: str