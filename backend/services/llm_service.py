from __future__ import annotations

import json
import urllib.error
import urllib.request

from backend.errors import ApiError


def resolve_chat_completions_url(base_url: str) -> str:
    trimmed = str(base_url or "").strip().rstrip("/")
    return trimmed if trimmed.endswith("/chat/completions") else f"{trimmed}/chat/completions"


def extract_json_from_text(text: str) -> dict:
    raw = str(text or "").strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            return json.loads(raw[start : end + 1])
    raise ApiError("大模型返回内容不是有效 JSON。")


class LlmService:
    def complete_json(self, config: dict, messages: list[dict], temperature: float = 0.3) -> dict:
        if not config.get("apiKey"):
            raise ApiError("请先在大模型页面配置 API Key。")
        if not config.get("baseUrl") or not config.get("model"):
            raise ApiError("请先补全大模型的 Base URL 和模型名。")
        payload = json.dumps(
            {
                "model": config["model"],
                "messages": messages,
                "temperature": temperature,
                "response_format": {"type": "json_object"},
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            resolve_chat_completions_url(config["baseUrl"]),
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config['apiKey']}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="ignore") if hasattr(error, "read") else ""
            try:
                payload = json.loads(body)
                message = payload.get("error", {}).get("message") or body
            except json.JSONDecodeError:
                message = body or str(error)
            raise ApiError(message or f"大模型请求失败：{error.code}")
        except Exception as error:
            raise ApiError(f"大模型请求失败：{error}") from error
        text = (((response_payload or {}).get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        return extract_json_from_text(text)
