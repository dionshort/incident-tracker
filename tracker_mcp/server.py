from django_mcpz.bearer_tokens.auth import token_auth
from django_mcpz.server import MCPServer


server = MCPServer(
    name="incidents",
    version="0.1.0",
    instructions="Query the incidents being tracked",
    auth=token_auth,
)
