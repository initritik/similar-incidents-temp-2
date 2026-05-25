"""
Lexical similarity search service.

Finds similar incidents without an LLM, embeddings, or vector search. The
ranking is based on matching words, technical terms, and adjacent phrases
across the mock incident corpus.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from app.api.routes.incidents import ASSIGNMENT_GROUPS, MOCK_INCIDENTS
from app.config.settings import settings
from app.schemas.incident import IncidentRecord, ReferenceField

ALL_RESULT_FIELDS = {
    "number", "short_description", "description", "assignment_group",
    "priority", "category", "state", "resolution_notes", "opened_at",
    "servicenow_link", "azure_devops_link", "datafix_code", "similarity_score",
}

_STOPWORDS = frozenset(
    "a an the and or but if then else when while in on at to for of with by "
    "from into over under after before during is are was were be been being "
    "have has had do does did can could should would will may might must "
    "this that these those it its as not no yes all any some each every "
    "user users issue issues incident incidents problem problems report "
    "reported service system team teams affected unable able getting seeing "
    "show shows using use new old all multiple several approximately".split()
)

_GROUP_NAME_BY_ID = {group_id: name for name, group_id in ASSIGNMENT_GROUPS}


def _tokenize(text: str) -> List[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) >= 2 and token not in _STOPWORDS
    ]


def _ngrams(tokens: Sequence[str], sizes: Iterable[int] = (2, 3)) -> Set[Tuple[str, ...]]:
    phrases: Set[Tuple[str, ...]] = set()
    for size in sizes:
        if len(tokens) < size:
            continue
        phrases.update(tuple(tokens[i : i + size]) for i in range(len(tokens) - size + 1))
    return phrases


def _reference_value(reference: Optional[ReferenceField]) -> str:
    if reference is None:
        return ""
    value = reference.value or reference.link
    return _GROUP_NAME_BY_ID.get(value, value)


def _incident_search_fields(incident: IncidentRecord) -> Dict[str, str]:
    return {
        "number": incident.number,
        "short_description": incident.short_description,
        "description": incident.description,
        "category": incident.category,
        "subcategory": incident.subcategory,
        "priority": incident.priority,
        "severity": incident.severity,
        "state": incident.state,
        "assignment_group": _reference_value(incident.assignment_group),
        "resolution_notes": incident.resolution_notes,
        "close_notes": incident.close_notes,
        "datafix_code": "datafix code script sql python fix" if incident.datafix_code else "",
    }


def _build_payload(incident: IncidentRecord, score: float) -> Dict[str, Any]:
    return {
        "number": incident.number,
        "short_description": incident.short_description,
        "description": incident.description,
        "assignment_group": _reference_value(incident.assignment_group),
        "priority": incident.priority,
        "category": incident.category,
        "state": incident.state,
        "resolution_notes": incident.resolution_notes,
        "opened_at": incident.opened_at,
        "servicenow_link": incident.servicenow_link,
        "azure_devops_link": incident.azure_devops_link,
        "datafix_code": incident.datafix_code,
        "similarity_score": score,
    }


def _field_weight(field: str) -> float:
    weights = {
        "number": 5.0,
        "short_description": 3.5,
        "category": 2.5,
        "subcategory": 2.5,
        "assignment_group": 1.8,
        "description": 1.4,
        "resolution_notes": 1.0,
        "close_notes": 0.8,
        "priority": 0.6,
        "severity": 0.6,
        "state": 0.4,
        "datafix_code": 0.4,
    }
    return weights.get(field, 1.0)


def _score_incident(query_text: str, incident: IncidentRecord) -> float:
    query_tokens = _tokenize(query_text)
    if not query_tokens:
        return 0.0

    query_counts = Counter(query_tokens)
    query_terms = set(query_counts)
    query_phrases = _ngrams(query_tokens)
    fields = _incident_search_fields(incident)

    raw_score = 0.0
    max_word_score = sum((1.0 + math.log(count)) * 3.5 for count in query_counts.values())

    for field, value in fields.items():
        if not value:
            continue

        field_tokens = _tokenize(value)
        if not field_tokens:
            continue

        field_weight = _field_weight(field)
        field_counts = Counter(field_tokens)
        overlap = query_terms & set(field_counts)

        for term in overlap:
            query_weight = 1.0 + math.log(query_counts[term])
            field_frequency_bonus = 1.0 + math.log(field_counts[term])
            raw_score += field_weight * query_weight * field_frequency_bonus

        field_phrases = _ngrams(field_tokens)
        phrase_overlap = query_phrases & field_phrases
        if phrase_overlap:
            raw_score += field_weight * 3.0 * sum(len(phrase) - 1 for phrase in phrase_overlap)

    normalized_query = re.sub(r"\W+", "", query_text.lower())
    if incident.number.lower() in query_text.lower():
        raw_score += 10.0
    if incident.sys_id.replace("-", "").lower() in normalized_query:
        raw_score += 10.0

    if raw_score <= 0.0:
        return 0.0

    # Convert the open-ended lexical score into a UI-friendly 0..1 range.
    # This preserves ordering while avoiding impossible-looking 100% matches.
    denominator = max(max_word_score, 1.0)
    score = raw_score / (raw_score + denominator)
    return round(min(score, 0.99), 4)


def _build_filter(filters: Optional[Dict[str, str]]) -> Dict[str, str]:
    if not filters:
        return {}
    supported = {"assignment_group", "category", "priority"}
    unsupported = set(filters) - supported
    if unsupported:
        raise ValueError("Unsupported filters: " + ", ".join(sorted(unsupported)))
    return {key: value.strip().lower() for key, value in filters.items() if value.strip()}


def _matches_filters(incident: IncidentRecord, filters: Dict[str, str]) -> bool:
    if not filters:
        return True

    field_values = _incident_search_fields(incident)
    for key, expected in filters.items():
        actual = field_values.get(key, "").strip().lower()
        if actual != expected:
            return False
    return True


def _format_search_result(payload: Dict[str, Any], fields: set) -> Dict[str, Any]:
    return {field: payload.get(field, "") for field in fields if field in payload}


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

    active_filters = _build_filter(filters)
    scored: List[Tuple[float, IncidentRecord]] = []

    for incident in MOCK_INCIDENTS:
        if not _matches_filters(incident, active_filters):
            continue
        score = _score_incident(query_text.strip(), incident)
        if score > 0.0:
            scored.append((score, incident))

    scored.sort(
        key=lambda item: (
            item[0],
            bool(item[1].resolution_notes),
            item[1].opened_at,
        ),
        reverse=True,
    )

    results = [
        _build_payload(incident, score)
        for score, incident in scored[:top_k]
    ]
    return [_format_search_result(payload, active_fields) for payload in results]
