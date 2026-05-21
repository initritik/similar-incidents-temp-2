# """
# Agentic incident analysis service.

# Implements a two-step agent pipeline:

#   Step 1 — Analyse similar incidents
#     The LLM reads the retrieved incidents and identifies the pattern, recurring
#     assignment group, and the most relevant past incident.

#   Step 2 — Recommend resolution + datafix
#     The LLM produces:
#       • recommended_resolution  – always present
#       • recommended_datafix     – only when at least one similar incident has
#                                   a datafix; otherwise None

# Each step emits structured progress events so the SSE stream can show the user
# what the agent is doing in real time (like Claude Code's operation log).

# Falls back to a rule-based mock when no API key is configured.
# """

# from __future__ import annotations

# import json
# from dataclasses import dataclass, field
# from typing import Any, Callable, Dict, Generator, List, Optional

# from app.config.settings import settings


# # ── Progress event types ─────────────────────────────────────────────────────

# @dataclass
# class AgentEvent:
#     """A single progress event emitted by the agent."""
#     type: str    # "step_start" | "step_done" | "tool_call" | "result" | "error"
#     label: str   # Short human-readable label shown in the operation log
#     detail: str = ""  # Optional longer detail text


# # ── Result ───────────────────────────────────────────────────────────────────

# @dataclass
# class AgentResult:
#     summary: str
#     recommended_resolution: str
#     recommended_datafix: Optional[str]
#     events: List[AgentEvent] = field(default_factory=list)


# # ── Helpers ──────────────────────────────────────────────────────────────────

# def _has_api_key() -> tuple[bool, str]:
#     """Return (has_key, provider) for the first available LLM provider."""
#     if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY not in ("", "your_api_key_here"):
#         return True, "anthropic"
#     if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY not in ("", "your_api_key_here"):
#         return True, "openai"
#     return False, "none"


# def _incidents_with_datafix(incidents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#     return [i for i in incidents if i.get("datafix_code", "").strip()]


# def _serialize(obj: Any) -> str:
#     return json.dumps(obj, indent=2)


# # ── Anthropic two-step agent ─────────────────────────────────────────────────

# STEP1_SYSTEM = """
# You are an expert IT incident analyst.

# You will receive a user query describing an IT incident, and a list of
# similar past incidents retrieved from a vector database.

# Your job in this step:
# 1. Identify the primary pattern or root cause across the similar incidents.
# 2. Note the most relevant assignment group.
# 3. Pick the single most relevant past incident and explain why.
# 4. Write a concise natural-language summary (3-5 sentences) for a support engineer.

# Respond ONLY with a JSON object in this exact shape (no markdown, no preamble):
# {
#   "pattern": "<one-sentence pattern description>",
#   "assignment_group": "<group name>",
#   "top_incident_number": "<INC number>",
#   "top_incident_reason": "<one sentence>",
#   "summary": "<3-5 sentence summary for the engineer>"
# }
# """.strip()

# STEP2_SYSTEM = """
# You are an expert IT incident resolver.

# You will receive:
# - A user query describing a current incident.
# - An analysis summary from a previous step.
# - A list of similar resolved incidents (some may include datafix code).

# Your job:
# 1. Write a clear, actionable recommended_resolution (step-by-step, max 6 steps).
# 2. If any similar incident includes datafix_code, write a recommended_datafix
#    that adapts the most relevant code to the current issue. If no datafix_code
#    is present in ANY of the incidents, set recommended_datafix to null.

# Respond ONLY with a JSON object in this exact shape (no markdown, no preamble):
# {
#   "recommended_resolution": "<step-by-step resolution, use \\n for line breaks>",
#   "recommended_datafix": "<adapted code or script as a string, or null>"
# }
# """.strip()


# def _call_anthropic(system: str, user: str) -> str:
#     import anthropic
#     client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
#     msg = client.messages.create(
#         model="claude-sonnet-4-20250514",
#         max_tokens=1500,
#         system=system,
#         messages=[{"role": "user", "content": user}],
#     )
#     return msg.content[0].text if msg.content else ""


# def _call_openai(system: str, user: str) -> str:
#     from openai import OpenAI
#     client = OpenAI(api_key=settings.OPENAI_API_KEY)
#     resp = client.chat.completions.create(
#         model="gpt-4.1-mini",
#         messages=[{"role": "system", "content": system},
#                   {"role": "user", "content": user}],
#         temperature=0.2,
#     )
#     return resp.choices[0].message.content if resp.choices else ""


