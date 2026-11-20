# app/resources.py
#
# Not shown as its own code block in the lesson -- Build Step 8 calls
# `resolve_resource(uri)` from app/server.py's `read_resource` handler but
# never defines it. Written here to actually resolve the two resource
# templates declared in config.yaml.
import re
from typing import Tuple

from app.backends import get_backend

TABLE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


async def resolve_resource(uri: str) -> Tuple[str, str]:
    if uri.startswith("db://tables/"):
        table_name = uri[len("db://tables/"):]
        # Identifiers can't be parameterized by psycopg2 the way values can
        # (cur.execute's params only bind values) -- validate the table name
        # ourselves before interpolating it into the query string.
        if not TABLE_NAME_RE.match(table_name):
            raise ValueError(f"Invalid table name: {table_name}")
        backend = get_backend("postgres")
        content = await backend.execute(
            "query_database",
            {"query": f"SELECT * FROM {table_name} LIMIT 50"},
        )
        return content, "application/json"

    if uri.startswith("docs://"):
        document_id = uri[len("docs://"):]
        backend = get_backend("http")
        content = await backend.execute(
            "search_documentation",
            {"query": document_id, "max_results": 1},
        )
        return content, "text/markdown"

    raise ValueError(f"Unsupported resource URI: {uri}")
