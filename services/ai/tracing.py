"""Bounded, redacted local investigation traces; never a business success log.

Provider traces live in a separate SQLite file so an API transaction cannot
deadlock its own audit writer. A started event is committed before a call;
completion/failure is appended afterward. Incomplete pairs remain inspectable.
"""
from __future__ import annotations

from contextlib import closing, contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sqlite3
from time import perf_counter
from typing import Any, Callable, Iterator, Mapping, Sequence, TypeVar
from uuid import uuid4

_context: ContextVar[dict[str, Any]] = ContextVar("muse_trace_context", default={})
_SENSITIVE = re.compile(r"authorization|cookie|password|passwd|secret|token|api.?key|audio|image_bytes|invoice_bytes|base64", re.I)
_ASSIGNMENT = re.compile(r"(?i)\b(api[_-]?key|(?:access[_-]?)?token|password|secret|authorization)[\"']?\s*[:=]\s*[\"']?[^\s,;\"'&]+")
_BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"(?<!\w)\+\d[\d ()-]{7,}\d(?!\w)")
_DATA = re.compile(r"data:[^\s\"']+", re.I)
T = TypeVar("T")


def sanitize_trace(value: Any, secret_values: Sequence[str] = ()) -> Any:
    """Return bounded JSON data without credentials, binary data or basic PII.

    Each event has a 64KiB payload budget; oversized events retain a safe
    prefix marked truncated, not a misleading complete request/response.
    """
    secrets = tuple(s for s in secret_values if isinstance(s, str) and s)

    def clean(item: Any, depth: int = 0) -> Any:
        if depth > 8:
            return "[depth limit]"
        if item is None or isinstance(item, (bool, int, float)):
            return item
        if isinstance(item, bytes):
            return {"omitted": "binary", "size_bytes": len(item)}
        if isinstance(item, str):
            for secret in secrets:
                item = item.replace(secret, "[redacted]")
            item = _BEARER.sub("Bearer [redacted]", item)
            item = _ASSIGNMENT.sub(lambda match: match.group(1) + "=[redacted]", item)
            item = _EMAIL.sub("[email redacted]", item)
            item = _PHONE.sub("[phone redacted]", item)
            item = _DATA.sub("[data URL omitted]", item)
            return item[:8192] + (" [truncated]" if len(item) > 8192 else "")
        if isinstance(item, Mapping):
            result = {}
            for index, (key, child) in enumerate(item.items()):
                if index == 100:
                    result["_truncated"] = True
                    break
                key = str(key)[:120]
                result[key] = "[redacted]" if _SENSITIVE.search(key) else clean(child, depth + 1)
            return result
        if isinstance(item, (list, tuple, set)):
            values = list(item)
            return [clean(child, depth + 1) for child in values[:100]] + (["[truncated]"] if len(values) > 100 else [])
        # Do not use repr: provider/client objects can contain credentials.
        return {"omitted_type": type(item).__name__}

    sanitized = clean(value)
    encoded = json.dumps(sanitized, ensure_ascii=False, allow_nan=False)
    if len(encoded.encode("utf-8")) > 65536:
        return {"truncated": True, "sanitized_prefix": encoded.encode("utf-8")[:16000].decode("utf-8", errors="ignore")}
    return sanitized


@contextmanager
def trace_context(correlation_id: str, shop_id: str | None = None, operation: str | None = None) -> Iterator[None]:
    context = {"correlation_id": correlation_id[:120], "shop_id": shop_id, "operation": operation}
    token = _context.set(context)
    try:
        yield
    finally:
        _context.reset(token)


class SQLiteTraceStore:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or os.getenv("STREET_CEO_TRACE_DATABASE", "data/muse-traces.sqlite3"))

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("""CREATE TABLE IF NOT EXISTS muse_trace_events (
            event_id TEXT PRIMARY KEY, correlation_id TEXT NOT NULL,
            created_at TEXT NOT NULL, payload TEXT NOT NULL)""")
        connection.execute("CREATE INDEX IF NOT EXISTS ix_muse_trace_correlation ON muse_trace_events(correlation_id)")
        connection.commit()
        return connection

    def record(self, trace: Mapping[str, Any]) -> str:
        context = _context.get()
        event = {"schema_version": 1, **context, **trace,
                 "event_id": str(uuid4()), "created_at": datetime.now(timezone.utc).isoformat()}
        event["correlation_id"] = str(event.get("correlation_id") or uuid4())
        safe = sanitize_trace(event)
        # Keep bounded, sanitized routing metadata outside an oversized body.
        # Investigation endpoints filter by shop_id before returning events;
        # losing it would silently hide the very event needing investigation.
        if safe.get("truncated"):
            envelope = {}
            for name in ("schema_version", "event_id", "created_at", "trace_id", "correlation_id", "shop_id",
                         "operation", "model", "phase", "source", "provider_called", "http_status", "status_code",
                         "error_type", "duration_ms"):
                if name not in event:
                    continue
                value = event[name]
                # Envelope fields are scalar metadata; arbitrary objects must
                # not escape the body sanitizer through a metadata field.
                if not (value is None or isinstance(value, (str, bool, int, float))):
                    value = "[invalid metadata]"
                value = sanitize_trace(value)
                envelope[name] = value[:256] if isinstance(value, str) else value
            safe = {**envelope, "payload": safe}
        with closing(self._connect()) as connection, connection:
            connection.execute("INSERT INTO muse_trace_events VALUES (?, ?, ?, ?)",
                               (event["event_id"], safe["correlation_id"], event["created_at"], json.dumps(safe)))
        return event["event_id"]

    def read(self, correlation_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 1000))
        with closing(self._connect()) as connection:
            if correlation_id is None:
                rows = connection.execute("SELECT payload FROM muse_trace_events ORDER BY rowid DESC LIMIT ?", (limit,))
            else:
                rows = connection.execute("SELECT payload FROM muse_trace_events WHERE correlation_id=? ORDER BY rowid DESC LIMIT ?", (correlation_id, limit))
            return [json.loads(row[0]) for row in rows]


def traced_call(*, operation: str, model: str, request: Any, call: Callable[[], T],
                secret_values: Sequence[str] = (), store: SQLiteTraceStore | None = None) -> T:
    """Persist provider request/result, preserving exceptions and return value.

    Trace write failure is deliberately fatal to this call: an untracked
    provider result must not be presented as a tracked result. Consumers may
    convert this to an explicit unavailable response, but must not commit it.
    """
    store = store or SQLiteTraceStore()
    context = _context.get()
    common = {"trace_id": str(uuid4()), "correlation_id": context.get("correlation_id") or str(uuid4()),
              "operation": operation, "model": model}
    store.record({**common, "phase": "started", "request": sanitize_trace(request, secret_values)})
    started = perf_counter()
    try:
        response = call()
    except Exception as exc:
        error_response = getattr(exc, "response", None)
        payload = None
        if error_response is not None:
            try:
                payload = error_response.json()
            except Exception:
                # Never dump arbitrary HTTP HTML/text or exception strings.
                payload = {"body": "non-JSON error response omitted"}
        store.record({**common, "phase": "failed", "duration_ms": round((perf_counter() - started) * 1000, 3),
                      "error_type": type(exc).__name__, "http_status": getattr(error_response, "status_code", None),
                      "response": sanitize_trace(payload, secret_values)})
        raise
    store.record({**common, "phase": "completed", "duration_ms": round((perf_counter() - started) * 1000, 3),
                  "response": sanitize_trace(response, secret_values)})
    return response