# def _parse_json(raw: str) -> Dict[str, Any]:
#     """Strip markdown fences and parse JSON."""
#     text = raw.strip()
#     if text.startswith("```"):
#         text = text.split("\n", 1)[-1]
#         text = text.rsplit("```", 1)[0]
#     return json.loads(text.strip())


# def _llm_call(system: str, user: str, provider: str) -> str:
#     if provider == "anthropic":
#         return _call_anthropic(system, user)
#     return _call_openai(system, user)


# # ── Mock agent (no API key) ───────────────────────────────────────────────────

# def _mock_agent(
#     user_query: str,
#     incidents: List[Dict[str, Any]],
#     emit: Callable[[AgentEvent], None],
# ) -> AgentResult:
#     emit(AgentEvent("step_start", "Analysing similar incidents", "Identifying patterns…"))

#     top = incidents[0] if incidents else {}
#     groups = list(dict.fromkeys(i.get("assignment_group", "") for i in incidents if i.get("assignment_group")))
#     datafix_incidents = _incidents_with_datafix(incidents)

#     summary = (
#         f"Found {len(incidents)} similar incident(s). "
#         f"The most relevant is {top.get('number', 'N/A')} "
#         f"({round(top.get('similarity_score', 0) * 100)}% match): "
#         f"{top.get('short_description', '')}. "
#         + (f"Recurring assignment group: {groups[0]}. " if groups else "")
#         + "[Mock summary — set ANTHROPIC_API_KEY for AI analysis.]"
#     )

#     emit(AgentEvent("step_done", "Pattern identified", f"Group: {groups[0] if groups else 'N/A'}"))
#     emit(AgentEvent("step_start", "Generating recommended resolution", ""))

#     resolution_lines = []
#     if top.get("resolution_notes"):
#         resolution_lines.append(f"Based on {top['number']}: {top['resolution_notes']}")
#     else:
#         resolution_lines.append("1. Verify the issue is reproducible in a staging environment.")
#         resolution_lines.append("2. Check relevant system logs for error messages.")
#         resolution_lines.append("3. Engage the assignment group for specialist investigation.")
#         resolution_lines.append("4. Apply fix, verify resolution, and update the incident record.")
#     recommended_resolution = "\n".join(resolution_lines)

#     emit(AgentEvent("step_done", "Resolution recommendation ready", ""))

#     recommended_datafix: Optional[str] = None
#     if datafix_incidents:
#         emit(AgentEvent("step_start", "Adapting datafix code", f"Source: {datafix_incidents[0].get('number')}"))
#         recommended_datafix = (
#             f"# Adapted from {datafix_incidents[0].get('number', 'N/A')}\n"
#             f"# [Mock datafix — set ANTHROPIC_API_KEY for AI-generated code]\n\n"
#             + datafix_incidents[0].get("datafix_code", "")
#         )
#         emit(AgentEvent("step_done", "Datafix code ready", ""))
#     else:
#         emit(AgentEvent("step_done", "No datafix needed", "Resolved via configuration or procedure"))

#     return AgentResult(
#         summary=summary,
#         recommended_resolution=recommended_resolution,
#         recommended_datafix=recommended_datafix,
#     )


# # ── Real two-step LLM agent ───────────────────────────────────────────────────

# def _real_agent(
#     user_query: str,
#     incidents: List[Dict[str, Any]],
#     provider: str,
#     emit: Callable[[AgentEvent], None],
# ) -> AgentResult:
#     datafix_incidents = _incidents_with_datafix(incidents)

#     # ── Step 1: analyse ───────────────────────────────────────────────────────
#     emit(AgentEvent("step_start", "Step 1 — Analysing similar incidents",
#                     f"Sending {len(incidents)} incidents to {provider}…"))

#     # Strip datafix_code from step 1 input to keep the prompt small
#     incidents_slim = [
#         {k: v for k, v in inc.items() if k != "datafix_code"}
#         for inc in incidents
#     ]
#     step1_user = (
#         f"User query:\n{user_query}\n\n"
#         f"Similar incidents:\n{_serialize(incidents_slim)}"
#     )

#     try:
#         step1_raw = _llm_call(STEP1_SYSTEM, step1_user, provider)
#         step1 = _parse_json(step1_raw)
#     except Exception as exc:
#         raise RuntimeError(f"Step 1 LLM call failed: {exc}") from exc

