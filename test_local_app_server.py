from __future__ import annotations

from contextlib import ExitStack
import json
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch

import backend.api.agent as agent_api
import backend.api.storage as storage_api
import backend.api.xhs as xhs_api
from backend.repositories.knowledge_repo import KnowledgeRepository
from backend.repositories.session_repo import SessionRepository
from backend.services.agent_service import AgentService
from backend.services.retrieval_service import RetrievalService
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
        self.assertEqual(3, payload["storage"]["schemaVersion"])
        self.assertIn("ftsEnabled", payload["storage"])

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
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = StorageRepository(Path(self.temp_dir.name) / "server-test.db")
        self.knowledge_repo = KnowledgeRepository(self.repo)
        self.session_repo = SessionRepository(self.repo)
        self.retrieval_service = RetrievalService(self.knowledge_repo)
        self.patchers = ExitStack()
        self.patchers.enter_context(patch.object(storage_api, "storage", self.repo))
        self.patchers.enter_context(patch.object(agent_api, "storage", self.repo))
        self.patchers.enter_context(patch.object(agent_api, "knowledge_repo", self.knowledge_repo))
        self.patchers.enter_context(patch.object(agent_api, "session_repo", self.session_repo))
        self.patchers.enter_context(patch.object(agent_api, "retrieval_service", self.retrieval_service))
        self.patchers.enter_context(
            patch.object(
                agent_api,
                "agent_service",
                AgentService(
                    storage=self.repo,
                    retrieval_service=self.retrieval_service,
                    llm_service=agent_api.llm_service,
                    session_repo=self.session_repo,
                ),
            )
        )
        self.controller = create_server_controller(0)
        self.controller.start()
        self.port = self.controller.server.server_address[1]
        wait_for_health(f"http://127.0.0.1:{self.port}/api/health", timeout_seconds=5)

    def tearDown(self):
        self.controller.shutdown()
        self.patchers.close()
        self.temp_dir.cleanup()

    def _fetch_json(self, path: str, method: str = "GET", payload: dict | None = None):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(payload).encode("utf-8") if payload is not None else None,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            return json.loads(response.read().decode("utf-8"))

    def test_bootstrap_endpoint_is_available(self):
        payload = self._fetch_json("/api/storage/bootstrap")
        self.assertTrue(payload["ok"])
        self.assertIn("storage", payload)

    def test_agent_classify_endpoint_is_available(self):
        payload = self._fetch_json(
            "/api/agent/classify",
            method="POST",
            payload={"question": "Redis 扣减库存如何保证缓存和数据库一致？"},
        )
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["domain"])
        self.assertTrue(payload["tags"])

    def test_agent_training_start_endpoint_is_available(self):
        payload = self._fetch_json(
            "/api/agent/training/start",
            method="POST",
            payload={
                "goal": {
                    "company": "Demo",
                    "role": "Backend",
                    "mode": "speed",
                    "preferredTopics": ["MySQL", "Redis"],
                },
                "filters": {"company": "Demo", "role": "Backend"},
            },
        )
        self.assertTrue(payload["ok"])
        self.assertEqual("training", payload["mode"])
        self.assertEqual("WAIT_ANSWER", payload["state"])
        self.assertTrue(payload["sessionId"])
        self.assertTrue(payload["activeQuestion"]["prompt"])
        self.assertEqual(2, len(payload["topicProgress"]))

    def test_agent_training_answer_and_advance_flow(self):
        started = self._fetch_json(
            "/api/agent/training/start",
            method="POST",
            payload={
                "goal": {
                    "company": "Demo",
                    "role": "Backend",
                    "mode": "deep",
                    "preferredTopics": ["MySQL"],
                },
                "filters": {"company": "Demo", "role": "Backend"},
            },
        )
        evaluated = self._fetch_json(
            "/api/agent/training/answer",
            method="POST",
            payload={
                "sessionId": started["sessionId"],
                "answer": "我会先从索引结构、最左匹配、范围查询和 explain 排查思路来回答，最后再补充线上优化经验。",
            },
        )
        self.assertTrue(evaluated["ok"])
        self.assertEqual("training", evaluated["mode"])
        self.assertTrue(evaluated["lastEvaluation"])
        self.assertTrue(evaluated["suggestedAction"])

        action = evaluated["availableActions"][0]
        advanced = self._fetch_json(
            "/api/agent/training/advance",
            method="POST",
            payload={"sessionId": started["sessionId"], "action": action},
        )
        self.assertTrue(advanced["ok"])
        self.assertEqual(started["sessionId"], advanced["sessionId"])
        self.assertIn(advanced["state"], {"WAIT_ANSWER", "SUMMARY_READY"})

    def test_storage_posts_endpoints_round_trip(self):
        record = {
            "id": "post-1",
            "title": "MySQL 索引面经",
            "content": "Mysql 索引失效有哪些场景？",
            "company": "Demo",
            "role": "Backend",
        }
        saved = self._fetch_json("/api/storage/posts", method="PUT", payload={"posts": [record]})
        self.assertTrue(saved["ok"])
        self.assertEqual(1, saved["count"])

        listed = self._fetch_json("/api/storage/posts")
        self.assertTrue(listed["ok"])
        self.assertEqual(1, len(listed["posts"]))
        self.assertEqual("post-1", listed["posts"][0]["id"])

    def test_xhs_search_endpoint_is_compatible(self):
        mock_response = {
            "ok": True,
            "query": "mysql",
            "items": [{"noteId": "note-1", "title": "Mock note"}],
            "rawCount": 1,
        }
        with patch.object(xhs_api.xhs_service, "search", return_value=mock_response) as mocked:
            payload = self._fetch_json(
                "/api/xhs/search",
                method="POST",
                payload={"query": "mysql", "cookiesStr": "cookie=value", "page": 1, "pageSize": 10},
            )
        self.assertTrue(payload["ok"])
        self.assertEqual("mysql", payload["query"])
        self.assertEqual(1, len(payload["items"]))
        mocked.assert_called_once()

    def test_xhs_note_detail_endpoint_is_compatible(self):
        mock_response = {
            "ok": True,
            "item": {"noteId": "note-1", "title": "Mock note detail", "detailLoaded": True},
        }
        with patch.object(xhs_api.xhs_service, "detail", return_value=mock_response) as mocked:
            payload = self._fetch_json(
                "/api/xhs/note-detail",
                method="POST",
                payload={"url": "https://www.xiaohongshu.com/explore/mock", "cookiesStr": "cookie=value"},
            )
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["item"]["detailLoaded"])
        mocked.assert_called_once()


if __name__ == "__main__":
    unittest.main()
