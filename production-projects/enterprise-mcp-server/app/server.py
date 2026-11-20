# app/server.py
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import (
    Tool, TextContent, Resource, ResourceTemplate,
    CallToolResult, ReadResourceResult
)
from app.config import load_config
from app.auth import authenticate
from app.rate_limit import check_rate_limit
from app.backends import get_backend
from app.audit import audit_log
from app.circuit import breaker
import anyio

config = load_config()
server = Server(config["server"]["name"])


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name=t["name"],
            description=t["description"],
            inputSchema=t["input_schema"]
        )
        for t in config["tools"]
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict, context) -> CallToolResult:
    tool_def = next(t for t in config["tools"] if t["name"] == name)

    # Auth
    user = authenticate(context.request.headers)
    if not user:
        return CallToolResult(isError=True, content=[TextContent(type="text", text="Authentication failed")])

    # Check scopes
    for scope in tool_def["required_scopes"]:
        if scope not in user["scopes"]:
            return CallToolResult(isError=True, content=[TextContent(type="text", text=f"Missing scope: {scope}")])

    # Rate limit
    if not check_rate_limit(name, user["user"]):
        return CallToolResult(isError=True, content=[TextContent(type="text", text="Rate limit exceeded")])

    # Execute -- routed through the circuit breaker (app/circuit.py) so a
    # failing backend trips open instead of being hammered on every call.
    backend = get_backend(tool_def["backend"])
    import time
    start = time.time()
    try:
        result = await breaker.call_async(tool_def["backend"], backend.execute, name, arguments)
        duration = int((time.time() - start) * 1000)
        audit_log(user["user"], name, arguments, True, duration)
        return CallToolResult(content=[TextContent(type="text", text=str(result))])
    except Exception as e:
        duration = int((time.time() - start) * 1000)
        audit_log(user["user"], name, arguments, False, duration)
        return CallToolResult(isError=True, content=[TextContent(type="text", text=str(e))])


# Add to server.py
#
# The lesson calls `@server.list_resource_templates()` unconditionally, but
# that decorator does not exist on mcp.server.Server in mcp==1.0.0 -- the
# exact version pinned in requirements.txt (verified: Server only exposes
# list_resources/read_resource for resources in this release, no separate
# templates-listing handler). Guarded with hasattr() so the module still
# imports against the pinned SDK instead of raising AttributeError at
# import time; resource *reads* for both db:// and docs:// URIs still work
# through read_resource() below regardless.
if hasattr(server, "list_resource_templates"):
    @server.list_resource_templates()
    async def list_resource_templates() -> list[ResourceTemplate]:
        return [
            ResourceTemplate(
                uriTemplate=r["uri"],
                name=r["name"],
                mimeType=r.get("mime_type", "application/json")
            )
            for r in config["resources"]
        ]


@server.read_resource()
async def read_resource(uri: str, context) -> ReadResourceResult:
    from app.resources import resolve_resource
    content, mime_type = await resolve_resource(uri)
    return ReadResourceResult(
        contents=[TextContent(type="text", text=content, mimeType=mime_type)]
    )
