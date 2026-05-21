"""
Incident normaliser: converts a ServiceNow record into embedding-ready text
and a structured metadata dict.
"""

from typing import Any, Dict, Optional

from app.schemas.incident import IncidentRecord, ReferenceField


def _reference_value(reference: Optional[ReferenceField]) -> str:
    if reference is None:
        return ""
    return reference.value or reference.link


def _add_line(lines: list, label: str, value: Any) -> None:
    if value:
        lines.append(f"{label}: {value}")


def normalize_incident(incident: IncidentRecord) -> Dict[str, Any]:
    """Convert a ServiceNow-style incident into embedding-ready text + metadata."""

    lines: list = []

    _add_line(lines, "Incident Number", incident.number)
    _add_line(lines, "Short Description", incident.short_description)
    _add_line(lines, "Description", incident.description)
    _add_line(lines, "Category", incident.category)
    _add_line(lines, "Subcategory", incident.subcategory)
    _add_line(lines, "Priority", incident.priority)
    _add_line(lines, "Severity", incident.severity)
    _add_line(lines, "State", incident.state)
    _add_line(lines, "Incident State", incident.incident_state)
    _add_line(lines, "Impact", incident.impact)
    _add_line(lines, "Urgency", incident.urgency)
    _add_line(lines, "Assignment Group", _reference_value(incident.assignment_group))
    _add_line(lines, "Assigned To", _reference_value(incident.assigned_to))
    _add_line(lines, "Caller", _reference_value(incident.caller_id))
    _add_line(lines, "Configuration Item", _reference_value(incident.cmdb_ci))
    _add_line(lines, "Close Notes", incident.close_notes)
    _add_line(lines, "Resolution Notes", incident.resolution_notes)
    # Include datafix summary in embedding text so similarity search naturally
    # surfaces incidents that were fixed with code when querying code-related issues.
    if incident.datafix_code:
        _add_line(lines, "Datafix Available", "yes")

    metadata = {
        "sys_id": incident.sys_id,
        "number": incident.number,
        "assignment_group": _reference_value(incident.assignment_group),
        "priority": incident.priority,
        "category": incident.category,
        "state": incident.state,
        "opened_at": incident.opened_at,
        "sys_created_on": incident.sys_created_on,
        "servicenow_link": incident.servicenow_link,
        "azure_devops_link": incident.azure_devops_link,
        "datafix_code": incident.datafix_code,
    }

    return {
        "text": "\n".join(lines),
        "metadata": metadata,
    }