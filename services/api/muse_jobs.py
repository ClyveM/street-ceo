"""Durable Ask Muse queue for the single-worker demo runtime."""
import asyncio
import copy
import hashlib
import json
import sqlite3
import time
from contextlib import asynccontextmanager, suppress
from contextvars import ContextVar
from uuid import UUID, uuid4

from fastapi import HTTPException
from starlette.responses import JSONResponse

from services.ai.tracing import SQLiteTraceStore, trace_context


JOB_TTL_SECONDS = 86400
MAX_ATTEMPTS = 2
FAILURE = "Muse couldn't finish this request. Please try again."
EXPIRED = "This Muse request expired. Please ask again."


_progress = ContextVar("muse_job_progress", default=None)
_previous_result = ContextVar("muse_previous_result", default=None)


def muse_previous_result():
    return _previous_result.get()


def report_muse_progress(stage, label):
    callback = _progress.get()
    if callback is not None:
        callback({"stage": stage, "label": label})


class MuseJobs:
    def __init__(self, path, clock=time.time):
        self.connection = sqlite3.connect(path or ":memory:", check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.lock = asyncio.Lock()
        self.wake = asyncio.Event()
        self.clock = clock
        self.progress = {}
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS muse_jobs (
                id TEXT PRIMARY KEY, shop TEXT NOT NULL, key_hash TEXT NOT NULL,
                body_hash TEXT NOT NULL, body TEXT, result TEXT, error TEXT,
                status TEXT NOT NULL DEFAULT 'queued', attempts INTEGER NOT NULL DEFAULT 0,
                created REAL NOT NULL, expires REAL NOT NULL, UNIQUE(shop, key_hash)
            );
            CREATE INDEX IF NOT EXISTS muse_jobs_queue ON muse_jobs(status, created);
            CREATE INDEX IF NOT EXISTS muse_jobs_expiry ON muse_jobs(expires);
        """)

    def expire(self):
        now = self.clock()
        self.connection.execute(
            """UPDATE muse_jobs SET status='expired', body=NULL, result=NULL, error=?
            WHERE expires <= ? AND status <> 'expired'""",
            (EXPIRED, now),
        )
        # Keep the key binding for another day so a late transport retry cannot revive a job.
        self.connection.execute("DELETE FROM muse_jobs WHERE expires <= ?", (now - JOB_TTL_SECONDS,))

    def recover(self):
        with self.connection:
            self.expire()
            self.connection.execute(
                "UPDATE muse_jobs SET status='queued' WHERE status='running' AND attempts < ?",
                (MAX_ATTEMPTS,),
            )
            self.connection.execute(
                """UPDATE muse_jobs SET status='failed', body=NULL, error=?
                WHERE status='running'""",
                (FAILURE,),
            )

    def response(self, row, status_code=200):
        return JSONResponse(
            {"job_id": row["id"], "status": row["status"],
             "result": json.loads(row["result"]) if row["result"] else None, "error": row["error"],
             "progress": self.progress.get(row["id"])},
            status_code=status_code,
            headers={"X-Correlation-ID": row["id"], "Cache-Control": "no-store"},
        )

    def submit(self, shop, key, request):
        if not key or not key.strip() or len(key) > 128:
            raise HTTPException(400, "Idempotency-Key is required and must be at most 128 characters")
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        body = request.model_dump_json()
        body_hash = hashlib.sha256(body.encode()).hexdigest()
        with self.connection:
            self.expire()
            row = self.connection.execute(
                "SELECT * FROM muse_jobs WHERE shop=? AND key_hash=?", (shop, key_hash),
            ).fetchone()
            if row:
                if row["body_hash"] != body_hash:
                    raise HTTPException(409, "Idempotency-Key already used for a different request")
                return self.response(row, 202)
            now = self.clock()
            job_id = str(uuid4())
            self.connection.execute(
                """INSERT INTO muse_jobs (id,shop,key_hash,body_hash,body,created,expires)
                VALUES (?,?,?,?,?,?,?)""",
                (job_id, shop, key_hash, body_hash, body, now, now + JOB_TTL_SECONDS),
            )
            row = self.connection.execute("SELECT * FROM muse_jobs WHERE id=?", (job_id,)).fetchone()
        self.wake.set()
        return self.response(row, 202)

    def read(self, shop, job_id):
        with self.connection:
            self.expire()
            row = self.connection.execute(
                "SELECT * FROM muse_jobs WHERE shop=? AND id=?", (shop, job_id),
            ).fetchone()
        if row is None:
            raise HTTPException(404, "Muse request not found")
        return self.response(row)

    def claim(self):
        with self.connection:
            self.expire()
            row = self.connection.execute(
                "SELECT * FROM muse_jobs WHERE status='queued' ORDER BY created, id LIMIT 1",
            ).fetchone()
            if row:
                self.connection.execute(
                    "UPDATE muse_jobs SET status='running', attempts=attempts+1 WHERE id=?", (row["id"],),
                )
        return row

    def finish(self, job_id, result):
        self.progress.pop(job_id, None)
        status = "succeeded" if result is not None else "failed"
        with self.connection:
            self.expire()
            self.connection.execute(
                """UPDATE muse_jobs SET status=?, body=NULL, result=?, error=?
                WHERE id=? AND status='running'""",
                (status, result, FAILURE if result is None else None, job_id),
            )

    def answer(self, row, request_type, reason, record, previous):
        started = time.monotonic()
        with trace_context(row["id"], shop_id=row["shop"], operation="muse"):
            trace = SQLiteTraceStore()
            try:
                request = request_type.model_validate_json(row["body"])
                trace.record({"phase": "started", "source": "muse_job", "request": request.model_dump()})
                if record is None:
                    raise LookupError("Shop unavailable")
                token = _progress.set(lambda progress: self.progress.__setitem__(row["id"], progress))
                previous_token = _previous_result.set(previous)
                try:
                    result = reason(request, record)
                finally:
                    _previous_result.reset(previous_token)
                    _progress.reset(token)
                trace.record({"phase": "completed", "source": "muse_job", "response": result.model_dump(),
                              "duration_ms": round((time.monotonic() - started) * 1000)})
                return result.model_dump_json()
            except Exception:
                with suppress(Exception):
                    trace.record({"phase": "failed", "source": "muse_job", "error_type": "job_processing_failed",
                                  "duration_ms": round((time.monotonic() - started) * 1000)})
                return None

    async def work(self, store, request_type, reason):
        while True:
            async with self.lock:
                row = self.claim()
                if row is not None:
                    try:
                        record = store.get_shop_record(UUID(row["shop"]))
                        # SQLite commits replace records. The memory adapter mutates them in place.
                        if not hasattr(store, "transaction"):
                            record = copy.deepcopy(record)
                    except (LookupError, RuntimeError):
                        record = None
                else:
                    self.wake.clear()
            if row is None:
                with suppress(asyncio.TimeoutError):
                    await asyncio.wait_for(self.wake.wait(), timeout=60)
                continue
            previous = None
            previous_id = json.loads(row["body"]).get("prior_job_id")
            if previous_id:
                found = self.connection.execute(
                    "SELECT result FROM muse_jobs WHERE id=? AND shop=? AND status='succeeded' AND expires>?",
                    (previous_id, row["shop"], self.clock()),
                ).fetchone()
                if found is not None and found["result"]:
                    prior = json.loads(found["result"])
                    previous = {"title": prior.get("title"), "answer": str(prior.get("answer", ""))[:4000],
                                "evidence_ids": prior.get("evidence_ids", [])[:16]}
            result = await asyncio.to_thread(self.answer, row, request_type, reason, record, previous)
            async with self.lock:
                self.finish(row["id"], result)

    def lifespan(self, store, request_type, reason):
        @asynccontextmanager
        async def lifespan(app):
            self.recover()
            worker = asyncio.create_task(self.work(store, request_type, reason))
            try:
                yield
            finally:
                worker.cancel()
                with suppress(asyncio.CancelledError):
                    await worker

        return lifespan
