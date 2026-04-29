from __future__ import annotations

import json
import sqlite3
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
DIST_DIR = ROOT / "dist"
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "offerscope.db"
SCHEMA_VERSION = 1
DEFAULT_PORT = 8080
XHS_SCRIPT_DIR = ROOT / "XhsSkills-master" / "skills" / "xhs-apis" / "scripts"

if str(XHS_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(XHS_SCRIPT_DIR))

import xhs_api_tool  # noqa: E402


class ApiError(Exception):
    def __init__(self, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST):
        super().__init__(message)
        self.status = status


@dataclass
class ServerController:
    server: ThreadingHTTPServer
    thread: threading.Thread | None = None

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def shutdown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        if self.thread:
            self.thread.join(timeout=5)


class StorageRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
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
                """
            )
        self.set_meta("schemaVersion", SCHEMA_VERSION)
        if self.get_meta("legacyImportCompleted") is None:
            self.set_meta("legacyImportCompleted", False)

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
                ON CONFLICT(key) DO UPDATE SET
                    value_json = excluded.value_json,
                    updated_at = CURRENT_TIMESTAMP
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

    def has_posts(self) -> bool:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(1) AS count FROM posts").fetchone()
        return bool(row["count"])

    def replace_posts(self, records: list[dict]) -> list[dict]:
        normalized = dedupe_post_records(records)
        with self._lock:
            with self._connect() as connection:
                connection.execute("DELETE FROM posts")
                for record in normalized:
                    self._insert_post(connection, record)
                connection.commit()
        return normalized

    def merge_posts(self, records: list[dict]) -> list[dict]:
        merged = dedupe_post_records(self.list_posts() + records)
        return self.replace_posts(merged)

    def _insert_post(self, connection: sqlite3.Connection, record: dict) -> None:
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
                ON CONFLICT(scope) DO UPDATE SET
                    value_json = excluded.value_json,
                    updated_at = CURRENT_TIMESTAMP
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


SUPPORTED_SETTING_SCOPES = {"xhsConfig", "llmConfig"}
STORAGE = StorageRepository(DB_PATH)
RUNTIME = None


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


def build_note_url(note_id, xsec_token, xsec_source="pc_search"):
    if not note_id or not xsec_token:
        return ""
    return f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}&xsec_source={xsec_source}"


def normalize_search_item(item):
    note_card = nested_get(item, "note_card") or {}
    user = first_non_empty(
        nested_get(note_card, "user"),
        nested_get(note_card, "author"),
        nested_get(item, "user")
    ) or {}
    interact = nested_get(note_card, "interact_info") or {}
    image_list = nested_get(note_card, "image_list") or []
    first_image = image_list[0] if image_list else {}
    cover = first_non_empty(
        nested_get(first_image, "url_default"),
        nested_get(first_image, "url"),
        nested_get(note_card, "cover", "url_default"),
        nested_get(item, "cover", "url_default")
    )
    note_id = first_non_empty(item.get("id"), note_card.get("note_id"), note_card.get("id"))
    xsec_token = first_non_empty(item.get("xsec_token"), note_card.get("xsec_token"))
    xsec_source = first_non_empty(item.get("xsec_source"), "pc_search")
    note_type_raw = str(first_non_empty(note_card.get("type"), item.get("model_type"), "")).lower()

    return {
        "noteId": note_id,
        "title": first_non_empty(
            note_card.get("display_title"),
            note_card.get("title"),
            item.get("display_title"),
            item.get("title")
        ) or "未命名帖子",
        "excerpt": first_non_empty(
            note_card.get("desc"),
            note_card.get("display_desc"),
            item.get("desc"),
            item.get("content")
        ) or "",
        "content": first_non_empty(
            note_card.get("desc"),
            note_card.get("display_desc"),
            item.get("desc")
        ) or "",
        "author": first_non_empty(
            user.get("nick_name"),
            user.get("nickname"),
            user.get("name")
        ) or "",
        "authorId": first_non_empty(user.get("user_id"), user.get("id")) or "",
        "publishTime": first_non_empty(
            note_card.get("time"),
            item.get("publish_time"),
            item.get("publishTime")
        ) or "",
        "coverUrl": cover or "",
        "likeCount": first_non_empty(interact.get("liked_count"), item.get("liked_count")),
        "commentCount": first_non_empty(interact.get("comment_count"), item.get("comment_count")),
        "collectCount": first_non_empty(interact.get("collected_count"), item.get("comment_count")),
        "noteTypeLabel": "视频" if "video" in note_type_raw else "图文",
        "xsecToken": xsec_token or "",
        "xsecSource": xsec_source,
        "sourceUrl": build_note_url(note_id, xsec_token, xsec_source)
    }


def normalize_detail_response(url, response_json):
    item = first_non_empty(
        nested_get(response_json, "data", "items", 0),
        nested_get(response_json, "data", "item"),
        nested_get(response_json, "data", "note_card")
    ) or {}
    normalized = normalize_search_item(item)
    note_card = nested_get(item, "note_card") or item
    desc = first_non_empty(note_card.get("desc"), note_card.get("display_desc"), normalized.get("content")) or ""
    normalized["content"] = desc
    normalized["excerpt"] = desc[:180]
    normalized["sourceUrl"] = url or normalized["sourceUrl"]
    normalized["detailLoaded"] = True
    return normalized


class XhsRuntime:
    def __init__(self):
        self.namespaces = xhs_api_tool._load_namespaces()

    def call(self, namespace, method, payload):
        target, signature = xhs_api_tool._resolve_callable(self.namespaces, namespace, method)
        normalized = xhs_api_tool._normalize_payload(self.namespaces, namespace, method, signature, payload)
        return target(**normalized)


def get_runtime():
    global RUNTIME
    if RUNTIME is None:
        RUNTIME = XhsRuntime()
    return RUNTIME


def normalize_post_record(record: dict) -> dict:
    if not isinstance(record, dict):
        raise ApiError("Post record must be an object.")

    normalized = dict(record)
    normalized["id"] = str(normalized.get("id") or f"post-{uuid.uuid4().hex}")
    normalized["title"] = str(normalized.get("title") or "未命名帖子")
    normalized["author"] = str(normalized.get("author") or "")
    normalized["publishTime"] = str(normalized.get("publishTime") or "")
    normalized["sourceUrl"] = str(normalized.get("sourceUrl") or "")
    normalized["content"] = str(normalized.get("content") or "")
    normalized["company"] = str(normalized.get("company") or "")
    normalized["role"] = str(normalized.get("role") or "")
    normalized["keyword"] = str(normalized.get("keyword") or "")
    normalized["noteId"] = str(normalized.get("noteId") or "")
    normalized["collectedAt"] = str(normalized.get("collectedAt") or time.strftime("%Y-%m-%dT%H:%M:%S"))
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
    return sorted(
        ordered.values(),
        key=lambda item: item.get("collectedAt") or "",
        reverse=True,
    )


def validate_posts_payload(payload: dict) -> list[dict]:
    items = payload.get("posts")
    if not isinstance(items, list):
        raise ApiError("Field 'posts' must be an array.")
    return items


def validate_setting_scope(scope: str) -> str:
    if scope not in SUPPORTED_SETTING_SCOPES:
        raise ApiError(f"Unsupported settings scope: {scope}", HTTPStatus.NOT_FOUND)
    return scope


def validate_setting_value(payload: dict) -> dict:
    value = payload.get("value")
    if not isinstance(value, dict):
        raise ApiError("Field 'value' must be an object.")
    return value


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(self.static_root()), **kwargs)

    @staticmethod
    def static_root() -> Path:
        return DIST_DIR if DIST_DIR.exists() else ROOT

    def do_GET(self):
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/health":
                self.write_json(
                    {
                        "ok": True,
                        "service": "offerscope-local-server",
                        "dbPath": str(DB_PATH),
                        "schemaVersion": SCHEMA_VERSION,
                    }
                )
                return
            if parsed.path == "/api/storage/bootstrap":
                self.write_json({"ok": True, **STORAGE.bootstrap_payload()})
                return
            if parsed.path == "/api/storage/posts":
                self.write_json({"ok": True, "posts": STORAGE.list_posts()})
                return
            if parsed.path == "/api/storage/settings":
                query = parse_qs(parsed.query)
                scope = query.get("scope", [None])[0]
                if scope:
                    validate_setting_scope(scope)
                    self.write_json({"ok": True, "scope": scope, "value": STORAGE.get_setting(scope, {})})
                else:
                    self.write_json({"ok": True, "settings": STORAGE.get_settings()})
                return
        except ApiError as exc:
            self.write_json({"ok": False, "error": str(exc)}, status=exc.status)
            return

        if parsed.path.startswith("/api/"):
            self.write_json({"ok": False, "error": "Unknown API path."}, status=HTTPStatus.NOT_FOUND)
            return

        if parsed.path == "/":
            self.path = "/index.html"
        elif DIST_DIR.exists() and not (self.static_root() / parsed.path.lstrip("/")).exists():
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            payload = self.read_json_body()
            if parsed.path == "/api/xhs/search":
                self.handle_xhs_search(payload)
                return
            if parsed.path == "/api/xhs/note-detail":
                self.handle_xhs_note_detail(payload)
                return
            if parsed.path == "/api/storage/import-local":
                self.handle_import_local(payload)
                return
            self.write_json({"ok": False, "error": "Unknown API path."}, status=HTTPStatus.NOT_FOUND)
        except ApiError as exc:
            self.write_json({"ok": False, "error": str(exc)}, status=exc.status)
        except Exception as exc:
            self.write_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def do_PUT(self):
        parsed = urlparse(self.path)
        try:
            payload = self.read_json_body()
            if parsed.path == "/api/storage/posts":
                records = validate_posts_payload(payload)
                stored = STORAGE.replace_posts(records)
                self.write_json({"ok": True, "posts": stored, "count": len(stored)})
                return
            if parsed.path.startswith("/api/storage/settings/"):
                scope = validate_setting_scope(parsed.path.rsplit("/", 1)[-1])
                value = validate_setting_value(payload)
                self.write_json({"ok": True, "scope": scope, "value": STORAGE.set_setting(scope, value)})
                return
            self.write_json({"ok": False, "error": "Unknown API path."}, status=HTTPStatus.NOT_FOUND)
        except ApiError as exc:
            self.write_json({"ok": False, "error": str(exc)}, status=exc.status)
        except Exception as exc:
            self.write_json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            return json.loads(raw or "{}")
        except json.JSONDecodeError as exc:
            raise ApiError(f"Invalid JSON body: {exc.msg}") from exc

    def handle_xhs_search(self, payload):
        query = str(payload.get("query") or "").strip()
        cookies_str = str(payload.get("cookiesStr") or "").strip()
        page = int(payload.get("page") or 1)
        page_size = max(1, min(50, int(payload.get("pageSize") or 20)))
        sort_type_choice = int(payload.get("sortTypeChoice") or 0)

        if not query:
            raise ApiError("Missing query.")
        if not cookies_str:
            raise ApiError("Missing cookiesStr.")

        success, msg, result = get_runtime().call(
            "pc",
            "search_note",
            {
                "query": query,
                "cookies_str": cookies_str,
                "page": page,
                "sort_type_choice": sort_type_choice,
            },
        )

        if not success:
            raise ApiError(msg or "Search failed.", HTTPStatus.BAD_GATEWAY)

        items = nested_get(result, "data", "items") or []
        self.write_json(
            {
                "ok": True,
                "query": query,
                "items": [normalize_search_item(item) for item in items[:page_size]],
                "rawCount": len(items),
            }
        )

    def handle_xhs_note_detail(self, payload):
        url = str(payload.get("url") or "").strip()
        cookies_str = str(payload.get("cookiesStr") or "").strip()

        if not url:
            raise ApiError("Missing url.")
        if not cookies_str:
            raise ApiError("Missing cookiesStr.")

        success, msg, result = get_runtime().call(
            "pc",
            "get_note_info",
            {
                "url": url,
                "cookies_str": cookies_str,
            },
        )

        if not success:
            raise ApiError(msg or "Detail request failed.", HTTPStatus.BAD_GATEWAY)

        self.write_json({"ok": True, "item": normalize_detail_response(url, result)})

    def handle_import_local(self, payload: dict):
        posts = payload.get("posts") or []
        if posts and not isinstance(posts, list):
            raise ApiError("Field 'posts' must be an array.")
        for scope in SUPPORTED_SETTING_SCOPES:
            if scope in payload and not isinstance(payload[scope], dict):
                raise ApiError(f"Field '{scope}' must be an object when provided.")
        result = STORAGE.import_legacy_payload(payload)
        self.write_json({"ok": True, **result})

    def write_json(self, payload, status=HTTPStatus.OK):
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def create_server(port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("127.0.0.1", port), AppHandler)


def create_server_controller(port: int = DEFAULT_PORT) -> ServerController:
    return ServerController(server=create_server(port))


def main():
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    server = create_server(port)
    print(f"OfferScope local server running at http://127.0.0.1:{port}")
    print(f"SQLite storage: {DB_PATH}")
    print("Use Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
