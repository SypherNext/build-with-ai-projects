# Enterprise MCP Server

Reference implementation for the "Build an Enterprise MCP Server" Production
Project in Sypher's `build-with-ai` course. A Model Context Protocol server
exposing database, API-proxy, and notification tools with bearer-token auth
with scopes, per-tool rate limiting, a circuit breaker around backend calls,
SQL input validation, audit logging, and both stdio and SSE transports.

This is the finished, verified version -- type the lesson's own steps
yourself first; come back here to compare your output or see it run.

- `config.yaml` -- tool and resource definitions (Build Step 1)
- `app/config.py` -- loads `config.yaml`
- `app/server.py` -- the MCP server core: tool listing, tool calls, resource
  templates (Build Steps 2 and 8)
- `app/backends.py` -- Postgres, HTTP, and notification backend connectors
  (Build Step 3)
- `app/auth.py` -- bearer-token authentication (Build Step 4)
- `app/rate_limit.py` -- per-user, per-tool rate limiting (Build Step 5)
- `app/audit.py` -- structured audit logging (Build Step 6)
- `app/main.py` -- entrypoint; picks stdio or SSE transport from
  `config.yaml` (Build Step 7)
- `app/resources.py` -- resolves the `db://` and `docs://` resource URIs
  declared in `config.yaml` (Build Step 8)
- `app/circuit.py` -- circuit breaker for backend calls (Deploy "Production
  Hardening")
- `app/validation.py` -- blocked-pattern SQL validation and input truncation
  (Deploy "Production Hardening")
- `test_client.py` -- connects over stdio and lists the server's tools
  (Build Step 9)
- `Dockerfile` -- builds the SSE server into a container image (verified
  locally only; no cloud deployment was provisioned for this reference)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env        # then fill in your own backend connection details
```

## Run the server (SSE)

```bash
python -m app.main
# MCP Server running on http://0.0.0.0:8000/sse
```

## Run the server (stdio) and test it

Set `transport: stdio` in `config.yaml`, then:

```bash
python test_client.py
# Available tools: ['query_database', 'search_documentation', 'send_notification']
```

## Connect from Claude Desktop

```json
{
  "mcpServers": {
    "enterprise-mcp": {
      "command": "python",
      "args": ["-m", "app.main"],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "MCP_POSTGRES_CONNECTION": "postgresql://...",
        "MCP_SLACK_WEBHOOK": "https://hooks.slack.com/..."
      }
    }
  }
}
```

## Build the Docker image locally

```bash
docker build -t enterprise-mcp-server .
docker run -p 8000:8000 --env-file .env enterprise-mcp-server
```
