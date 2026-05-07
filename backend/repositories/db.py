from __future__ import annotations

import json
import re
import sqlite3
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from backend.config import DB_PATH, SCHEMA_VERSION, SUPPORTED_SETTING_SCOPES
from backend.errors import ApiError


QUESTION_PATTERN = re.compile(r"[?？]|怎么|如何|为什么|区别|原理|设计|保证|实现|限流|一致性")


def normalize_text(value, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def nested_get(data, *keys):
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list) and isinstance(key, int) and 0 <= key < len(current):
            current = current[key]
        else:
            return None
    return current


def first_non_empty(*values):
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def normalize_post_record(record: dict) -> dict:
    if not isinstance(record, dict):
        raise ApiError("Post record must be an object.")
    normalized = dict(record)
    normalized["id"] = str(normalized.get("id") or f"post-{uuid.uuid4().hex}")
    normalized["title"] = normalize_text(normalized.get("title"), "未命名帖子")
    normalized["author"] = normalize_text(normalized.get("author"))
    normalized["publishTime"] = normalize_text(normalized.get("publishTime"))
    normalized["sourceUrl"] = normalize_text(normalized.get("sourceUrl"))
    normalized["content"] = normalize_text(normalized.get("content"))
    normalized["excerpt"] = normalize_text(normalized.get("excerpt"), normalized["content"][:180])
    normalized["company"] = normalize_text(normalized.get("company"))
    normalized["role"] = normalize_text(normalized.get("role"))
    normalized["keyword"] = normalize_text(normalized.get("keyword"))
    normalized["noteId"] = normalize_text(normalized.get("noteId"))
    normalized["coverUrl"] = normalize_text(normalized.get("coverUrl"))
    normalized["collectedAt"] = normalize_text(normalized.get("collectedAt"), time.strftime("%Y-%m-%dT%H:%M:%S"))
    return normalized


def post_identity(record: dict) -> str:
    if record.get("noteId"):
        return f"note:{record['noteId']}"
    if record.get("sourceUrl"):
        return f"url:{record['sourceUrl']}"
    return f"id:{record['id']}"


def dedupe_post_records(records: list[dict]) -> list[dict]:
    ordered: dict[str, dict] = {}
    for raw_record in records:
        record = normalize_post_record(raw_record)
        identity = post_identity(record)
        current = ordered.get(identity)
        if current:
            ordered[identity] = {
                **current,
                **record,
                "id": current.get("id") or record["id"],
                "noteId": record.get("noteId") or current.get("noteId") or "",
                "sourceUrl": record.get("sourceUrl") or current.get("sourceUrl") or "",
            }
        else:
            ordered[identity] = record
    return sorted(ordered.values(), key=lambda item: item.get("collectedAt") or "", reverse=True)


def validate_posts_payload(payload: dict) -> list[dict]:
    items = payload.get("posts")
    if not isinstance(items, list):
        raise ApiError("Field 'posts' must be an array.")
    return items


def validate_setting_scope(scope: str) -> str:
    if scope not in SUPPORTED_SETTING_SCOPES:
        raise ApiError(f"Unsupported settings scope: {scope}")
    return scope


def validate_setting_value(payload: dict) -> dict:
    value = payload.get("value")
    if not isinstance(value, dict):
        raise ApiError("Field 'value' must be an object.")
    return value


def extract_questions_from_post(record: dict) -> list[str]:
    lines = []
    body = normalize_text(record.get("content") or record.get("excerpt"))
    for raw_line in re.split(r"\n+", body):
        line = normalize_text(re.sub(r"^\d+[.、]\s*", "", raw_line))
        if not line:
            continue
        if QUESTION_PATTERN.search(line):
            lines.append(line)
    return lines[:8]


