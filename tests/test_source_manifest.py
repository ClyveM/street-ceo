"""Keep build inputs while excluding generated/private local artifacts."""
import unittest

from infra.check_source_manifest import REQUIRED, forbidden


class SourceManifestTests(unittest.TestCase):
    def test_required_wrapper_locks_and_assets_are_not_forbidden(self):
        for path in REQUIRED:
            self.assertFalse(forbidden(path), path)

    def test_private_and_generated_paths_are_rejected(self):
        for path in [".env", "nested/.env.production", ".codex-remote-attachments/photo.png",
                     ".pytest-test/traces.sqlite3", "apps/web/tsconfig.tsbuildinfo",
                     "apps/web/local-office/src/OfficeApp.tsx", "data/output.log",
                     "data/private-attachment.png",
                     "services/api/local_team.py", "services/api/test_project_office.py",
                     "apps/android/android/local.properties", "apps/android/android/.gradle/state.bin",
                     "apps/android/web-assets/index.html", "apps/android/android/app/build/app.apk",
                     "certificates/release.jks", "apps/web/node_modules/dependency/index.js"]:
            self.assertTrue(forbidden(path), path)
