from datetime import datetime
from typing import Annotated

from django.db.models import Count
import msgspec

from incidents.models import Incident
from incidents.selectors import visible_incidents

from .server import server


class CountOpenResult(msgspec.Struct):
    count: int


@server.tool(
    description="Count only the open incidents the user can see",
    read_only=True,
)
def count_open_incidents(request) -> CountOpenResult:
    incidents = visible_incidents(request.user)
    return CountOpenResult(count=incidents.filter(status="open").count())


class ListOpenParams(msgspec.Struct):
    limit: Annotated[int, msgspec.Meta(ge=1, le=20)] = 10


class IncidentSummary(msgspec.Struct):
    id: int
    title: str
    created_at: datetime
    severity: str


class ListOpenResult(msgspec.Struct):
    incidents: list[IncidentSummary]


@server.tool(
    description="List the open incidents the user can see, "
    "newest first, up to limit (default 10)",
    read_only=True,
)
def list_open_incidents(request, params: ListOpenParams) -> ListOpenResult:
    incidents = (
        visible_incidents(request.user)
        .filter(status="open")
        .order_by("-created_at")[: params.limit]
    )
    return ListOpenResult(
        incidents=[
            IncidentSummary(id=incident.id, title=incident.title, created_at=incident.created_at, severity=incident.severity)
            for incident in incidents
        ]
    )


class GetIncidentParams(msgspec.Struct):
    incident_id: Annotated[int, msgspec.Meta(ge=1)]


class IncidentDetail(msgspec.Struct):
    id: int
    title: str
    description: str
    status: str
    severity: str
    created_at: datetime
    reporter: str
    assignee: str | None
    updated_at: datetime


class GetIncidentResult(msgspec.Struct):
    found: bool
    incident: IncidentDetail | None = None


@server.tool(
    description="Get one incident by ID with full details, "
    "returns `found: false` if the user cannot access it.",
    read_only=True,
)
def get_incident(request, params: GetIncidentParams) -> GetIncidentResult:
    incident = (
        visible_incidents(request.user)
        .filter(id=params.incident_id)
        .first()
    )
    if incident is None:
        return GetIncidentResult(found=False)
    return GetIncidentResult(
        found=True,
        incident=IncidentDetail(
            id=incident.id,
            title=incident.title,
            description=incident.description,
            status=incident.status,
            severity=incident.severity,
            created_at=incident.created_at,
            reporter=incident.reporter.username,
            assignee=incident.assignee.username if incident.assignee is not None else None,
            updated_at=incident.updated_at,
        )
    )


class StatusCount(msgspec.Struct):
    status: str
    count: int


class CountByStatusResult(msgspec.Struct):
    counts: list[StatusCount]


@server.tool(
    description="Count the incidents the user can see, "
    "grouped by status. Every status is included, with 0 "
    "if it has no incidents.",
    read_only=True,
)
def count_incidents_by_status(request) -> CountByStatusResult:
    rows = (
        visible_incidents(request.user)
        .values("status")
        .annotate(count=Count("id"))
    )
    counts_by_status = {row["status"]: row["count"] for row in rows}
    return CountByStatusResult(
        counts=[
            StatusCount(status=status, count=counts_by_status.get(status, 0))
            for status, _label in Incident.Status.choices
        ]
    )
