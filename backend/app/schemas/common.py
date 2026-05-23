from pydantic import BaseModel, Field


class PageResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    q: str | None = Field(default=None, max_length=120)
