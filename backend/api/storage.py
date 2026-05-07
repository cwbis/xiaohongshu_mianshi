from typing import Optional

from fastapi import APIRouter

from backend.config import DB_PATH
from backend.errors import ApiError
from backend.repositories.db import StorageRepository, validate_posts_payload, validate_setting_scope, validate_setting_value


router = APIRouter()
storage = StorageRepository(DB_PATH)


@router.get("/api/storage/bootstrap")
def bootstrap():
    return {"ok": True, **storage.bootstrap_payload()}


@router.get("/api/storage/posts")
def list_posts():
    return {"ok": True, "posts": storage.list_posts()}


@router.get("/api/storage/settings")
def list_settings(scope: Optional[str] = None):
    if scope:
        validate_setting_scope(scope)
        return {"ok": True, "scope": scope, "value": storage.get_setting(scope, {})}
    return {"ok": True, "settings": storage.get_settings()}


@router.put("/api/storage/posts")
def replace_posts(payload: dict):
    records = validate_posts_payload(payload)
    stored = storage.replace_posts(records)
    return {"ok": True, "posts": stored, "count": len(stored)}


@router.put("/api/storage/settings/{scope}")
def save_setting(scope: str, payload: dict):
    scope = validate_setting_scope(scope)
    value = validate_setting_value(payload)
    return {"ok": True, "scope": scope, "value": storage.set_setting(scope, value)}


@router.post("/api/storage/import-local")
def import_local(payload: dict):
    posts = payload.get("posts") or []
    if posts and not isinstance(posts, list):
        raise ApiError("Field 'posts' must be an array.")
    result = storage.import_legacy_payload(payload)
    return {"ok": True, **result}
