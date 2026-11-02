"""Exercise the restricted APK handler without binding a network socket."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import json
import unittest

from infra.serve_apk import artifact_metadata, handler_for


class MemoryConnection:
    def __init__(self, request):
        self.request = request
        self.output = BytesIO()

    def makefile(self, *args, **kwargs):
        return BytesIO(self.request)

    def sendall(self, data):
        self.output.write(data)


def response_for(apk, path, method="GET"):
    connection = MemoryConnection(f"{method} {path} HTTP/1.0\r\n\r\n".encode("ascii"))
    handler_for(apk)(connection, ("127.0.0.1", 1234), SimpleNamespace())
    headers, body = connection.output.getvalue().split(b"\r\n\r\n", 1)
    return headers.decode("ascii"), body


class ApkDownloadTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory(prefix="street-ceo-apk-handler-")
        self.addCleanup(self.directory.cleanup)
        self.apk = Path(self.directory.name) / "demo.apk"
        self.content = b"synthetic APK fixture\x00\xff"
        self.apk.write_bytes(self.content)

    def test_only_apk_bytes_are_downloaded_with_explicit_mime_and_length(self):
        headers, body = response_for(self.apk, "/street-ceo.apk")
        self.assertIn("200 OK", headers)
        self.assertIn("application/vnd.android.package-archive", headers)
        self.assertIn(f"Content-Length: {len(self.content)}", headers)
        self.assertEqual(self.content, body)

    def test_metadata_hash_and_head_are_repeatable_without_exposing_local_path(self):
        headers, body = response_for(self.apk, "/artifact.json")
        self.assertIn("200 OK", headers)
        metadata = json.loads(body)
        self.assertEqual(sha256(self.content).hexdigest(), metadata["sha256"])
        self.assertEqual(artifact_metadata(self.apk), metadata)
        self.assertNotIn(str(self.apk), body.decode("utf-8"))
        head_headers, head_body = response_for(self.apk, "/street-ceo.apk", "HEAD")
        self.assertIn(f"Content-Length: {len(self.content)}", head_headers)
        self.assertEqual(b"", head_body)

    def test_repository_and_directory_paths_cannot_be_downloaded(self):
        for path in ("/", "/README.md", "/../README.md", "/%2e%2e/.env", "/data/demo-mvp.sqlite3"):
            with self.subTest(path=path):
                headers, body = response_for(self.apk, path)
                self.assertIn("404", headers)
                self.assertNotIn(str(self.directory.name).encode(), body)


if __name__ == "__main__":
    unittest.main()
