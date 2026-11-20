# app/main.py
from app.server import server, config
from app.auth import init_tokens
from mcp.server.models import InitializationOptions
import anyio


async def main():
    if config["auth"]["enabled"]:
        init_tokens(config["auth"]["tokens"])

    transport = config["server"].get("transport", "stdio")

    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route
        import uvicorn

        sse = SseServerTransport("/messages")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send,
                server.create_initialization_options()
            ) as session:
                await server.run(session)

        app = Starlette(routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=sse.handle_post_message),
        ])

        host = config["server"].get("host", "0.0.0.0")
        port = config["server"].get("port", 8000)
        print(f"MCP Server running on http://{host}:{port}/sse")
        # Lesson's own code names this local variable `config`, which
        # shadows the module-level `config` imported from app.server for the
        # *entire* function (Python decides a name is local to a function
        # the moment it sees any assignment to that name anywhere in the
        # function body) -- so the `config["auth"]["enabled"]` and
        # `config["server"].get(...)` reads above would raise
        # UnboundLocalError before ever reaching this line. Renamed to
        # `uvicorn_config` to fix that.
        uvicorn_config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server_uv = uvicorn.Server(uvicorn_config)
        await server_uv.serve()
    else:
        from mcp.server.stdio import stdio_server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    anyio.run(main)
