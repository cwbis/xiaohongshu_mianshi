from __future__ import annotations

import json
import tempfile
import unittest
import urllib.request
from pathlib import Path

from desktop_launcher import wait_for_health
from local_app_server import StorageRepository, create_server_controller


class StorageRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = StorageRepository(Path(self.temp_dir.name) / "test.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_replace_posts_dedupes_by_note_id_and_source_url(self):
        stored = self.repo.replace_posts(
            [
                {"id": "1", "noteId": "note-a", "title": "A1", "sourceUrl": "", "content": "x"},
                {"id": "2", "noteId": "note-a", "title": "A2", "sourceUrl": "", "content": "y"},
                {"id": "3", "title": "B1", "sourceUrl": "https://example.com/post", "content": "z"},
                {"id": "4", "title": "B2", "sourceUrl": "https://example.com/post", "content": "w"},
            ]
        )
        self.assertEqual(2, len(stored))
        titles = {item["title"] for item in stored}
        self.assertEqual({"A2", "B2"}, titles)

    def test_bootstrap_payload_contains_settings_and_storage_meta(self):
        self.repo.set_setting("xhsConfig", {"query": "offer"})
        payload = self.repo.bootstrap_payload()
        self.assertIn("storage", payload)
        self.assertEqual("offer", payload["settings"]["xhsConfig"]["query"])
        self.assertEqual(1, payload["storage"]["schemaVersion"])

    def test_import_legacy_marks_migration_complete(self):
        result = self.repo.import_legacy_payload(
            {
                "posts": [{"id": "1", "title": "Legacy", "content": "body"}],
                "llmConfig": {"model": "demo-model"},
            }
        )
        self.assertEqual(1, result["postsImported"])
        self.assertIn("llmConfig", result["settingsImported"])
        self.assertTrue(result["storage"]["legacyImportCompleted"])


class LocalServerApiTests(unittest.TestCase):
    def setUp(self):
        self.controller = create_server_controller(0)
        self.controller.start()
        self.port = self.controller.server.server_address[1]
        wait_for_health(f"http://127.0.0.1:{self.port}/api/health", timeout_seconds=5)

    def tearDown(self):
        self.controller.shutdown()

    def test_bootstrap_endpoint_is_available(self):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/api/storage/bootstrap", timeout=2) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self.assertTrue(payload["ok"])
        self.assertIn("storage", payload)


if __name__ == "__main__":
    unittest.main()
