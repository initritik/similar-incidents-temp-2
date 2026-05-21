# """
# LLM response service with mock fallback.

# Uses the Anthropic Claude API (claude-sonnet-4-20250514) when ANTHROPIC_API_KEY
# is set, falls back to OpenAI when OPENAI_API_KEY is set, and produces a
# structured plain-text summary when neither key is available.
# """

# import json
# from typing import Any, Dict, List

# from app.config.settings import settings

# SYSTEM_PROMPT = """
# You are an incident support assistant.

# Use only the retrieved incident data provided by the backend.
# Do not invent incident numbers, symptoms, assignment groups, or resolutions.
# Do not fabricate resolution steps if resolution notes are missing.
# If the retrieved incidents do not contain enough information, say so clearly.

# Your job is to:
# - explain why the incidents are similar to the user's query
# - identify recurring issues or assignment groups when present
# - summarize resolution notes only when they are provided
# - highlight the highest-similarity incident
# - produce a concise, human-readable support response
# """.strip()


# def _serialize_incidents(incidents: List[Dict[str, Any]]) -> str:
#     return json.dumps(incidents, indent=2)


# def _build_user_prompt(user_query: str, incidents: List[Dict[str, Any]]) -> str:
#     return f"""
# User query:
# {user_query.strip()}

# Retrieved similar incidents:
# {_serialize_incidents(incidents)}

# Write a concise response for a support user. Include:
# - how many similar incidents were found
# - the strongest recurring issue or pattern
# - common resolution notes if present
# - the highest similarity incident
# """.strip()


# def _anthropic_response(user_query: str, incidents: List[Dict[str, Any]]) -> str:
#     """Call Claude via the Anthropic API."""
#     try:
#         import anthropic
#     except ImportError as exc:
#         raise RuntimeError("anthropic package is not installed.") from exc

#     client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
#     message = client.messages.create(
#         model="claude-sonnet-4-20250514",
#         max_tokens=1024,
#         system=SYSTEM_PROMPT,
#         messages=[{"role": "user", "content": _build_user_prompt(user_query, incidents)}],
#     )
#     content = message.content[0].text if message.content else ""
#     if not content.strip():
#         raise RuntimeError("Anthropic returned an empty response.")
#     return content.strip()


# def _openai_response(user_query: str, incidents: List[Dict[str, Any]]) -> str:
#     """Call GPT via the OpenAI API."""
#     try:
#         from openai import OpenAI, OpenAIError
#     except ImportError as exc:
#         raise RuntimeError("openai package is not installed.") from exc

#     client = OpenAI(api_key=settings.OPENAI_API_KEY)
#     try:
#         response = client.chat.completions.create(
#             model="gpt-4.1-mini",
#             messages=[
#                 {"role": "system", "content": SYSTEM_PROMPT},
#                 {"role": "user", "content": _build_user_prompt(user_query, incidents)},
#             ],
#             temperature=0.2,
#         )
#     except OpenAIError as exc:
#         raise RuntimeError("OpenAI chat completion request failed.") from exc

#     if not response.choices:
#         raise RuntimeError("OpenAI returned no chat completion choices.")

#     content = response.choices[0].message.content if response.choices[0].message else ""
#     if not content or not content.strip():
#         raise RuntimeError("OpenAI returned an empty incident response.")
#     return content.strip()


# def _mock_response(user_query: str, incidents: List[Dict[str, Any]]) -> str:
#     """
#     Produce a structured plain-text summary without any LLM API.

#     Used when no API key is configured so the full frontend flow can be
#     demonstrated locally.
#     """
#     if not incidents:
#         return "No similar incidents were found for your query."

#     top = incidents[0]
#     top_score = round(top.get("similarity_score", 0) * 100)

#     lines = [
#         f"Found {len(incidents)} similar incident(s) for your query.\n",
#         f"Most similar: {top.get('number', 'N/A')} "
#         f"({top_score}% match) — {top.get('short_description', '')}",
#     ]

#     # Collect unique assignment groups
#     groups = list(dict.fromkeys(
#         inc.get("assignment_group", "") for inc in incidents if inc.get("assignment_group")
#     ))
#     if groups:
#         lines.append(f"\nRecurring assignment group(s): {', '.join(groups)}")

#     # Summarise resolution notes
#     resolved = [
#         inc for inc in incidents
#         if inc.get("resolution_notes") and inc["resolution_notes"].strip()
#     ]
#     if resolved:
#         lines.append("\nResolution patterns from similar incidents:")
#         for inc in resolved[:3]:
#             lines.append(f"  • {inc['number']}: {inc['resolution_notes'][:200]}")

#     lines.append(
#         "\n[Note: This summary was generated without an LLM API key. "
#         "Set ANTHROPIC_API_KEY or OPENAI_API_KEY for AI-powered responses.]"
#     )

#     return "\n".join(lines)


# def generate_incident_response(
#     user_query: str,
#     similar_incidents: List[Dict[str, Any]],
# ) -> str:
#     """
#     Generate a readable incident summary grounded in retrieved incidents.

#     Priority: Anthropic API → OpenAI API → mock summary.
#     """
#     if not user_query or not user_query.strip():
#         raise ValueError("user_query is required.")

#     if not similar_incidents:
#         raise ValueError("similar_incidents cannot be empty.")

#     has_anthropic = bool(
#         settings.ANTHROPIC_API_KEY
#         and settings.ANTHROPIC_API_KEY not in ("", "your_api_key_here")
#     )
#     has_openai = bool(
#         settings.OPENAI_API_KEY
#         and settings.OPENAI_API_KEY not in ("", "your_api_key_here")
#     )

