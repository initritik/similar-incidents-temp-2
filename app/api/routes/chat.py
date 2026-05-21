# """
# Chat orchestration endpoint with Server-Sent Events (SSE) streaming.

# POST /chat/incidents
#   → Resolves the query
#   → Streams progress events (AgentEvents) as SSE
#   → Streams the final result as a "done" event

# The frontend consumes this stream so users see each agent step in real time.
# """

# import json
# from typing import Any, AsyncGenerator, Dict, List, Optional

# from fastapi import APIRouter, HTTPException
# from fastapi.responses import StreamingResponse
# from pydantic import BaseModel, Field

# from app.schemas.incident import IncidentRecord
# from app.services.agent_service import AgentEvent, AgentResult, run_agent
# from app.services.incident_fetch_service import fetch_incident_by_identifier
# from app.services.incident_parser_service import extract_incident_identifier
# from app.services.similarity_search_service import search_similar_incidents

# router = APIRouter()


# # ── Request / response models ─────────────────────────────────────────────────

# class IncidentChatRequest(BaseModel):
#     user_query: Optional[str] = Field(default=None, min_length=1)
#     incident_link: Optional[str] = Field(default=None, min_length=1)
#     incident_number: Optional[str] = Field(default=None, min_length=1)
#     top_k: int = Field(default=5, ge=1)


# class IncidentChatResult(BaseModel):
#     incident_number: str = ""
#     short_description: str = ""
#     description: str = ""
#     assignment_group: str = ""
#     priority: str = ""
#     category: str = ""
#     resolution_notes: str = ""
#     servicenow_link: str = ""
#     azure_devops_link: str = ""
#     datafix_code: str = ""
#     similarity_score: float = 0.0


# class IncidentChatResponse(BaseModel):
#     status: str
#     user_query: str
#     results: List[IncidentChatResult]
#     answer: str
#     recommended_resolution: str = ""
#     recommended_datafix: Optional[str] = None


# # ── Helpers ────────────────────────────────────────────────────────────────────

# def _reference_value(reference: object) -> str:
#     if reference is None:
#         return ""
#     return getattr(reference, "value", "") or getattr(reference, "link", "")


# def _build_query_from_incident(incident: IncidentRecord) -> str:
#     parts = [
#         incident.short_description,
#         incident.description,
#         incident.category,
#         _reference_value(incident.assignment_group),
#         incident.resolution_notes,
#     ]
#     text = "\n".join(p for p in parts if p)
#     if not text.strip():
#         raise ValueError("Fetched incident does not contain searchable text.")
#     return text


# def _resolve_chat_query(request: IncidentChatRequest) -> str:
#     provided = [
#         bool(request.incident_link and request.incident_link.strip()),
#         bool(request.incident_number and request.incident_number.strip()),
#         bool(request.user_query and request.user_query.strip()),
#     ]
#     if sum(provided) > 1:
#         raise ValueError("Provide only one of user_query, incident_link, or incident_number.")

#     if request.incident_link:
#         identifier = extract_incident_identifier(request.incident_link)
#         incident = fetch_incident_by_identifier(identifier)
#         return _build_query_from_incident(incident)

#     if request.incident_number:
#         identifier = extract_incident_identifier(request.incident_number)
#         incident = fetch_incident_by_identifier(identifier)
#         return _build_query_from_incident(incident)

#     if request.user_query and request.user_query.strip():
#         return request.user_query.strip()

#     raise ValueError("Provide user_query, incident_link, or incident_number.")


# def _map_result(raw: Dict[str, Any]) -> IncidentChatResult:
#     return IncidentChatResult(
#         incident_number=raw.get("number", ""),
#         short_description=raw.get("short_description", ""),
#         description=raw.get("description", ""),
#         assignment_group=raw.get("assignment_group", ""),
#         priority=raw.get("priority", ""),
#         category=raw.get("category", ""),
#         resolution_notes=raw.get("resolution_notes", ""),
#         servicenow_link=raw.get("servicenow_link", ""),
#         azure_devops_link=raw.get("azure_devops_link", ""),
#         datafix_code=raw.get("datafix_code", ""),
#         similarity_score=raw.get("similarity_score", 0.0),
#     )