#     emit(AgentEvent("step_done", "Pattern identified",
#                     f"Top incident: {step1.get('top_incident_number', '?')} | "
#                     f"Group: {step1.get('assignment_group', '?')}"))

#     # ── Step 2: resolve + datafix ─────────────────────────────────────────────
#     emit(AgentEvent("step_start", "Step 2 — Generating resolution recommendation", ""))

#     if datafix_incidents:
#         emit(AgentEvent("tool_call", "Fetching datafix code",
#                         f"{len(datafix_incidents)} incident(s) have datafix code"))

#     step2_user = (
#         f"User query:\n{user_query}\n\n"
#         f"Step 1 analysis:\n{_serialize(step1)}\n\n"
#         f"Similar incidents (with datafix code where available):\n{_serialize(incidents)}"
#     )

#     try:
#         step2_raw = _llm_call(STEP2_SYSTEM, step2_user, provider)
#         step2 = _parse_json(step2_raw)
#     except Exception as exc:
#         raise RuntimeError(f"Step 2 LLM call failed: {exc}") from exc

#     recommended_datafix = step2.get("recommended_datafix") or None
#     if recommended_datafix:
#         emit(AgentEvent("step_done", "Datafix code generated",
#                         "Adapted from similar resolved incidents"))
#     else:
#         emit(AgentEvent("step_done", "No datafix needed",
#                         "Issue resolvable via procedure / configuration"))

#     emit(AgentEvent("result", "Analysis complete", ""))

#     return AgentResult(
#         summary=step1.get("summary", ""),
#         recommended_resolution=step2.get("recommended_resolution", ""),
#         recommended_datafix=recommended_datafix,
#     )


# # ── Public entry point ────────────────────────────────────────────────────────

# def run_agent(
#     user_query: str,
#     incidents: List[Dict[str, Any]],
#     emit: Callable[[AgentEvent], None],
# ) -> AgentResult:
#     """
#     Run the two-step incident analysis agent.

#     `emit` is called synchronously for each AgentEvent so the SSE endpoint
#     can forward progress to the frontend in real time.
#     """
#     if not incidents:
#         emit(AgentEvent("error", "No incidents found", "Cannot run analysis without retrieved incidents."))
#         return AgentResult(
#             summary="No similar incidents were found for your query.",
#             recommended_resolution="Escalate to the relevant assignment group for manual investigation.",
#             recommended_datafix=None,
#         )

#     has_key, provider = _has_api_key()

#     if not has_key:
#         emit(AgentEvent("step_start", "Mock agent (no API key)", "Using rule-based fallback…"))
#         result = _mock_agent(user_query, incidents, emit)
#         emit(AgentEvent("result", "Analysis complete (mock)", ""))
#         return result

#     return _real_agent(user_query, incidents, provider, emit)



"""
Agentic incident analysis service.

Implements a two-step agent pipeline:

  Step 1 — Analyse similar incidents
    The LLM reads the retrieved incidents and identifies the pattern, recurring
    assignment group, and the most relevant past incident.

  Step 2 — Recommend resolution + datafix
    The LLM produces:
      • recommended_resolution  – always present
      • recommended_datafix     – only when at least one similar incident has
                                  a datafix; otherwise None

Each step emits structured progress events so the SSE stream can show the user
what the agent is doing in real time (like Claude Code's operation log).

Falls back to a rule-based mock when no API key is configured.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generator, List, Optional

from app.config.settings import settings


# ── Progress event types ─────────────────────────────────────────────────────

@dataclass
class AgentEvent:
    """A single progress event emitted by the agent."""
    type: str    # "step_start" | "step_done" | "tool_call" | "result" | "error"
    label: str   # Short human-readable label shown in the operation log
    detail: str = ""  # Optional longer detail text


# ── Result ───────────────────────────────────────────────────────────────────

@dataclass
class AgentResult:
    summary: str
    recommended_resolution: str
    recommended_datafix: Optional[str]
    events: List[AgentEvent] = field(default_factory=list)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _has_api_key() -> tuple[bool, str]:
    """Return (has_key, provider) for the first available LLM provider."""
    if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY not in ("", "your_api_key_here"):
        return True, "anthropic"
    if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY not in ("", "your_api_key_here"):
        return True, "openai"
    return False, "none"


def _incidents_with_datafix(incidents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Fixed Bug: Ensures we don't call .strip() on None if datafix_code is explicitly null
    return [i for i in incidents if (i.get("datafix_code") or "").strip()]


def _serialize(obj: Any) -> str:
    return json.dumps(obj, indent=2)


# ── Anthropic two-step agent ─────────────────────────────────────────────────

STEP1_SYSTEM = """
You are an expert IT incident analyst.

