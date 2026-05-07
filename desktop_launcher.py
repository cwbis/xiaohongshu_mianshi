from __future__ import annotations

import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from local_app_server import DEFAULT_PORT, create_server_controller


ROOT = Path(__file__).resolve().parent
APP_URL = f"http://127.0.0.1:{DEFAULT_PORT}"
HEALTH_URL = f"{APP_URL}/api/health"


def wait_for_health(url: str = HEALTH_URL, timeout_seconds: float = 10.0) -> None:
    deadline = time.time() + timeout_seconds
    last_error = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as response:
                if response.status == 200:
                    return
        except Exception as error:  # pragma: no cover - surfaced in final failure
            last_error = error
            time.sleep(0.25)
    raise RuntimeError(f"本地服务启动失败：{last_error or '健康检查超时'}")


def require_webview():
    try:
        import webview  # type: ignore
    except ImportError as error:
        raise RuntimeError(
            "缺少 pywebview 依赖。请先执行 `python -m pip install pywebview`，或者暂时使用 `python local_app_server.py` 启动服务。"
        ) from error
    return webview


def main() -> int:
    controller = create_server_controller(DEFAULT_PORT)
    try:
        controller.start()
        port = controller.server.server_address[1]
        wait_for_health(f"http://127.0.0.1:{port}/api/health")
        webview = require_webview()
        app_url = f"http://127.0.0.1:{port}"
        window = webview.create_window("OfferScope", app_url, width=1440, height=960)
        webview.start()
        return 0 if window else 0
    except Exception as error:
        print(f"[OfferScope Launcher] {error}", file=sys.stderr)
        return 1
    finally:
        controller.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