# def _sse(event: str, data: Any) -> str:
#     """Format a single SSE message."""
#     return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# # ── SSE streaming endpoint ────────────────────────────────────────────────────

# async def _stream_chat(request: IncidentChatRequest) -> AsyncGenerator[str, None]:
#     """
#     Generator that yields SSE messages as the agent works.

#     Message types:
#       progress  – agent step update  { type, label, detail }
#       result    – final payload       { status, user_query, results, answer,
#                                         recommended_resolution, recommended_datafix }
#       error     – fatal error         { message }
#     """
#     # ── Resolve query ─────────────────────────────────────────────────────────
#     yield _sse("progress", {"type": "step_start", "label": "Resolving query", "detail": ""})

#     try:
#         user_query = _resolve_chat_query(request)
#     except LookupError as exc:
#         yield _sse("error", {"message": str(exc)})
#         return
#     except ValueError as exc:
#         yield _sse("error", {"message": str(exc)})
#         return

#     yield _sse("progress", {"type": "step_done", "label": "Query resolved",
#                              "detail": user_query[:120]})

#     # ── Similarity search ─────────────────────────────────────────────────────
#     yield _sse("progress", {"type": "step_start", "label": "Searching vector database",
#                              "detail": f"top_k={request.top_k}"})
#     try:
#         retrieved = search_similar_incidents(query_text=user_query, top_k=request.top_k)
#     except Exception as exc:
#         yield _sse("error", {"message": f"Search failed: {exc}"})
#         return

#     yield _sse("progress", {"type": "step_done", "label": "Similar incidents retrieved",
#                              "detail": f"{len(retrieved)} incident(s) found"})

#     # ── Agentic analysis ──────────────────────────────────────────────────────
#     events_buffer: list[AgentEvent] = []

#     def emit(event: AgentEvent) -> None:
#         events_buffer.append(event)

#     # run_agent is synchronous; we collect events then yield them.
#     # For a fully async agent, replace with an async generator in agent_service.
#     import asyncio
#     loop = asyncio.get_event_loop()

#     agent_result: AgentResult | None = None
#     agent_error: str | None = None

#     # Run synchronous agent in thread pool so we don't block the event loop
#     import concurrent.futures
#     executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

#     future = loop.run_in_executor(executor, run_agent, user_query, retrieved, emit)

#     # Poll the events buffer while the agent runs and stream them live
#     import asyncio as _asyncio
#     while not future.done():
#         # Drain any events the agent emitted
#         while events_buffer:
#             ev = events_buffer.pop(0)
#             yield _sse("progress", {"type": ev.type, "label": ev.label, "detail": ev.detail})
#         await _asyncio.sleep(0.05)

#     # Drain remaining events after agent finishes
#     while events_buffer:
#         ev = events_buffer.pop(0)
#         yield _sse("progress", {"type": ev.type, "label": ev.label, "detail": ev.detail})

#     try:
#         agent_result = await future
#     except Exception as exc:
#         yield _sse("error", {"message": f"Agent failed: {exc}"})
#         return

#     # ── Stream final result ───────────────────────────────────────────────────
#     results = [_map_result(r) for r in retrieved]

#     payload = IncidentChatResponse(
#         status="success",
#         user_query=user_query,
#         results=results,
#         answer=agent_result.summary,
#         recommended_resolution=agent_result.recommended_resolution,
#         recommended_datafix=agent_result.recommended_datafix,
#     )

#     yield _sse("result", payload.model_dump())


# @router.post("/chat/incidents")
# async def chat_about_incidents(request: IncidentChatRequest) -> StreamingResponse:
#     """
#     Stream agent progress and the final incident analysis result via SSE.