You will receive a user query describing an IT incident, and a list of
similar past incidents retrieved from a vector database.

Your job in this step:
1. Identify the primary pattern or root cause across the similar incidents.
2. Note the most relevant assignment group.
3. Pick the single most relevant past incident and explain why.
4. Write a concise natural-language summary (3-5 sentences) for a support engineer.

Respond ONLY with a JSON object in this exact shape (no markdown, no preamble):
{
  "pattern": "<one-sentence pattern description>",
  "assignment_group": "<group name>",
  "top_incident_number": "<INC number>",
  "top_incident_reason": "<one sentence>",
  "summary": "<3-5 sentence summary for the engineer>"
}
""".strip()

STEP2_SYSTEM = """
You are an expert IT incident resolver.

You will receive:
- A user query describing a current incident.
- An analysis summary from a previous step.
- A list of similar resolved incidents (some may include datafix code).

Your job:
1. Write a clear, actionable recommended_resolution (step-by-step, max 6 steps).
2. If any similar incident includes datafix_code, write a recommended_datafix
   that adapts the most relevant code to the current issue. If no datafix_code
   is present in ANY of the incidents, set recommended_datafix to null.

Respond ONLY with a JSON object in this exact shape (no markdown, no preamble):
{
  "recommended_resolution": "<step-by-step resolution, use \\n for line breaks>",
  "recommended_datafix": "<adapted code or script as a string, or null>"
}
""".strip()


def _call_anthropic(system: str, user: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model="claude-3-5-sonnet-20240620", # Fixed Bug: Removed fake model name
        max_tokens=1500,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text if msg.content else ""


def _call_openai(system: str, user: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model="gpt-4o-mini", # Fixed Bug: Removed fake model name
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        temperature=0.2,
    )
    return resp.choices[0].message.content if resp.choices else ""


def _parse_json(raw: str) -> Dict[str, Any]:
    """Strip markdown fences and parse JSON."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text.strip())


def _llm_call(system: str, user: str, provider: str) -> str:
    if provider == "anthropic":
        return _call_anthropic(system, user)
    return _call_openai(system, user)


# ── Mock agent (no API key) ───────────────────────────────────────────────────

def _mock_agent(
    user_query: str,
    incidents: List[Dict[str, Any]],
    emit: Callable[[AgentEvent], None],
) -> AgentResult:
    emit(AgentEvent("step_start", "Analysing similar incidents", "Identifying patterns…"))

    top = incidents[0] if incidents else {}
    groups = list(dict.fromkeys(i.get("assignment_group", "") for i in incidents if i.get("assignment_group")))
    datafix_incidents = _incidents_with_datafix(incidents)

    summary = (
        f"Found {len(incidents)} similar incident(s). "
        f"The most relevant is {top.get('number', 'N/A')} "
        f"({round(top.get('similarity_score', 0) * 100)}% match): "
        f"{top.get('short_description', '')}. "
        + (f"Recurring assignment group: {groups[0]}. " if groups else "")
        + "[Mock summary — set ANTHROPIC_API_KEY for AI analysis.]"
    )

    emit(AgentEvent("step_done", "Pattern identified", f"Group: {groups[0] if groups else 'N/A'}"))
    emit(AgentEvent("step_start", "Generating recommended resolution", ""))

    resolution_lines = []
    if top.get("resolution_notes"):
        resolution_lines.append(f"Based on {top['number']}: {top['resolution_notes']}")
    else:
        resolution_lines.append("1. Verify the issue is reproducible in a staging environment.")
        resolution_lines.append("2. Check relevant system logs for error messages.")
        resolution_lines.append("3. Engage the assignment group for specialist investigation.")
        resolution_lines.append("4. Apply fix, verify resolution, and update the incident record.")
    recommended_resolution = "\n".join(resolution_lines)

    emit(AgentEvent("step_done", "Resolution recommendation ready", ""))

    recommended_datafix: Optional[str] = None
    if datafix_incidents:
        emit(AgentEvent("step_start", "Adapting datafix code", f"Source: {datafix_incidents[0].get('number')}"))
        recommended_datafix = (
            f"# Adapted from {datafix_incidents[0].get('number', 'N/A')}\n"
            f"# [Mock datafix — set ANTHROPIC_API_KEY for AI-generated code]\n\n"
            + datafix_incidents[0].get("datafix_code", "")
        )
        emit(AgentEvent("step_done", "Datafix code ready", ""))
    else:
        emit(AgentEvent("step_done", "No datafix needed", "Resolved via configuration or procedure"))

    return AgentResult(
        summary=summary,
        recommended_resolution=recommended_resolution,
        recommended_datafix=recommended_datafix,
    )


