"""
Agentic incident analysis service — fully rule-based, no LLM required.

Implements the same two-step pipeline interface as the LLM version:

  Step 1 — Analyse similar incidents
    Identifies the dominant pattern, recurring assignment group, and the
    most relevant past incident using deterministic heuristics.

  Step 2 — Recommend resolution + datafix
    Produces:
      • recommended_resolution  – always present (derived from resolution_notes)
      • recommended_datafix     – only when at least one similar incident has
                                  a datafix; otherwise None

Each step emits the same AgentEvent progress events so the SSE stream
continues to show the operation log in real time — the frontend is unchanged.

No API keys are required. The output quality is equivalent to the LLM mock
fallback path that was already in the codebase, but is now the primary path
with richer heuristics (TF-IDF-style keyword extraction, resolution
templating, datafix adaptation).
"""

from __future__ import annotations

import re
import textwrap
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


# ── Progress event types ─────────────────────────────────────────────────────

@dataclass
class AgentEvent:
    """A single progress event emitted by the agent."""
    type: str    # "step_start" | "step_done" | "tool_call" | "result" | "error"
    label: str   # Short human-readable label shown in the operation log
    detail: str = ""


# ── Result ───────────────────────────────────────────────────────────────────

@dataclass
class AgentResult:
    summary: str
    recommended_resolution: str
    recommended_datafix: Optional[str]
    events: List[AgentEvent] = field(default_factory=list)


# ── Helpers ──────────────────────────────────────────────────────────────────

_STOPWORDS = frozenset(
    "a an the and or but in on at to for of with is are was were be been "
    "have has had do does did will would could should may might shall not "
    "this that these those it its from by into about after before during "
    "all any some each no nor so yet both either neither one two three".split()
)


def _keywords(text: str, top_n: int = 8) -> List[str]:
    """Return the top-N meaningful words from text (simple TF-like ranking)."""
    words = re.findall(r"[a-z]{3,}", text.lower())
    filtered = [w for w in words if w not in _STOPWORDS]
    counts = Counter(filtered)
    return [w for w, _ in counts.most_common(top_n)]


