"""
Incident fetch service.

Looks up a single incident from the mock data source by sys_id or number.
When a real ServiceNow API is available, only this file and the import of
MOCK_INCIDENTS need to change — the rest of the pipeline stays the same.
"""

from typing import Dict

from app.api.routes.incidents import MOCK_INCIDENTS
from app.schemas.incident import IncidentRecord


def _strip_dashes(value: str) -> str:
    """Return a lowercase hex string with UUID dashes removed."""
    return value.replace("-", "").lower()


def fetch_incident_by_identifier(identifier: Dict[str, str]) -> IncidentRecord:
    """
    Fetch a mock incident by parsed sys_id or incident number.

    sys_id matching is dash-insensitive: the parser normalises to UUID format
    (with dashes) but the caller may pass either form, and ServiceNow URLs
    embed sys_ids as 32-char hex without dashes.
    """
    identifier_type = identifier.get("type")
    identifier_value = identifier.get("value")

    if identifier_type not in {"sys_id", "number"} or not identifier_value:
        raise ValueError("Invalid incident identifier.")

    for incident in MOCK_INCIDENTS:
        if identifier_type == "sys_id":
            # Compare without dashes so UUID format and hex32 format both match.
            if _strip_dashes(incident.sys_id) == _strip_dashes(identifier_value):
                return incident

        elif identifier_type == "number":
            if incident.number.upper() == identifier_value.upper():
                return incident

    raise LookupError(
        f"Incident '{identifier_value}' not found in mock incident source."
    )