"""Serve exactly one built APK; no repository files or directory listings."""
from __future__ import annotations

import argparse
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from shutil import copyfileobj
from urllib.parse import urlsplit


def artifact_metadata(apk: Path) -> dict:
    digest = sha256()
    with apk.open("rb") as stream:
        size = os.fstat(stream.fileno()).st_size
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"service": "street-ceo-apk-only", "filename": "street-ceo.apk",
            "size_bytes": size, "sha256": digest.hexdigest()}


def handler_for(apk: Path):
    class ApkHandler(BaseHTTPRequestHandler):
        def do_HEAD(self):
            self._serve(head_only=True)

        def do_GET(self):
            self._serve(head_only=False)

        def _serve(self, head_only):
            route = urlsplit(self.path).path
            if route not in {"/street-ceo.apk", "/artifact.json"}:
                self.send_error(404, "Only the demo APK is available")
                return
            try:
                if route == "/artifact.json":
                    data = json.dumps(artifact_metadata(apk)).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    if not head_only:
                        self.wfile.write(data)
                    return
                with apk.open("rb") as stream:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/vnd.android.package-archive")
                    self.send_header("Content-Disposition", 'attachment; filename="street-ceo.apk"')
                    self.send_header("Content-Length", str(os.fstat(stream.fileno()).st_size))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    if not head_only:
                        copyfileobj(stream, self.wfile)
            except OSError:
                self.send_error(503, "APK is unavailable; rebuild and retry")

        def log_message(self, format, *args):
            # Never log arbitrary request paths/headers from a phone.
            pass

    return ApkHandler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apk", required=True, type=Path)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8081, type=int)
    parser.add_argument("--check", action="store_true", help="Validate artifact without opening a listener")
    args = parser.parse_args()
    apk = args.apk.resolve(strict=True)
    if not apk.is_file() or apk.suffix.lower() != ".apk":
        parser.error("--apk must point to a built .apk file")
    if not 1024 <= args.port <= 65535:
        parser.error("--port must be between 1024 and 65535")
    print(json.dumps(artifact_metadata(apk)), flush=True)
    if not args.check:
        with ThreadingHTTPServer((args.host, args.port), handler_for(apk)) as server:
            server.serve_forever()


if __name__ == "__main__":
    main()
