from datetime import datetime
from typing import Annotated

import msgspec

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
