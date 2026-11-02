"""Read-only, shop-filtered investigation boundary for the local demo."""
import json
import sqlite3
from contextlib import closing

from services.ai.tracing import SQLiteTraceStore, sanitize_trace


def read_shop_traces(shop_id: str, limit: int = 20, correlation_id: str | None = None) -> list[dict]:
    path = SQLiteTraceStore().path.resolve()
    if not path.exists():
        return []
    limit = max(1, min(int(limit), 100))
    query = "SELECT payload FROM muse_trace_events WHERE json_extract(payload, '$.shop_id') = ?"
    parameters: list = [shop_id]
    if correlation_id is not None:
        query += " AND correlation_id = ?"
        parameters.append(correlation_id)
    query += " ORDER BY rowid DESC LIMIT ?"
    parameters.append(limit)
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)) as connection:
        rows = connection.execute(query, parameters).fetchall()
    # Defense in depth: sanitize again and never return global/other-shop events.
    return [sanitize_trace(item) for row in rows if isinstance(item := json.loads(row[0]), dict) and item.get("shop_id") == shop_id]
