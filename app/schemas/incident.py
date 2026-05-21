from typing import Optional

from pydantic import BaseModel


class ReferenceField(BaseModel):
    """ServiceNow-style reference object."""
    link: str
    value: str


class IncidentRecord(BaseModel):
    """ServiceNow-style incident record schema."""

    sys_id: str
    number: str
    short_description: str
    description: str
    category: str
    subcategory: str
    priority: str
    severity: str
    state: str
    incident_state: str
    impact: str
    urgency: str
    active: bool
    opened_at: str
    sys_created_on: str
    sys_updated_on: str
    close_notes: str
    resolution_notes: str

    # Direct link to open this incident in the ServiceNow UI.
    servicenow_link: str = ""

    # Azure DevOps PR/commit link for the datafix that resolved this incident.
    # Empty string when the incident was resolved without a code change.
    azure_devops_link: str = ""

    # Actual datafix code (SQL, Python, script, etc.) committed to resolve the
    # incident.  Empty string when no code change was needed.
    datafix_code: str = ""

    assignment_group: ReferenceField
    assigned_to: Optional[ReferenceField] = None
    caller_id: Optional[ReferenceField] = None
    cmdb_ci: Optional[ReferenceField] = None


class IncidentResponse(BaseModel):
    """Outer ServiceNow response wrapper."""
    result: IncidentRecord