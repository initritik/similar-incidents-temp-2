"""
Semantic similarity search endpoint.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.similarity_search_service import search_similar_incidents

router = APIRouter()


class SimilarIncidentSearchRequest(BaseModel):
    query_text: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1)


class SimilarIncidentResult(BaseModel):
    incident_number: str = ""
    short_description: str = ""
    description: str = ""
    assignment_group: str = ""
    priority: str = ""
    category: str = ""
    resolution_notes: str = ""
    servicenow_link: str = ""
    similarity_score: float = 0.0


class SimilarIncidentSearchResponse(BaseModel):
    status: str
    query_text: str
    results: List[SimilarIncidentResult]


def _map_result(raw: Dict[str, Any]) -> SimilarIncidentResult:
    return SimilarIncidentResult(
        incident_number=raw.get("number", ""),
        short_description=raw.get("short_description", ""),
        description=raw.get("description", ""),
        assignment_group=raw.get("assignment_group", ""),
        priority=raw.get("priority", ""),
        category=raw.get("category", ""),
        resolution_notes=raw.get("resolution_notes", ""),
        servicenow_link=raw.get("servicenow_link", ""),
        similarity_score=raw.get("similarity_score", 0.0),
    )


@router.post(
    "/search/similar-incidents",
    response_model=SimilarIncidentSearchResponse,
)
def search_similar_incidents_endpoint(
    request: SimilarIncidentSearchRequest,
) -> SimilarIncidentSearchResponse:
    """Search Qdrant for incidents semantically similar to the query."""

    query_text = request.query_text.strip()

    if not query_text:
        raise HTTPException(status_code=400, detail="query_text cannot be empty.")

    try:
        service_results = search_similar_incidents(
            query_text=query_text,
            top_k=request.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Similar incident search failed.",
        ) from exc

    return SimilarIncidentSearchResponse(
        status="success",
        query_text=query_text,
        results=[_map_result(r) for r in service_results],
    )