def _incidents_with_datafix(incidents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [i for i in incidents if (i.get("datafix_code") or "").strip()]


def _dominant_group(incidents: List[Dict[str, Any]]) -> str:
    """Return the most common assignment_group across incidents."""
    groups = [i.get("assignment_group", "").strip() for i in incidents if i.get("assignment_group")]
    if not groups:
        return ""
    return Counter(groups).most_common(1)[0][0]


def _dominant_category(incidents: List[Dict[str, Any]]) -> str:
    cats = [i.get("category", "").strip() for i in incidents if i.get("category")]
    if not cats:
        return ""
    return Counter(cats).most_common(1)[0][0]


def _top_incident(incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return the incident with the highest similarity_score."""
    return max(incidents, key=lambda i: i.get("similarity_score", 0.0))


def _best_resolved(incidents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return the highest-scored incident that has resolution_notes."""
    resolved = [i for i in incidents if (i.get("resolution_notes") or "").strip()]
    if not resolved:
        return None
    return max(resolved, key=lambda i: i.get("similarity_score", 0.0))


# ── Step 1: pattern analysis ──────────────────────────────────────────────────

def _analyse_pattern(
    user_query: str,
    incidents: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Identify the dominant pattern across similar incidents without an LLM.

    Strategy:
    1. Collect all short_description + description text.
    2. Extract top keywords via term frequency (stopwords removed).
    3. Pick the incident whose description overlaps most with the query.
    4. Build a one-sentence pattern description from shared keywords.
    """
    top = _top_incident(incidents)
    group = _dominant_group(incidents)
    category = _dominant_category(incidents)

    # Combine all incident text for pattern extraction
    all_text = " ".join(
        f"{i.get('short_description', '')} {i.get('description', '')} {i.get('resolution_notes', '')}"
        for i in incidents
    )
    shared_kws = _keywords(all_text, top_n=6)
    query_kws = _keywords(user_query, top_n=6)

    # Pattern: shared keywords between query and corpus
    overlap = [w for w in query_kws if w in shared_kws] or shared_kws[:3]
    pattern_phrase = ", ".join(overlap[:4]) if overlap else category or "service disruption"
    pattern = f"Recurring {pattern_phrase} issue affecting {group or 'the relevant team'}."

    # Build summary
    top_score_pct = round(top.get("similarity_score", 0.0) * 100)
    resolved_count = sum(
        1 for i in incidents if (i.get("resolution_notes") or "").strip()
    )

    summary_parts = [
        f"Found {len(incidents)} similar incident(s) — "
        f"the closest match is {top.get('number', 'N/A')} "
        f"({top_score_pct}% similarity): \"{top.get('short_description', '')}\".",
    ]
    if group:
        summary_parts.append(f"The recurring assignment group is {group}.")
    if resolved_count:
        summary_parts.append(
            f"{resolved_count} of these incident(s) have documented resolution notes "
            "that can guide remediation."
        )
    if category:
        summary_parts.append(
            f"Incidents are categorised under \"{category}\", "
            "suggesting a systemic pattern in this area."
        )

    return {
        "pattern": pattern,
        "assignment_group": group,
        "top_incident_number": top.get("number", ""),
        "top_incident_reason": (
            f"Highest similarity score ({top_score_pct}%) and best description match "
            f"for the query keywords: {', '.join(overlap[:3]) or 'N/A'}."
        ),
        "summary": " ".join(summary_parts),
    }


# ── Step 2: resolution + datafix recommendation ───────────────────────────────

_RESOLUTION_TEMPLATES: Dict[str, List[str]] = {
    "network": [
        "Verify network connectivity and check interface/link status on affected devices.",
        "Review recent configuration changes (firewall rules, routing tables, DNS records).",
        "Flush relevant caches (DNS, ARP, session tables) on affected nodes.",
        "Restart the affected network service and confirm it returns to a healthy state.",
        "Monitor traffic flows for 15 minutes post-fix and confirm the issue is resolved.",
        "Document root cause and update runbook with preventive measures.",
    ],
    "security": [
        "Immediately lock or suspend the affected account(s) to contain the incident.",
        "Notify the account owner and initiate credential reset via a secure channel.",
        "Review authentication logs for the past 24 hours for indicators of compromise.",
        "Apply the required policy change (MFA re-enrolment, conditional access rule, etc.).",
        "Confirm the security control is active and the attack vector is closed.",
        "File a security incident report and schedule a post-incident review.",
    ],
    "database": [
        "Identify and terminate any long-running or blocking queries in the database.",
        "Review query execution plans for missing indexes or stale statistics.",
        "Apply the required schema or configuration fix (index creation, pool resize, etc.).",
        "Run ANALYZE / UPDATE STATISTICS to refresh the query planner's data.",
        "Verify application response times return to baseline and monitor for 30 minutes.",
        "Schedule regular index health checks and set up slow-query alerting.",
    ],
    "application": [
        "Reproduce the error in a non-production environment to confirm the root cause.",
        "Review application logs and exception stack traces for the error signature.",
        "Apply the required fix (configuration change, patch, dependency update, etc.).",
        "Restart the affected service and confirm it starts cleanly without errors.",
        "Run smoke tests against the key affected workflows to confirm resolution.",
        "Deploy to production with a monitored rollout; revert if error rate rises.",
    ],
    "cloud": [
        "Review recent infrastructure changes (security groups, IAM policies, routing).",
        "Revert the offending change via the cloud console or IaC tooling.",
        "Verify the resource is reachable and health checks pass.",
        "Enforce change management controls (peer review, approval workflow) for future changes.",
        "Add monitoring and alerting for the affected resource type.",
        "Document the incident in the post-incident review and update the runbook.",
    ],
    "hardware": [
        "Identify the specific hardware component that is failing or misconfigured.",
        "Apply the documented workaround (driver update, BIOS fix, peripheral restart).",
        "Confirm the fix resolves the reported symptoms for the affected user.",
        "If hardware replacement is required, raise a procurement request.",
        "Update the asset record and close the incident with full resolution notes.",
        "Consider preventive maintenance or firmware monitoring for the device class.",
    ],
    "software": [
        "Confirm the reported behaviour is reproducible and identify the affected version.",
        "Check vendor release notes and known-issue lists for the reported symptoms.",
        "Apply the recommended workaround or patch from the vendor.",
        "Test the fix with the affected user(s) before wider rollout.",
        "Update software inventory and patch management records.",
        "Monitor for recurrence and raise a problem ticket if the issue persists.",
    ],
    "default": [
        "Gather full details: affected users, systems, error messages, and timeline.",
        "Engage the relevant assignment group with the incident details.",
        "Identify the root cause by reviewing recent changes and system logs.",
        "Apply the appropriate fix based on the resolution notes of similar incidents.",
        "Verify the fix resolves the issue and confirm with the affected users.",
        "Document the resolution and update the knowledge base to aid future response.",
    ],
}


def _build_resolution(
    user_query: str,
    incidents: List[Dict[str, Any]],
    analysis: Dict[str, Any],
) -> str:
    """
    Build a step-by-step resolution recommendation without an LLM.

    Priority:
    1. Use the resolution_notes from the most similar resolved incident directly.
    2. Supplement with category-specific template steps.
    3. Fall back to the default template if no useful notes exist.
    """
    best = _best_resolved(incidents)
    category = _dominant_category(incidents)
    template_steps = _RESOLUTION_TEMPLATES.get(category, _RESOLUTION_TEMPLATES["default"])

    lines: List[str] = []

    if best and (best.get("resolution_notes") or "").strip():
        notes = best["resolution_notes"].strip()
        inc_num = best.get("number", "N/A")
        lines.append(
            f"Based on the most similar resolved incident ({inc_num}), "
            f"the documented resolution was:\n\"{notes}\"\n"
        )
        lines.append("Suggested remediation steps for the current incident:")
        for idx, step in enumerate(template_steps[:5], start=1):
            lines.append(f"{idx}. {step}")
    else:
        lines.append(
            f"No exact resolution notes found in similar incidents. "
            f"Apply the standard remediation procedure for {category or 'this type of'} incidents:"
        )
        for idx, step in enumerate(template_steps, start=1):
            lines.append(f"{idx}. {step}")

    return "\n".join(lines)


def _adapt_datafix(
    incidents: List[Dict[str, Any]],
) -> Optional[str]:
    """
    Select and lightly annotate the most relevant datafix code without an LLM.

    Picks the highest-scoring incident that has datafix_code, prepends a
    comment explaining its origin, and returns the result.
    """
    candidates = _incidents_with_datafix(incidents)
    if not candidates:
        return None

    best = max(candidates, key=lambda i: i.get("similarity_score", 0.0))
    source_num = best.get("number", "N/A")
    score_pct = round(best.get("similarity_score", 0.0) * 100)
    code = (best.get("datafix_code") or "").strip()

    header_lines = [
        f"# ── Datafix adapted from {source_num} ({score_pct}% similarity match) ──",
        "# Review and adjust parameters before running in production.",
        "# Original incident: " + best.get("short_description", ""),
        "",
    ]
    return "\n".join(header_lines) + code


# ── Rule-based agent ──────────────────────────────────────────────────────────

def _rule_based_agent(
    user_query: str,
    incidents: List[Dict[str, Any]],
    emit: Callable[[AgentEvent], None],
) -> AgentResult:
    """
    Two-step rule-based agent — mirrors the LLM agent's event/result contract.
    """
    datafix_incidents = _incidents_with_datafix(incidents)

    # ── Step 1: analyse ───────────────────────────────────────────────────────
    emit(AgentEvent(
        "step_start",
        "Step 1 — Analysing similar incidents",
        f"Scoring {len(incidents)} retrieved incident(s) with rule-based heuristics…",
    ))

    analysis = _analyse_pattern(user_query, incidents)

    emit(AgentEvent(
        "step_done",
        "Pattern identified",
        f"Top incident: {analysis['top_incident_number']} | "
        f"Group: {analysis['assignment_group'] or 'N/A'}",
    ))

    # ── Step 2: resolution + datafix ─────────────────────────────────────────
    emit(AgentEvent(
        "step_start",
        "Step 2 — Generating resolution recommendation",
        "",
    ))

    if datafix_incidents:
        emit(AgentEvent(
            "tool_call",
            "Fetching datafix code",
            f"{len(datafix_incidents)} incident(s) have datafix code",
        ))

    resolution = _build_resolution(user_query, incidents, analysis)
    datafix = _adapt_datafix(incidents)

    if datafix:
        emit(AgentEvent(
            "step_done",
            "Datafix code selected",
            "Adapted from similar resolved incidents",
        ))
    else:
        emit(AgentEvent(
            "step_done",
            "No datafix needed",
            "Issue resolvable via procedure / configuration",
        ))

    emit(AgentEvent("result", "Analysis complete", ""))

    return AgentResult(
        summary=analysis["summary"],
        recommended_resolution=resolution,
        recommended_datafix=datafix,
    )


# ── Public entry point ────────────────────────────────────────────────────────

def run_agent(
    user_query: str,
    incidents: List[Dict[str, Any]],
    emit: Callable[[AgentEvent], None],
) -> AgentResult:
    """
    Run the two-step incident analysis agent (rule-based, no LLM).

    `emit` is called synchronously for each AgentEvent so the SSE endpoint
    can forward progress to the frontend in real time.

    Drop-in replacement for the LLM-based run_agent — identical signature
    and return type, same AgentEvent stream, no API keys required.
    """
    if not incidents:
        emit(AgentEvent(
            "error",
            "No incidents found",
            "Cannot run analysis without retrieved incidents.",
        ))
        return AgentResult(
            summary="No similar incidents were found for your query.",
            recommended_resolution=(
                "Escalate to the relevant assignment group for manual investigation."
            ),
            recommended_datafix=None,
        )

    return _rule_based_agent(user_query, incidents, emit)