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


def page_response(total: int, page: int, page_size: int, items: list, schema: type) -> PageResponse:
    """Wrap a page of rows, validating each with the response schema.

    Eleven services held their own `_page` copy until round 125 — ten byte-identical ones, which the duplicate-body
    gate pins, and an eleventh in `admin_service` that had already diverged in its loop variable and annotation
    without changing what it does. Each service imports this as `_page`, so **no call site changed**.
    """
    return PageResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[schema.model_validate(item) for item in items],
    )