class StorageRepository:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._fts_enabled = True
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS posts (
                    id TEXT PRIMARY KEY,
                    note_id TEXT,
                    source_url TEXT,
                    title TEXT NOT NULL,
                    publish_time TEXT,
                    collected_at TEXT,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_note_id
                    ON posts(note_id)
                    WHERE note_id IS NOT NULL AND note_id != '';
                CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_source_url
                    ON posts(source_url)
                    WHERE source_url IS NOT NULL AND source_url != '';

                CREATE TABLE IF NOT EXISTS settings (
                    scope TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS meta (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS questions (
                    id TEXT PRIMARY KEY,
                    post_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    source_title TEXT NOT NULL,
                    company TEXT NOT NULL DEFAULT '',
                    role TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS knowledge_points (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    parent TEXT NOT NULL DEFAULT '',
                    aliases_json TEXT NOT NULL DEFAULT '[]',
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS agent_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    question TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'qa',
                    state TEXT NOT NULL DEFAULT '',
                    domain TEXT NOT NULL DEFAULT '',
                    tags_json TEXT NOT NULL DEFAULT '[]',
                    answer_json TEXT NOT NULL DEFAULT '{}',
                    filters_json TEXT NOT NULL DEFAULT '{}',
                    sources_json TEXT NOT NULL DEFAULT '[]',
                    goal_json TEXT NOT NULL DEFAULT '{}',
                    active_question_json TEXT NOT NULL DEFAULT '{}',
                    topic_progress_json TEXT NOT NULL DEFAULT '[]',
                    review_summary_json TEXT NOT NULL DEFAULT '{}',
                    last_evaluation_json TEXT NOT NULL DEFAULT '{}',
                    suggested_action TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS agent_messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_agent_messages_session
                    ON agent_messages(session_id, created_at);

                CREATE TABLE IF NOT EXISTS agent_attempts (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    topic TEXT NOT NULL DEFAULT '',
                    question TEXT NOT NULL DEFAULT '',
                    answer_text TEXT NOT NULL DEFAULT '',
                    evaluation_json TEXT NOT NULL DEFAULT '{}',
                    next_action TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_agent_attempts_session
                    ON agent_attempts(session_id, created_at);
                """
            )
            try:
                connection.executescript(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS posts_fts USING fts5(
                        post_id UNINDEXED,
                        title,
                        content,
                        excerpt,
                        company,
                        role
                    );
                    CREATE VIRTUAL TABLE IF NOT EXISTS questions_fts USING fts5(
                        question_id UNINDEXED,
                        text,
                        source_title,
                        company,
                        role
                    );
                    CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_points_fts USING fts5(
                        point_id UNINDEXED,
                        name,
                        parent,
                        aliases,
                        description
                    );
                    """
                )
                self._fts_enabled = True
            except sqlite3.OperationalError as error:
                self._fts_enabled = False
                print(f"SQLite FTS5 不可用，已降级为关键词检索：{error}", file=sys.stderr)
            self._ensure_agent_training_schema(connection)
        self.set_meta("schemaVersion", SCHEMA_VERSION)
        if self.get_meta("legacyImportCompleted") is None:
            self.set_meta("legacyImportCompleted", False)
        self._seed_knowledge_points()
        self._rebuild_derived_indexes()

    def _ensure_agent_training_schema(self, connection: sqlite3.Connection) -> None:
        existing_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(agent_sessions)").fetchall()
        }
        required_columns = {
            "mode": "TEXT NOT NULL DEFAULT 'qa'",
            "state": "TEXT NOT NULL DEFAULT ''",
            "goal_json": "TEXT NOT NULL DEFAULT '{}'",
            "active_question_json": "TEXT NOT NULL DEFAULT '{}'",
            "topic_progress_json": "TEXT NOT NULL DEFAULT '[]'",
            "review_summary_json": "TEXT NOT NULL DEFAULT '{}'",
            "last_evaluation_json": "TEXT NOT NULL DEFAULT '{}'",
            "suggested_action": "TEXT NOT NULL DEFAULT ''",
        }
        for column_name, definition in required_columns.items():
            if column_name not in existing_columns:
                connection.execute(f"ALTER TABLE agent_sessions ADD COLUMN {column_name} {definition}")

    def get_meta(self, key: str):
        with self._connect() as connection:
            row = connection.execute("SELECT value_json FROM meta WHERE key = ?", (key,)).fetchone()
        return json.loads(row["value_json"]) if row else None

    def set_meta(self, key: str, value) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO meta(key, value_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json, updated_at = CURRENT_TIMESTAMP
                """,
                (key, payload),
            )
            connection.commit()

    def list_posts(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM posts ORDER BY COALESCE(collected_at, '') DESC, updated_at DESC"
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def replace_posts(self, records: list[dict]) -> list[dict]:
        normalized = dedupe_post_records(records)
        with self._lock:
            with self._connect() as connection:
                connection.execute("DELETE FROM posts")
                for record in normalized:
                    connection.execute(
                        """
                        INSERT INTO posts(id, note_id, source_url, title, publish_time, collected_at, payload_json, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """,
                        (
                            record["id"],
                            record.get("noteId") or None,
                            record.get("sourceUrl") or None,
                            record.get("title") or "Untitled Post",
                            record.get("publishTime") or "",
                            record.get("collectedAt") or "",
                            json.dumps(record, ensure_ascii=False),
                        ),
                    )
                connection.commit()
            self._rebuild_derived_indexes()
        return normalized

    def merge_posts(self, records: list[dict]) -> list[dict]:
        merged = dedupe_post_records(self.list_posts() + records)
        return self.replace_posts(merged)

    def get_settings(self) -> dict:
        with self._connect() as connection:
            rows = connection.execute("SELECT scope, value_json FROM settings").fetchall()
        return {row["scope"]: json.loads(row["value_json"]) for row in rows}

    def get_setting(self, scope: str, fallback=None):
        with self._connect() as connection:
            row = connection.execute("SELECT value_json FROM settings WHERE scope = ?", (scope,)).fetchone()
        return json.loads(row["value_json"]) if row else fallback

    def set_setting(self, scope: str, value: dict):
        payload = json.dumps(value, ensure_ascii=False)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO settings(scope, value_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(scope) DO UPDATE SET value_json = excluded.value_json, updated_at = CURRENT_TIMESTAMP
                """,
                (scope, payload),
            )
            connection.commit()
        return value

    def bootstrap_payload(self) -> dict:
        posts = self.list_posts()
        settings = self.get_settings()
        return {
            "posts": posts,
            "settings": settings,
            "storage": {
                "dbPath": str(self.db_path),
                "schemaVersion": self.get_meta("schemaVersion") or SCHEMA_VERSION,
                "legacyImportCompleted": bool(self.get_meta("legacyImportCompleted")),
                "postCount": len(posts),
                "settingsScopes": sorted(settings.keys()),
                "ftsEnabled": self._fts_enabled,
            },
        }

    def import_legacy_payload(self, payload: dict) -> dict:
        posts = payload.get("posts") or []
        merged_posts = self.merge_posts(posts) if posts else self.list_posts()
        imported_scopes: list[str] = []
        for scope in SUPPORTED_SETTING_SCOPES:
            if scope in payload and isinstance(payload[scope], dict):
                self.set_setting(scope, payload[scope])
                imported_scopes.append(scope)
        self.set_meta("legacyImportCompleted", True)
        return {
            "postsImported": len(merged_posts),
            "settingsImported": imported_scopes,
            "storage": self.bootstrap_payload()["storage"],
        }

    def _seed_knowledge_points(self) -> None:
        points = [
            ("kp-redis-consistency", "缓存一致性", "Redis", ["延迟双删", "双写一致性", "cache consistency"], "缓存与数据库一致性问题。"),
            ("kp-high-concurrency", "高并发", "系统设计", ["秒杀", "削峰", "高吞吐"], "高并发场景下的系统设计与稳定性。"),
            ("kp-distributed-transaction", "分布式事务", "系统设计", ["2PC", "TCC", "SAGA"], "跨服务事务一致性。"),
            ("kp-rate-limit", "限流", "系统设计", ["令牌桶", "滑动窗口", "漏桶"], "流量控制与服务保护。"),
            ("kp-mq-reliability", "消息可靠性", "MQ", ["Kafka", "RabbitMQ", "重复消费"], "消息丢失、重复、顺序等问题。"),
            ("kp-mysql-transaction", "事务与索引", "MySQL", ["索引", "隔离级别", "回表"], "MySQL 核心能力与事务。"),
        ]
        with self._connect() as connection:
            for point_id, name, parent, aliases, description in points:
                connection.execute(
                    """
                    INSERT INTO knowledge_points(id, name, parent, aliases_json, description, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        parent = excluded.parent,
                        aliases_json = excluded.aliases_json,
                        description = excluded.description,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (point_id, name, parent, json.dumps(aliases, ensure_ascii=False), description),
                )
            connection.commit()
        self._refresh_knowledge_fts()

    def _rebuild_derived_indexes(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM questions")
            if self._fts_enabled:
                connection.execute("DELETE FROM posts_fts")
                connection.execute("DELETE FROM questions_fts")
            rows = connection.execute("SELECT payload_json FROM posts").fetchall()
            for row in rows:
                post = json.loads(row["payload_json"])
                if self._fts_enabled:
                    connection.execute(
                        """
                        INSERT INTO posts_fts(post_id, title, content, excerpt, company, role)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            post.get("id", ""),
                            post.get("title", ""),
                            post.get("content", ""),
                            post.get("excerpt", ""),
                            post.get("company", ""),
                            post.get("role", ""),
                        ),
                    )
                for question_text in extract_questions_from_post(post):
                    question_id = f"q-{uuid.uuid4().hex}"
                    connection.execute(
                        """
                        INSERT INTO questions(id, post_id, text, source_title, company, role)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            question_id,
                            post.get("id", ""),
                            question_text,
                            post.get("title", ""),
                            post.get("company", ""),
                            post.get("role", ""),
                        ),
                    )
                    if self._fts_enabled:
                        connection.execute(
                            """
                            INSERT INTO questions_fts(question_id, text, source_title, company, role)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                question_id,
                                question_text,
                                post.get("title", ""),
                                post.get("company", ""),
                                post.get("role", ""),
                            ),
                        )
            connection.commit()
        self._refresh_knowledge_fts()

    def _refresh_knowledge_fts(self) -> None:
        if not self._fts_enabled:
            return
        with self._connect() as connection:
            connection.execute("DELETE FROM knowledge_points_fts")
            rows = connection.execute("SELECT * FROM knowledge_points").fetchall()
            for row in rows:
                aliases = json.loads(row["aliases_json"] or "[]")
                connection.execute(
                    """
                    INSERT INTO knowledge_points_fts(point_id, name, parent, aliases, description)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (row["id"], row["name"], row["parent"], " ".join(aliases), row["description"]),
                )
            connection.commit()

    def search_context(self, query: str, filters: Optional[dict] = None, limit: int = 5) -> List[dict]:
        filters = filters or {}
        company = normalize_text(filters.get("company"))
        role = normalize_text(filters.get("role"))
        query = normalize_text(query)
        sources: list[dict] = []
        with self._connect() as connection:
            if self._fts_enabled and query:
                post_rows = connection.execute(
                    """
                    SELECT p.payload_json, bm25(posts_fts) AS score
                    FROM posts_fts
                    JOIN posts p ON p.id = posts_fts.post_id
                    WHERE posts_fts MATCH ?
                    ORDER BY score
                    LIMIT ?
                    """,
                    (query, limit),
                ).fetchall()
                question_rows = connection.execute(
                    """
                    SELECT q.*, bm25(questions_fts) AS score
                    FROM questions_fts
                    JOIN questions q ON q.id = questions_fts.question_id
                    WHERE questions_fts MATCH ?
                    ORDER BY score
                    LIMIT ?
                    """,
                    (query, limit),
                ).fetchall()
                knowledge_rows = connection.execute(
                    """
                    SELECT kp.*, bm25(knowledge_points_fts) AS score
                    FROM knowledge_points_fts
                    JOIN knowledge_points kp ON kp.id = knowledge_points_fts.point_id
                    WHERE knowledge_points_fts MATCH ?
                    ORDER BY score
                    LIMIT ?
                    """,
                    (query, limit),
                ).fetchall()
            else:
                like = f"%{query}%"
                post_rows = connection.execute(
                    """
                    SELECT payload_json, 1.0 AS score
                    FROM posts
                    WHERE title LIKE ? OR payload_json LIKE ?
                    LIMIT ?
                    """,
                    (like, like, limit),
                ).fetchall()
                question_rows = connection.execute(
                    """
                    SELECT *, 1.0 AS score
                    FROM questions
                    WHERE text LIKE ? OR source_title LIKE ?
                    LIMIT ?
                    """,
                    (like, like, limit),
                ).fetchall()
                knowledge_rows = connection.execute(
                    """
                    SELECT *, 1.0 AS score
                    FROM knowledge_points
                    WHERE name LIKE ? OR description LIKE ?
                    LIMIT ?
                    """,
                    (like, like, limit),
                ).fetchall()
            for row in post_rows:
                post = json.loads(row["payload_json"])
                if company and post.get("company") != company:
                    continue
                if role and post.get("role") != role:
                    continue
                sources.append(
                    {
                        "type": "post",
                        "id": post.get("id", ""),
                        "title": post.get("title", "未命名帖子"),
                        "summary": normalize_text(post.get("excerpt") or post.get("content"))[:180],
                        "company": post.get("company", ""),
                        "role": post.get("role", ""),
                        "score": float(row["score"] or 0.0),
                        "reason": "帖子内容匹配当前问题",
                    }
                )
            for row in question_rows:
                if company and row["company"] != company:
                    continue
                if role and row["role"] != role:
                    continue
                sources.append(
                    {
                        "type": "question",
                        "id": row["id"],
                        "title": row["text"],
                        "summary": row["source_title"],
                        "company": row["company"],
                        "role": row["role"],
                        "score": float(row["score"] or 0.0),
                        "reason": "面试题抽取结果匹配当前问题",
                    }
                )
            for row in knowledge_rows:
                sources.append(
                    {
                        "type": "knowledge",
                        "id": row["id"],
                        "title": row["name"],
                        "summary": row["description"],
                        "company": "",
                        "role": "",
                        "score": float(row["score"] or 0.0),
                        "reason": "知识点库命中当前问题",
                    }
                )
        unique: dict[tuple[str, str], dict] = {}
        for item in sources:
            unique[(item["type"], item["id"])] = item
        ordered = sorted(unique.values(), key=lambda item: item["score"])
        return ordered[:limit]

    def _hydrate_session_summary(self, row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "title": row["title"],
            "question": row["question"],
            "mode": row["mode"] or "qa",
            "state": row["state"] or "",
            "domain": row["domain"],
            "tags": json.loads(row["tags_json"] or "[]"),
            "goal": json.loads(row["goal_json"] or "{}"),
            "updatedAt": row["updated_at"],
        }

    def _hydrate_attempt(self, row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "topic": row["topic"],
            "question": row["question"],
            "answer": row["answer_text"],
            "evaluation": json.loads(row["evaluation_json"] or "{}"),
            "nextAction": row["next_action"] or "",
            "createdAt": row["created_at"],
        }

    def create_session(
        self,
        *,
        question: str,
        domain: str,
        tags: list[str],
        answer_payload: dict,
        filters: dict,
        sources: list[dict],
    ) -> str:
        session_id = f"session-{uuid.uuid4().hex}"
        title = question[:60]
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO agent_sessions(
                    id, title, question, mode, state, domain, tags_json, answer_json, filters_json, sources_json
                )
                VALUES (?, ?, ?, 'qa', 'ANSWER_READY', ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    title,
                    question,
                    domain,
                    json.dumps(tags, ensure_ascii=False),
                    json.dumps(answer_payload, ensure_ascii=False),
                    json.dumps(filters, ensure_ascii=False),
                    json.dumps(sources, ensure_ascii=False),
                ),
            )
            connection.execute(
                "INSERT INTO agent_messages(id, session_id, role, content_json) VALUES (?, ?, ?, ?)",
                (f"msg-{uuid.uuid4().hex}", session_id, "user", json.dumps({"question": question}, ensure_ascii=False)),
            )
            connection.execute(
                "INSERT INTO agent_messages(id, session_id, role, content_json) VALUES (?, ?, ?, ?)",
                (f"msg-{uuid.uuid4().hex}", session_id, "assistant", json.dumps(answer_payload, ensure_ascii=False)),
            )
            connection.commit()
        return session_id

    def create_training_session(
        self,
        *,
        title: str,
        question: str,
        goal: dict,
        filters: dict,
        active_question: dict,
        topic_progress: list[dict],
        sources: list[dict],
    ) -> str:
        session_id = f"session-{uuid.uuid4().hex}"
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO agent_sessions(
                    id, title, question, mode, state, domain, tags_json, answer_json, filters_json, sources_json,
                    goal_json, active_question_json, topic_progress_json
                )
                VALUES (?, ?, ?, 'training', 'WAIT_ANSWER', '', '[]', '{}', ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    title,
                    question,
                    json.dumps(filters, ensure_ascii=False),
                    json.dumps(sources, ensure_ascii=False),
                    json.dumps(goal, ensure_ascii=False),
                    json.dumps(active_question, ensure_ascii=False),
                    json.dumps(topic_progress, ensure_ascii=False),
                ),
            )
            connection.execute(
                "INSERT INTO agent_messages(id, session_id, role, content_json) VALUES (?, ?, ?, ?)",
                (
                    f"msg-{uuid.uuid4().hex}",
                    session_id,
                    "system",
                    json.dumps({"event": "goal_set", "goal": goal, "question": question}, ensure_ascii=False),
                ),
            )
            connection.commit()
        return session_id

    def append_session_messages(self, session_id: str, question: str, answer_payload: dict) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO agent_messages(id, session_id, role, content_json) VALUES (?, ?, ?, ?)",
                (f"msg-{uuid.uuid4().hex}", session_id, "user", json.dumps({"question": question}, ensure_ascii=False)),
            )
            connection.execute(
                "INSERT INTO agent_messages(id, session_id, role, content_json) VALUES (?, ?, ?, ?)",
                (f"msg-{uuid.uuid4().hex}", session_id, "assistant", json.dumps(answer_payload, ensure_ascii=False)),
            )
            connection.execute(
                """
                UPDATE agent_sessions
                SET answer_json = ?, state = 'ANSWER_READY', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (json.dumps(answer_payload, ensure_ascii=False), session_id),
            )
            connection.commit()

    def record_training_attempt(
        self,
        session_id: str,
        *,
        topic: str,
        question: str,
        answer: str,
        evaluation: dict,
        next_action: str,
    ) -> None:
        with self._connect() as connection:
            attempt_id = f"attempt-{uuid.uuid4().hex}"
            connection.execute(
                """
                INSERT INTO agent_attempts(id, session_id, topic, question, answer_text, evaluation_json, next_action)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt_id,
                    session_id,
                    topic,
                    question,
                    answer,
                    json.dumps(evaluation, ensure_ascii=False),
                    next_action,
                ),
            )
            connection.execute(
                "INSERT INTO agent_messages(id, session_id, role, content_json) VALUES (?, ?, ?, ?)",
                (
                    f"msg-{uuid.uuid4().hex}",
                    session_id,
                    "user",
                    json.dumps({"answer": answer, "topic": topic, "question": question}, ensure_ascii=False),
                ),
            )
            connection.execute(
                "INSERT INTO agent_messages(id, session_id, role, content_json) VALUES (?, ?, ?, ?)",
                (
                    f"msg-{uuid.uuid4().hex}",
                    session_id,
                    "coach",
                    json.dumps({"evaluation": evaluation, "nextAction": next_action}, ensure_ascii=False),
                ),
            )
            connection.commit()

    def update_training_session(
        self,
        session_id: str,
        *,
        state: str,
        question: Optional[str] = None,
        filters: Optional[dict] = None,
        sources: Optional[list[dict]] = None,
        active_question: Optional[dict] = None,
        topic_progress: Optional[list[dict]] = None,
        review_summary: Optional[dict] = None,
        last_evaluation: Optional[dict] = None,
        suggested_action: Optional[str] = None,
    ) -> None:
        assignments = ["state = ?", "updated_at = CURRENT_TIMESTAMP"]
        values: list = [state]
        if question is not None:
            assignments.append("question = ?")
            values.append(question)
        if filters is not None:
            assignments.append("filters_json = ?")
            values.append(json.dumps(filters, ensure_ascii=False))
        if sources is not None:
            assignments.append("sources_json = ?")
            values.append(json.dumps(sources, ensure_ascii=False))
        if active_question is not None:
            assignments.append("active_question_json = ?")
            values.append(json.dumps(active_question, ensure_ascii=False))
        if topic_progress is not None:
            assignments.append("topic_progress_json = ?")
            values.append(json.dumps(topic_progress, ensure_ascii=False))
        if review_summary is not None:
            assignments.append("review_summary_json = ?")
            values.append(json.dumps(review_summary, ensure_ascii=False))
        if last_evaluation is not None:
            assignments.append("last_evaluation_json = ?")
            values.append(json.dumps(last_evaluation, ensure_ascii=False))
        if suggested_action is not None:
            assignments.append("suggested_action = ?")
            values.append(suggested_action)
        values.append(session_id)
        with self._connect() as connection:
            connection.execute(
                f"UPDATE agent_sessions SET {', '.join(assignments)} WHERE id = ?",
                values,
            )
            connection.commit()

    def get_session(self, session_id: str) -> Optional[Dict]:
        with self._connect() as connection:
            session = connection.execute("SELECT * FROM agent_sessions WHERE id = ?", (session_id,)).fetchone()
            if not session:
                return None
            messages = connection.execute(
                "SELECT role, content_json, created_at FROM agent_messages WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
            attempts = connection.execute(
                "SELECT * FROM agent_attempts WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
        return {
            "session": self._hydrate_session_summary(session),
            "messages": [
                {"role": row["role"], "content": json.loads(row["content_json"]), "createdAt": row["created_at"]}
                for row in messages
            ],
            "activeQuestion": json.loads(session["active_question_json"] or "{}"),
            "topicProgress": json.loads(session["topic_progress_json"] or "[]"),
            "reviewSummary": json.loads(session["review_summary_json"] or "{}"),
            "lastEvaluation": json.loads(session["last_evaluation_json"] or "{}"),
            "suggestedAction": session["suggested_action"] or "",
            "attempts": [self._hydrate_attempt(row) for row in attempts],
            "sources": json.loads(session["sources_json"] or "[]"),
        }

    def list_sessions(self, limit: int = 20, mode: Optional[str] = None) -> list[dict]:
        with self._connect() as connection:
            if mode:
                rows = connection.execute(
                    "SELECT * FROM agent_sessions WHERE mode = ? ORDER BY updated_at DESC LIMIT ?",
                    (mode, limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM agent_sessions ORDER BY updated_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [self._hydrate_session_summary(row) for row in rows]