#     if has_anthropic:
#         return _anthropic_response(user_query, similar_incidents)

#     if has_openai:
#         return _openai_response(user_query, similar_incidents)

#     print("[llm] No API key configured – using mock LLM response.")
#     return _mock_response(user_query, similar_incidents)


"""
LLM response service with mock fallback.

Uses the Anthropic Claude API (claude-sonnet-4-20250514) when ANTHROPIC_API_KEY
is set, falls back to OpenAI when OPENAI_API_KEY is set, and produces a
structured plain-text summary when neither key is available.
"""

import json
from typing import Any, Dict, List

from app.config.settings import settings

SYSTEM_PROMPT = """
You are an incident support assistant.

Use only the retrieved incident data provided by the backend.
Do not invent incident numbers, symptoms, assignment groups, or resolutions.
Do not fabricate resolution steps if resolution notes are missing.
If the retrieved incidents do not contain enough information, say so clearly.

Your job is to:
- explain why the incidents are similar to the user's query
- identify recurring issues or assignment groups when present
- summarize resolution notes only when they are provided
- highlight the highest-similarity incident
- produce a concise, human-readable support response
""".strip()


def _serialize_incidents(incidents: List[Dict[str, Any]]) -> str:
    return json.dumps(incidents, indent=2)


def _build_user_prompt(user_query: str, incidents: List[Dict[str, Any]]) -> str:
    return f"""
User query:
{user_query.strip()}

Retrieved similar incidents:
{_serialize_incidents(incidents)}

Write a concise response for a support user. Include:
- how many similar incidents were found
- the strongest recurring issue or pattern
- common resolution notes if present
- the highest similarity incident
""".strip()


def _anthropic_response(user_query: str, incidents: List[Dict[str, Any]]) -> str:
    """Call Claude via the Anthropic API."""
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("anthropic package is not installed.") from exc

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620", # Fixed Bug: Removed fake model name
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": _build_user_prompt(user_query, incidents)}],
    )
    content = message.content[0].text if message.content else ""
    if not content.strip():
        raise RuntimeError("Anthropic returned an empty response.")
    return content.strip()


def _openai_response(user_query: str, incidents: List[Dict[str, Any]]) -> str:
    """Call GPT via the OpenAI API."""
    try:
        from openai import OpenAI, OpenAIError
    except ImportError as exc:
        raise RuntimeError("openai package is not installed.") from exc

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Fixed Bug: Removed fake model name
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(user_query, incidents)},
            ],
            temperature=0.2,
        )
    except OpenAIError as exc:
        raise RuntimeError("OpenAI chat completion request failed.") from exc

    if not response.choices:
        raise RuntimeError("OpenAI returned no chat completion choices.")

    content = response.choices[0].message.content if response.choices[0].message else ""
    if not content or not content.strip():
        raise RuntimeError("OpenAI returned an empty incident response.")
    return content.strip()


def _mock_response(user_query: str, incidents: List[Dict[str, Any]]) -> str:
    """
    Produce a structured plain-text summary without any LLM API.

    Used when no API key is configured so the full frontend flow can be
    demonstrated locally.
    """
    if not incidents:
        return "No similar incidents were found for your query."

    top = incidents[0]
    top_score = round(top.get("similarity_score", 0) * 100)

    lines = [
        f"Found {len(incidents)} similar incident(s) for your query.\n",
        f"Most similar: {top.get('number', 'N/A')} "
        f"({top_score}% match) — {top.get('short_description', '')}",
    ]

    # Collect unique assignment groups
    groups = list(dict.fromkeys(
        inc.get("assignment_group", "") for inc in incidents if inc.get("assignment_group")
    ))
    if groups:
        lines.append(f"\nRecurring assignment group(s): {', '.join(groups)}")

    # Summarise resolution notes
    resolved = [
        inc for inc in incidents
        if inc.get("resolution_notes") and inc["resolution_notes"].strip()
    ]
    if resolved:
        lines.append("\nResolution patterns from similar incidents:")
        for inc in resolved[:3]:
            lines.append(f"  • {inc['number']}: {inc['resolution_notes'][:200]}")

    lines.append(
        "\n[Note: This summary was generated without an LLM API key. "
        "Set ANTHROPIC_API_KEY or OPENAI_API_KEY for AI-powered responses.]"
    )

    return "\n".join(lines)


def generate_incident_response(
    user_query: str,
    similar_incidents: List[Dict[str, Any]],
) -> str:
    """
    Generate a readable incident summary grounded in retrieved incidents.

    Priority: Anthropic API → OpenAI API → mock summary.
    """
    if not user_query or not user_query.strip():
        raise ValueError("user_query is required.")

    if not similar_incidents:
        raise ValueError("similar_incidents cannot be empty.")

    has_anthropic = bool(
        settings.ANTHROPIC_API_KEY
        and settings.ANTHROPIC_API_KEY not in ("", "your_api_key_here")
    )
    has_openai = bool(
        settings.OPENAI_API_KEY
        and settings.OPENAI_API_KEY not in ("", "your_api_key_here")
    )

    if has_anthropic:
        return _anthropic_response(user_query, similar_incidents)

    if has_openai:
        return _openai_response(user_query, similar_incidents)

    print("[llm] No API key configured – using mock LLM response.")
    return _mock_response(user_query, similar_incidents)