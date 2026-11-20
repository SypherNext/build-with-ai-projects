# test_client.py
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import anyio


async def test():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "app.main"],
        env={"MCP_TRANSPORT": "stdio"}
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools]}")


# The lesson's own code calls `anyio.run(test())` -- invoking test()
# immediately produces a coroutine object, but anyio.run() expects a
# callable it invokes itself (as app/main.py correctly does with
# `anyio.run(main)`), and raises `TypeError: 'coroutine' object is not
# callable` otherwise. Fixed by passing the function, not the call.
anyio.run(test)
