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
