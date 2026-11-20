# app/backends.py
import httpx
import json
from typing import Dict, Any

from app.validation import validate_sql_query


class PostgresBackend:
    def __init__(self, connection_string: str):
        import psycopg2
        self.conn = psycopg2.connect(connection_string)

    async def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        query = args["query"]
        # Wires in the Deploy lesson's own validate_sql_query() -- shown
        # there as standalone hardening code but never actually called from
        # the query_database tool path. Without this, Step 2's "Input
        # Validation" section does nothing.
        if not validate_sql_query(query):
            raise ValueError("Query rejected: contains a blocked SQL pattern")
        params = args.get("params", [])
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                columns = [desc[0] for desc in cur.description]
                rows = [dict(zip(columns, row)) for row in cur.fetchall()]
                return json.dumps(rows, default=str)
            self.conn.commit()
            return json.dumps({"affected_rows": cur.rowcount})


class HttpBackend:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/search",
                json=args,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10
            )
            response.raise_for_status()
            return json.dumps(response.json(), indent=2)


class NotificationBackend:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def execute(self, tool_name: str, args: Dict[str, Any]) -> str:
        payload = {
            "text": f"[{args.get('priority', 'info').upper()}] {args['message']}",
            "channel": args["channel"]
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.webhook_url, json=payload, timeout=5)
            return json.dumps({"sent": response.status_code == 200})


_backends = {}


def get_backend(backend_type: str):
    if backend_type not in _backends:
        env_key = f"MCP_{backend_type.upper()}_CONNECTION"
        import os
        conn_str = os.environ.get(env_key, "")

        if backend_type == "postgres":
            _backends[backend_type] = PostgresBackend(conn_str)
        elif backend_type == "http":
            _backends[backend_type] = HttpBackend(
                os.environ.get("MCP_API_BASE_URL", "http://localhost:8080"),
                os.environ.get("MCP_API_KEY", "")
            )
        elif backend_type == "notify":
            _backends[backend_type] = NotificationBackend(
                os.environ.get("MCP_SLACK_WEBHOOK", "")
            )
    return _backends[backend_type]
