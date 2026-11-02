"""Versioned, transactional local demo store. Run one API worker per file.

Explicit tagged JSON preserves the existing domain models without pickle.
Binary invoice/image assets are committed in the same transaction as state.
"""
from __future__ import annotations

import asyncio
import copy
import json
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import fields
from datetime import date, datetime
from pathlib import Path
from uuid import UUID, uuid4

from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from services.api.app import InMemoryStore, _ShopRecord


class SQLiteStore(InMemoryStore):
    def __init__(self, path: str) -> None:
        super().__init__()
        if path == ":memory:":
            raise ValueError("SQLite demo requires a file-backed database")
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.path), timeout=10, check_same_thread=False)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS demo_schema(version INTEGER NOT NULL);
            INSERT INTO demo_schema SELECT 1 WHERE NOT EXISTS(SELECT 1 FROM demo_schema);
            CREATE TABLE IF NOT EXISTS shop_state(shop_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS shop_assets(asset_id TEXT PRIMARY KEY, content BLOB NOT NULL);
        """)
        self.connection.commit()
        if self.connection.execute("SELECT version FROM demo_schema").fetchone()[0] != 1:
            raise RuntimeError("Unsupported SQLite demo schema version")
        self._models = self._model_registry()
        self._reload()

    @staticmethod
    def _model_registry() -> dict[str, type[BaseModel]]:
        from services.api import app, costs, retail_control, social_data, voice_boundary, paper_sales
        return {f"{value.__module__}.{value.__name__}": value
                for module in (app, costs, retail_control, social_data, voice_boundary, paper_sales)
                for value in vars(module).values()
                if isinstance(value, type) and issubclass(value, BaseModel)}

    def _encode(self, value, assets: dict[str, bytes]):
        if isinstance(value, BaseModel):
            return {"$model": f"{type(value).__module__}.{type(value).__name__}", "value": self._encode(value.model_dump(mode="python"), assets)}
        if isinstance(value, UUID):
            return {"$uuid": str(value)}
        if isinstance(value, datetime):
            return {"$datetime": value.isoformat()}
        if isinstance(value, date):
            return {"$date": value.isoformat()}
        if isinstance(value, bytes):
            asset_id = str(uuid4())
            assets[asset_id] = value
            return {"$blob": asset_id}
        if isinstance(value, dict):
            return {"$dict": [[self._encode(k, assets), self._encode(v, assets)] for k, v in value.items()]}
        if isinstance(value, (list, tuple, set)):
            return {"$" + type(value).__name__: [self._encode(item, assets) for item in value]}
        if value is None or isinstance(value, (str, bool, int, float)):
            return value
        raise TypeError(f"Unsupported persisted value: {type(value).__name__}")

    def _decode(self, value, assets):
        if not isinstance(value, dict):
            return value
        if "$model" in value:
            model = self._models.get(value["$model"])
            if model is None:
                raise RuntimeError("Unknown persisted model")
            return model.model_validate(self._decode(value["value"], assets))
        if "$uuid" in value:
            return UUID(value["$uuid"])
        if "$datetime" in value:
            return datetime.fromisoformat(value["$datetime"])
        if "$date" in value:
            return date.fromisoformat(value["$date"])
        if "$blob" in value:
            return assets[value["$blob"]]
        if "$dict" in value:
            return {self._decode(k, assets): self._decode(v, assets) for k, v in value["$dict"]}
        for kind, factory in (("list", list), ("tuple", tuple), ("set", set)):
            if "$" + kind in value:
                return factory(self._decode(item, assets) for item in value["$" + kind])
        raise RuntimeError("Invalid persisted state encoding")

    def _reload(self) -> None:
        assets = dict(self.connection.execute("SELECT asset_id, content FROM shop_assets"))
        loaded = {}
        for shop_id, payload in self.connection.execute("SELECT shop_id, payload FROM shop_state"):
            values = self._decode(json.loads(payload), assets)
            loaded[UUID(shop_id)] = _ShopRecord(**values)
        self.shops = loaded

    def _save(self) -> None:
        rows, assets = [], {}
        for shop_id, record in self.shops.items():
            values = {field.name: getattr(record, field.name) for field in fields(record)}
            rows.append((str(shop_id), json.dumps(self._encode(values, assets), separators=(",", ":"), allow_nan=False)))
        self.connection.execute("DELETE FROM shop_state")
        self.connection.execute("DELETE FROM shop_assets")
        self.connection.executemany("INSERT INTO shop_state VALUES (?, ?)", rows)
        self.connection.executemany("INSERT INTO shop_assets VALUES (?, ?)", assets.items())

    @contextmanager
    def transaction(self):
        self.connection.execute("BEGIN IMMEDIATE")
        original = self.shops
        try:
            self._reload()
            self.shops = copy.deepcopy(self.shops)
            yield self
            self._save()
            self.connection.commit()
        except BaseException:
            self.connection.rollback()
            self.shops = original
            raise

    def check_ready(self) -> None:
        try:
            self.connection.execute("SELECT version FROM demo_schema").fetchone()
        except sqlite3.Error as exc:
            raise RuntimeError("SQLite database is unavailable") from exc

    def close(self) -> None:
        self.connection.close()


class _RollbackResponse(Exception):
    pass


class SQLiteTransactionMiddleware(BaseHTTPMiddleware):
    """Serializes requests and commits before a successful response is sent."""
    def __init__(self, app, store: SQLiteStore):
        super().__init__(app)
        self.store = store
        self.lock = asyncio.Lock()

    async def dispatch(self, request, call_next):
        from services.ai.tracing import SQLiteTraceStore, trace_context
        paper_extract = '/daily-sales-batches/' in request.url.path and request.url.path.endswith('/extract')
        traced = request.method == "POST" and ("/voice/" in request.url.path or request.url.path.endswith("/muse") or paper_extract)
        correlation_id = str(uuid4())
        operation = request.url.path.rsplit("/", 1)[-1]
        shop_id = request.headers.get("x-shop-id")
        trace_store = None
        started = time.monotonic()
        payload = None
        if traced:
            # Audio is deliberately excluded even before the sanitizer sees it.
            if operation != "audio" and not paper_extract:
                try:
                    payload = await request.json()
                except Exception:
                    payload = {"invalid_json": True}
            try:
                trace_store = SQLiteTraceStore()
                trace_store.record({"correlation_id": correlation_id, "shop_id": shop_id, "operation": operation, "phase": "started", "request": payload, "source": "api"})
            except Exception:
                return JSONResponse({"detail": "Request logging unavailable; no changes were committed"}, status_code=503)
        async with self.lock:
            response = None
            committed = False
            try:
                with trace_context(correlation_id, shop_id=shop_id, operation=operation):
                    with self.store.transaction():
                        response = await call_next(request)
                        if traced:
                            content = b"".join([chunk async for chunk in response.body_iterator])
                            result_payload = json.loads(content)
                            trace_source = result_payload.get("resolution_source") or "api"
                            provider_events = trace_store.read(correlation_id=correlation_id, limit=1000)
                            actual_provider_called = any(event.get("model") and event.get("phase") == "started" for event in provider_events)
                            response = Response(content, status_code=response.status_code, headers=dict(response.headers), background=response.background)
                        if response.status_code >= 400:
                            raise _RollbackResponse()
                        if traced:
                            trace_store.record({"correlation_id": correlation_id, "shop_id": shop_id, "operation": operation, "phase": "response_prepared", "response": json.loads(content), "source": "api"})
                committed = True
                if traced:
                    trace_store.record({"correlation_id": correlation_id, "shop_id": shop_id, "operation": operation, "phase": "completed", "duration_ms": round((time.monotonic() - started) * 1000), "status_code": response.status_code, "response": result_payload, "source": trace_source, "provider_called": actual_provider_called, "resolution_provider_called": result_payload.get("provider_called")})
                    response.headers["X-Correlation-ID"] = correlation_id
                return response
            except _RollbackResponse:
                if traced:
                    try:
                        trace_store.record({"correlation_id": correlation_id, "shop_id": shop_id, "operation": operation, "phase": "failed", "status_code": response.status_code, "response": json.loads(content), "source": "api", "duration_ms": round((time.monotonic() - started) * 1000), "provider_called": actual_provider_called})
                    except Exception:
                        return JSONResponse({"detail": "Request logging unavailable; no changes were committed"}, status_code=503)
                    response.headers["X-Correlation-ID"] = correlation_id
                return response
            except Exception:
                if traced:
                    try:
                        trace_store.record({"correlation_id": correlation_id, "shop_id": shop_id, "operation": operation, "phase": "failed", "error_type": "transaction_or_trace_failure", "source": "api", "duration_ms": round((time.monotonic() - started) * 1000)})
                    except Exception:
                        pass  # Preserve the controlled 503 even when the audit device fails.
                detail = "Receipt logging failed after commit; retry with the same Idempotency-Key" if committed else "SQLite transaction failed; no changes were committed"
                return JSONResponse({"detail": detail}, status_code=503)
