"""Archive quote alignment API."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.alignment import align_quotes

app = FastAPI(
    title="Archive Quote Alignment API",
    summary="Locate ordered quotes inside a source text.",
    version="1.0.0",
)


class AlignRequest(BaseModel):
    text: str = Field(..., description="Original source text.")
    quotes: list[str] = Field(..., description="Ordered quotes to locate.")


class Span(BaseModel):
    start: int = Field(..., description="Start offset in the original text (inclusive).")
    end: int = Field(..., description="End offset in the original text (exclusive).")


class AlignResponse(BaseModel):
    results: list[Span | None] = Field(
        ...,
        description="One entry per quote: its original [start, end) offsets, "
        "or null when the quote could not be located.",
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/quotes/align", response_model=AlignResponse)
def align(request: AlignRequest) -> AlignResponse:
    spans = align_quotes(request.text, request.quotes)
    return AlignResponse(
        results=[
            Span(start=span[0], end=span[1]) if span is not None else None
            for span in spans
        ]
    )
