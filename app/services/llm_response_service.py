"""
LLM response service — fully rule-based, no API key required.

Produces a structured plain-text summary from the retrieved incidents using
the same interface as the original Anthropic/OpenAI implementation.

The output mirrors what the LLM mock fallback produced, but with richer
heuristics:
  - Keyword extraction to highlight the recurring theme
  - Priority-ranked resolution notes
  - Grouped assignment-group summary
  - Similarity-score-aware ranking

This is the primary (and only) implementation. The original LLM-backed
paths have been replaced. No ANTHROPIC_API_KEY or OPENAI_API_KEY is needed.
"""

import re
from collections import Counter
from typing import Any, Dict, List


# ── Internal helpers ──────────────────────────────────────────────────────────

_STOPWORDS = frozenset(
    "a an the and or but in on at to for of with is are was were be been "
    "have has had do does did will would could should may might shall not "
    "this that these those it its from by into about after before during "
    "all any some each no nor so yet both either neither one two three "
    "users user issue error reported report system service team".split()
)


def _top_keywords(text: str, n: int = 5) -> List[str]:
    words = re.findall(r"[a-z]{4,}", text.lower())
    filtered = [w for w in words if w not in _STOPWORDS]
    return [w for w, _ in Counter(filtered).most_common(n)]


def _dominant_value(incidents: List[Dict[str, Any]], key: str) -> str:
    vals = [i.get(key, "").strip() for i in incidents if i.get(key, "").strip()]
    if not vals:
        return ""
    return Counter(vals).most_common(1)[0][0]


def _build_summary(
    user_query: str,
    incidents: List[Dict[str, Any]],
) -> str:
    """
    Build a concise, human-readable support summary from retrieved incidents.

    Sections:
      1. Overview (count + best match)
      2. Recurring pattern keywords
      3. Assignment group(s)
      4. Resolution notes from top resolved incidents
    """
    if not incidents:
        return "No similar incidents were found for your query."

    top = max(incidents, key=lambda i: i.get("similarity_score", 0.0))
    top_score_pct = round(top.get("similarity_score", 0.0) * 100)

    lines: List[str] = []

    # ── 1. Overview ──────────────────────────────────────────────────────────
    lines.append(
        f"Found {len(incidents)} similar incident(s) for your query.\n"
    )
    lines.append(
        f"Most similar: {top.get('number', 'N/A')} ({top_score_pct}% match) — "
        f"{top.get('short_description', '')}"
    )

    # ── 2. Recurring pattern ─────────────────────────────────────────────────
    corpus = " ".join(
        f"{i.get('short_description', '')} {i.get('description', '')} "
        f"{i.get('resolution_notes', '')}"
        for i in incidents
    )
    keywords = _top_keywords(corpus, n=5)
    if keywords:
        lines.append(
            f"\nRecurring theme keywords: {', '.join(keywords)}"
        )

    # ── 3. Assignment group(s) ───────────────────────────────────────────────
    groups = list(dict.fromkeys(
        i.get("assignment_group", "").strip()
        for i in incidents
        if i.get("assignment_group", "").strip()
    ))
    if groups:
        lines.append(f"\nRecurring assignment group(s): {', '.join(groups[:3])}")

    # ── 4. Resolution notes ──────────────────────────────────────────────────
    resolved = [
        i for i in incidents
        if (i.get("resolution_notes") or "").strip()
    ]
    # Sort by similarity score descending so the most relevant notes come first
    resolved.sort(key=lambda i: i.get("similarity_score", 0.0), reverse=True)

    if resolved:
        lines.append("\nResolution patterns from similar incidents:")
        for inc in resolved[:3]:
            snippet = inc["resolution_notes"].strip()[:220]
            if len(inc["resolution_notes"].strip()) > 220:
                snippet += "…"
            lines.append(f"  • {inc.get('number', 'N/A')}: {snippet}")
    else:
        lines.append(
            "\nNo resolved incidents with documented notes were found. "
            "Engage the assignment group for manual investigation."
        )

    # ── 5. Datafix indicator ─────────────────────────────────────────────────
    datafix_incs = [
        i for i in incidents
        if (i.get("datafix_code") or "").strip()
    ]
    if datafix_incs:
        nums = ", ".join(i.get("number", "?") for i in datafix_incs[:3])
        lines.append(
            f"\nDatafix code is available from: {nums}. "
            "See the Recommended Datafix tab for adapted code."
        )

    return "\n".join(lines)


# ── Public API ────────────────────────────────────────────────────────────────

def generate_incident_response(
    user_query: str,
    similar_incidents: List[Dict[str, Any]],
) -> str:
    """
    Generate a readable incident summary grounded in retrieved incidents.

    Drop-in replacement for the original LLM-backed function — identical
    signature, no API keys, deterministic output.

    Raises ValueError for invalid inputs (matching original contract).
    """
    if not user_query or not user_query.strip():
        raise ValueError("user_query is required.")

    if not similar_incidents:
        raise ValueError("similar_incidents cannot be empty.")

    return _build_summary(user_query.strip(), similar_incidents)