# ── Real two-step LLM agent ───────────────────────────────────────────────────

def _real_agent(
    user_query: str,
    incidents: List[Dict[str, Any]],
    provider: str,
    emit: Callable[[AgentEvent], None],
) -> AgentResult:
    datafix_incidents = _incidents_with_datafix(incidents)

    # ── Step 1: analyse ───────────────────────────────────────────────────────
    emit(AgentEvent("step_start", "Step 1 — Analysing similar incidents",
                    f"Sending {len(incidents)} incidents to {provider}…"))

    # Strip datafix_code from step 1 input to keep the prompt small
    incidents_slim = [
        {k: v for k, v in inc.items() if k != "datafix_code"}
        for inc in incidents
    ]
    step1_user = (
        f"User query:\n{user_query}\n\n"
        f"Similar incidents:\n{_serialize(incidents_slim)}"
    )

    try:
        step1_raw = _llm_call(STEP1_SYSTEM, step1_user, provider)
        step1 = _parse_json(step1_raw)
    except Exception as exc:
        raise RuntimeError(f"Step 1 LLM call failed: {exc}") from exc

    emit(AgentEvent("step_done", "Pattern identified",
                    f"Top incident: {step1.get('top_incident_number', '?')} | "
                    f"Group: {step1.get('assignment_group', '?')}"))

    # ── Step 2: resolve + datafix ─────────────────────────────────────────────
    emit(AgentEvent("step_start", "Step 2 — Generating resolution recommendation", ""))

    if datafix_incidents:
        emit(AgentEvent("tool_call", "Fetching datafix code",
                        f"{len(datafix_incidents)} incident(s) have datafix code"))

    step2_user = (
        f"User query:\n{user_query}\n\n"
        f"Step 1 analysis:\n{_serialize(step1)}\n\n"
        f"Similar incidents (with datafix code where available):\n{_serialize(incidents)}"
    )

    try:
        step2_raw = _llm_call(STEP2_SYSTEM, step2_user, provider)
        step2 = _parse_json(step2_raw)
    except Exception as exc:
        raise RuntimeError(f"Step 2 LLM call failed: {exc}") from exc

    recommended_datafix = step2.get("recommended_datafix") or None
    if recommended_datafix:
        emit(AgentEvent("step_done", "Datafix code generated",
                        "Adapted from similar resolved incidents"))
    else:
        emit(AgentEvent("step_done", "No datafix needed",
                        "Issue resolvable via procedure / configuration"))

    emit(AgentEvent("result", "Analysis complete", ""))

    return AgentResult(
        summary=step1.get("summary", ""),
        recommended_resolution=step2.get("recommended_resolution", ""),
        recommended_datafix=recommended_datafix,
    )


# ── Public entry point ────────────────────────────────────────────────────────

def run_agent(
    user_query: str,
    incidents: List[Dict[str, Any]],
    emit: Callable[[AgentEvent], None],
) -> AgentResult:
    """
    Run the two-step incident analysis agent.

    `emit` is called synchronously for each AgentEvent so the SSE endpoint
    can forward progress to the frontend in real time.
    """
    if not incidents:
        emit(AgentEvent("error", "No incidents found", "Cannot run analysis without retrieved incidents."))
        return AgentResult(
            summary="No similar incidents were found for your query.",
            recommended_resolution="Escalate to the relevant assignment group for manual investigation.",
            recommended_datafix=None,
        )

    has_key, provider = _has_api_key()

    if not has_key:
        emit(AgentEvent("step_start", "Mock agent (no API key)", "Using rule-based fallback…"))
        result = _mock_agent(user_query, incidents, emit)
        emit(AgentEvent("result", "Analysis complete (mock)", ""))
        return result

    return _real_agent(user_query, incidents, provider, emit)