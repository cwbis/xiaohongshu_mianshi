from __future__ import annotations

import sys

from backend.config import XHS_SCRIPT_DIR
from backend.repositories.db import first_non_empty, nested_get
from backend.errors import ApiError

if str(XHS_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(XHS_SCRIPT_DIR))

import xhs_api_tool  # noqa: E402


def build_note_url(note_id, xsec_token, xsec_source="pc_search"):
    if not note_id or not xsec_token:
        return ""
    return f"https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}&xsec_source={xsec_source}"


def normalize_search_item(item):
    note_card = nested_get(item, "note_card") or {}
    user = first_non_empty(nested_get(note_card, "user"), nested_get(note_card, "author"), nested_get(item, "user")) or {}
    interact = nested_get(note_card, "interact_info") or {}
    image_list = nested_get(note_card, "image_list") or []
    first_image = image_list[0] if image_list else {}
    cover = first_non_empty(
        nested_get(first_image, "url_default"),
        nested_get(first_image, "url"),
        nested_get(note_card, "cover", "url_default"),
        nested_get(item, "cover", "url_default"),
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
            item.get("title"),
        )
        or "未命名帖子",
        "excerpt": first_non_empty(note_card.get("desc"), note_card.get("display_desc"), item.get("desc"), item.get("content")) or "",
        "content": first_non_empty(note_card.get("desc"), note_card.get("display_desc"), item.get("desc")) or "",
        "author": first_non_empty(user.get("nick_name"), user.get("nickname"), user.get("name")) or "",
        "authorId": first_non_empty(user.get("user_id"), user.get("id")) or "",
        "publishTime": first_non_empty(note_card.get("time"), item.get("publish_time"), item.get("publishTime")) or "",
        "coverUrl": cover or "",
        "likeCount": first_non_empty(interact.get("liked_count"), item.get("liked_count")),
        "commentCount": first_non_empty(interact.get("comment_count"), item.get("comment_count")),
        "collectCount": first_non_empty(interact.get("collected_count"), item.get("comment_count")),
        "noteTypeLabel": "视频" if "video" in note_type_raw else "图文",
        "xsecToken": xsec_token or "",
        "xsecSource": xsec_source,
        "sourceUrl": build_note_url(note_id, xsec_token, xsec_source),
    }


def normalize_detail_response(url, response_json):
    item = first_non_empty(
        nested_get(response_json, "data", "items", 0),
        nested_get(response_json, "data", "item"),
        nested_get(response_json, "data", "note_card"),
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


class XhsService:
    def __init__(self):
        self.runtime = XhsRuntime()

    def search(self, query: str, cookies_str: str, page: int, page_size: int, sort_type_choice: int) -> dict:
        if not query:
            raise ApiError("Missing query.")
        if not cookies_str:
            raise ApiError("Missing cookiesStr.")
        success, msg, result = self.runtime.call(
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
            raise ApiError(msg or "Search failed.")
        items = nested_get(result, "data", "items") or []
        return {
            "ok": True,
            "query": query,
            "items": [normalize_search_item(item) for item in items[:page_size]],
            "rawCount": len(items),
        }

    def detail(self, url: str, cookies_str: str) -> dict:
        if not url:
            raise ApiError("Missing url.")
        if not cookies_str:
            raise ApiError("Missing cookiesStr.")
        success, msg, result = self.runtime.call("pc", "get_note_info", {"url": url, "cookies_str": cookies_str})
        if not success:
            raise ApiError(msg or "Detail request failed.")
        return {"ok": True, "item": normalize_detail_response(url, result)}
