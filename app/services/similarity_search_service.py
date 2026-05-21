"""
Similarity search service.

Embeds the query, searches Qdrant, and returns results shaped according to
the RESULT_FIELDS setting.
"""

from typing import Any, Dict, List, Optional

from qdrant_client.models import Filter, ScoredPoint

from app.config.settings import settings
from app.db.qdrant_client import get_qdrant_client
from app.services.embedding_service import generate_embedding

ALL_RESULT_FIELDS = {
    "number", "short_description", "description", "assignment_group",
    "priority", "category", "state", "resolution_notes", "opened_at",
    "servicenow_link", "azure_devops_link", "datafix_code", "similarity_score",
}


def _build_qdrant_filter(filters: Optional[Dict[str, str]]) -> Optional[Filter]:
    if not filters:
        return None
    supported = {"assignment_group", "category", "priority"}
    unsupported = set(filters) - supported
    if unsupported:
        raise ValueError("Unsupported filters: " + ", ".join(sorted(unsupported)))
    return None


def _format_search_result(point: ScoredPoint, fields: set) -> Dict[str, Any]:
    payload = point.payload or {}
    field_map = {
        "number":            lambda: payload.get("number", ""),
        "short_description": lambda: payload.get("short_description", ""),
        "description":       lambda: payload.get("description", ""),
        "assignment_group":  lambda: payload.get("assignment_group", ""),
        "priority":          lambda: payload.get("priority", ""),
        "category":          lambda: payload.get("category", ""),
        "state":             lambda: payload.get("state", ""),
        "resolution_notes":  lambda: payload.get("resolution_notes", ""),
        "opened_at":         lambda: payload.get("opened_at", ""),
        "servicenow_link":   lambda: payload.get("servicenow_link", ""),
        "azure_devops_link": lambda: payload.get("azure_devops_link", ""),
        "datafix_code":      lambda: payload.get("datafix_code", ""),
        "similarity_score":  lambda: point.score,
    }
    return {field: field_map[field]() for field in fields if field in field_map}


def search_similar_incidents(
    query_text: str,
    top_k: int = 5,
    filters: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    if not query_text or not query_text.strip():
        raise ValueError("query_text is required for similarity search.")
    if top_k < 1:
        raise ValueError("top_k must be greater than zero.")

    active_fields = settings.result_fields_set & ALL_RESULT_FIELDS
    if not active_fields:
        active_fields = ALL_RESULT_FIELDS

    try:
        query_embedding = generate_embedding(query_text.strip())
    except Exception as exc:
        raise RuntimeError("Failed to generate query embedding.") from exc

    try:
        client = get_qdrant_client()
        response = client.query_points(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query=query_embedding,
            limit=top_k,
            query_filter=_build_qdrant_filter(filters),
            with_payload=True,
        )
    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError("Qdrant similarity search failed.") from exc

    points = sorted(response.points, key=lambda p: p.score, reverse=True)
    return [_format_search_result(p, active_fields) for p in points]