#     The response is a text/event-stream. Clients should listen for:
#       - 'progress' events while the agent works
#       - 'result'   event when analysis is complete
#       - 'error'    event on failure
#     """
#     return StreamingResponse(
#         _stream_chat(request),
#         media_type="text/event-stream",
#         headers={
#             "Cache-Control": "no-cache",
#             "X-Accel-Buffering": "no",  # disable nginx buffering
#         },
#     )



"""
Chat orchestration endpoint with Server-Sent Events (SSE) streaming.

POST /chat/incidents
  → Resolves the query
  → Streams progress events (AgentEvents) as SSE
  → Streams the final result as a "done" event

The frontend consumes this stream so users see each agent step in real time.
"""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.schemas.incident import IncidentRecord
from app.services.agent_service import AgentEvent, AgentResult, run_agent
from app.services.incident_fetch_service import fetch_incident_by_identifier
from app.services.incident_parser_service import extract_incident_identifier
from app.services.similarity_search_service import search_similar_incidents

router = APIRouter()


# ── Request / response models ─────────────────────────────────────────────────

class IncidentChatRequest(BaseModel):
    user_query: Optional[str] = Field(default=None, min_length=1)
    incident_link: Optional[str] = Field(default=None, min_length=1)
    incident_number: Optional[str] = Field(default=None, min_length=1)
    top_k: int = Field(default=5, ge=1)


class IncidentChatResult(BaseModel):
    incident_number: str = ""
    short_description: str = ""
    description: str = ""
    assignment_group: str = ""
    priority: str = ""
    category: str = ""
    resolution_notes: str = ""
    servicenow_link: str = ""
    azure_devops_link: str = ""
    datafix_code: str = ""
    similarity_score: float = 0.0


class IncidentChatResponse(BaseModel):
    status: str
    user_query: str
    results: List[IncidentChatResult]
    answer: str
    recommended_resolution: str = ""
    recommended_datafix: Optional[str] = None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _reference_value(reference: object) -> str:
    if reference is None:
        return ""
    return getattr(reference, "value", "") or getattr(reference, "link", "")


def _build_query_from_incident(incident: IncidentRecord) -> str:
    parts = [
        incident.short_description,
        incident.description,
        incident.category,
        _reference_value(incident.assignment_group),
        incident.resolution_notes,
    ]
    text = "\n".join(p for p in parts if p)
    if not text.strip():
        raise ValueError("Fetched incident does not contain searchable text.")
    return text


def _resolve_chat_query(request: IncidentChatRequest) -> str:
    provided = [
        bool(request.incident_link and request.incident_link.strip()),
        bool(request.incident_number and request.incident_number.strip()),
        bool(request.user_query and request.user_query.strip()),
    ]
    if sum(provided) > 1:
        raise ValueError("Provide only one of user_query, incident_link, or incident_number.")

    if request.incident_link:
        identifier = extract_incident_identifier(request.incident_link)
        incident = fetch_incident_by_identifier(identifier)
        return _build_query_from_incident(incident)

    if request.incident_number:
        identifier = extract_incident_identifier(request.incident_number)
        incident = fetch_incident_by_identifier(identifier)
        return _build_query_from_incident(incident)

    if request.user_query and request.user_query.strip():
        return request.user_query.strip()

    raise ValueError("Provide user_query, incident_link, or incident_number.")


def _map_result(raw: Dict[str, Any]) -> IncidentChatResult:
    return IncidentChatResult(
        incident_number=raw.get("number", ""),
        short_description=raw.get("short_description", ""),
        description=raw.get("description", ""),
        assignment_group=raw.get("assignment_group", ""),
        priority=raw.get("priority", ""),
        category=raw.get("category", ""),
        resolution_notes=raw.get("resolution_notes", ""),
        servicenow_link=raw.get("servicenow_link", ""),
        azure_devops_link=raw.get("azure_devops_link", ""),
        datafix_code=raw.get("datafix_code", ""),
        similarity_score=raw.get("similarity_score", 0.0),
    )


