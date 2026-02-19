from pydantic import BaseModel

class ExampleEntity(BaseModel):
    """Example entity model."""
    id: int
    name: str
    description: str | None = None

    class Config:
        from_attributes = True
