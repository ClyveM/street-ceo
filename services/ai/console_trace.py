"""Readable, correlated console projection of persisted investigation events."""
from datetime import datetime
import json
import os
import threading

_LOCK = threading.Lock()


def emit_console_trace(event):
    """Best-effort display only; never affects provider/business outcomes.

    JSON escaping prevents speech/provider text from injecting terminal controls.
    Persisted traces remain the authoritative investigation record.
    """
    mode = os.getenv("STREET_CEO_CONSOLE_TRACE", "normal").strip().lower()
    if mode not in {"normal", "detail"}:
        return
    try:
        try:
            from .tracing import sanitize_trace
        except ImportError:  # unittest discovery with services/ai on sys.path
            from tracing import sanitize_trace
        safe = sanitize_trace(event)
        phase = safe.get("phase")
        if phase not in {"started", "completed", "failed"}:
            return
        provider = bool(safe.get("model"))
        correlation = safe.get("correlation_id", "unknown")
        operation = safe.get("operation", "command")
        # Full correlation and provider IDs distinguish interleaved/late results.
        prefix = f"[{datetime.now().astimezone().strftime('%H:%M:%S')}] "
        prefix += json.dumps({"id": correlation, "call": safe.get("trace_id"), "operation": operation}, ensure_ascii=True)
        rows = []
        truncated_payload = safe.get("payload") if isinstance(safe.get("payload"), dict) and safe["payload"].get("truncated") else None
        if truncated_payload:
            rows.append(("PAYLOAD TRUNCATED", {"note": "Oversized event; only a bounded sanitized prefix is available"}))
        request = safe.get("request") or truncated_payload or {}
        response = safe.get("response") or truncated_payload or {}
        if provider:
            label = "MUSE REQUEST" if phase == "started" else "MUSE RESPONSE" if phase == "completed" else "MUSE FAILED"
            summary = {"model": safe.get("model"), "duration_ms": safe.get("duration_ms"),
                       "error": safe.get("error_type"), "http_status": safe.get("http_status")}
            if phase == "completed":
                summary["note"] = "Provider returned; application validation/confirmation still required"
            rows.append((label, summary))
            if mode == "detail":
                rows.append(("PAYLOAD", request if phase == "started" else response))
        elif phase == "started":
            heard = request.get("transcript", request.get("question")) if isinstance(request, dict) else None
            rows.append(("APO RECEIVED", {"heard": heard, "note": "Evaluating locally; Muse used only if needed"}))
            if mode == "detail" and heard is None:
                rows.append(("APP REQUEST", request))
        else:
            response = response if isinstance(response, dict) else {}
            called = safe.get("provider_called")
            route = "MUSE USED" if called else "LOCAL - Muse not called" if called is False else "APP"
            basket = [{"product": line.get("product_name") or line.get("name") or line.get("product_id"),
                       "quantity": line.get("quantity")} for line in response.get("lines", []) if isinstance(line, dict)]
            rows.append((route, {"phase": phase, "source": safe.get("source"),
                        "status": response.get("status"), "http_status": safe.get("status_code"),
                        "duration_ms": safe.get("duration_ms"), "basket": basket,
                        "question": response.get("clarification_question"),
                        "error": response.get("error") or response.get("detail") or safe.get("error_type")}))
            if mode == "detail":
                rows.append(("APP RESPONSE", response))
        block = "\n".join(f"{prefix} {label} | {json.dumps(value, ensure_ascii=True)}" for label, value in rows)
        with _LOCK:
            print(block, flush=True)
    except Exception:
        # A closed terminal or broken console must not turn a valid sale into a failure.
        pass