def _sse(event: str, data: Any) -> str:
    """Format a single SSE message."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# ── SSE streaming endpoint ────────────────────────────────────────────────────

async def _stream_chat(request: IncidentChatRequest) -> AsyncGenerator[str, None]:
    """
    Generator that yields SSE messages as the agent works.

    Message types:
      progress  – agent step update  { type, label, detail }
      result    – final payload       { status, user_query, results, answer,
                                        recommended_resolution, recommended_datafix }
      error     – fatal error         { message }
    """
    # ── Resolve query ─────────────────────────────────────────────────────────
    yield _sse("progress", {"type": "step_start", "label": "Resolving query", "detail": ""})

    try:
        user_query = _resolve_chat_query(request)
    except LookupError as exc:
        yield _sse("error", {"message": str(exc)})
        return
    except ValueError as exc:
        yield _sse("error", {"message": str(exc)})
        return

    yield _sse("progress", {"type": "step_done", "label": "Query resolved",
                             "detail": user_query[:120]})

    # ── Similarity search ─────────────────────────────────────────────────────
    yield _sse("progress", {"type": "step_start", "label": "Searching vector database",
                             "detail": f"top_k={request.top_k}"})
    try:
        retrieved = search_similar_incidents(query_text=user_query, top_k=request.top_k)
    except Exception as exc:
        yield _sse("error", {"message": f"Search failed: {exc}"})
        return

    yield _sse("progress", {"type": "step_done", "label": "Similar incidents retrieved",
                             "detail": f"{len(retrieved)} incident(s) found"})

    # ── Agentic analysis ──────────────────────────────────────────────────────
    events_buffer: list[AgentEvent] = []

    def emit(event: AgentEvent) -> None:
        events_buffer.append(event)

    # run_agent is synchronous; we collect events then yield them.
    # For a fully async agent, replace with an async generator in agent_service.
    import asyncio
    
    # Fixed Bug: get_event_loop() is deprecated in Python 3.10+ and causes issues here
    loop = asyncio.get_running_loop()

    agent_result: AgentResult | None = None
    agent_error: str | None = None

    # Run synchronous agent in thread pool so we don't block the event loop
    import concurrent.futures
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    future = loop.run_in_executor(executor, run_agent, user_query, retrieved, emit)

    # Poll the events buffer while the agent runs and stream them live
    import asyncio as _asyncio
    while not future.done():
        # Drain any events the agent emitted
        while events_buffer:
            ev = events_buffer.pop(0)
            yield _sse("progress", {"type": ev.type, "label": ev.label, "detail": ev.detail})
        await _asyncio.sleep(0.05)

    # Drain remaining events after agent finishes
    while events_buffer:
        ev = events_buffer.pop(0)
        yield _sse("progress", {"type": ev.type, "label": ev.label, "detail": ev.detail})

    try:
        agent_result = await future
    except Exception as exc:
        yield _sse("error", {"message": f"Agent failed: {exc}"})
        return

    # ── Stream final result ───────────────────────────────────────────────────
    results = [_map_result(r) for r in retrieved]

    payload = IncidentChatResponse(
        status="success",
        user_query=user_query,
        results=results,
        answer=agent_result.summary,
        recommended_resolution=agent_result.recommended_resolution,
        recommended_datafix=agent_result.recommended_datafix,
    )

    yield _sse("result", payload.model_dump())


@router.post("/chat/incidents")
async def chat_about_incidents(request: IncidentChatRequest) -> StreamingResponse:
    """
    Stream agent progress and the final incident analysis result via SSE.

    The response is a text/event-stream. Clients should listen for:
      - 'progress' events while the agent works
      - 'result'   event when analysis is complete
      - 'error'    event on failure
    """
    return StreamingResponse(
        _stream_chat(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )