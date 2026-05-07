from __future__ import annotations

import socket
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

try:
    import uvicorn

    from backend.app import create_app
except ImportError as error:  # pragma: no cover - surfaced during startup
    raise RuntimeError(
        "缺少 FastAPI 运行依赖。请先执行 `python -m pip install -r requirements.txt`。"
    ) from error
from backend.config import DB_PATH, DEFAULT_PORT
from backend.repositories.db import StorageRepository


@dataclass
class ServerAddress:
    server_address: tuple[str, int] = ("127.0.0.1", 0)


@dataclass
class ServerController:
    port: int = DEFAULT_PORT
    server: ServerAddress = field(default_factory=ServerAddress)
    _server: Optional[uvicorn.Server] = None
    _thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        if not _is_port_available("127.0.0.1", self.port):
            print(f"端口 {self.port} 已被占用，正在选择可用端口。", file=sys.stderr)
            self.port = 0
        config = uvicorn.Config(create_app(), host="127.0.0.1", port=self.port, log_level="warning")
        self._server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()
        deadline = time.time() + 10
        while time.time() < deadline:
            if self._server.started:
                servers = getattr(self._server, "servers", None) or []
                if servers and servers[0].sockets:
                    sock = servers[0].sockets[0]
                    self.server.server_address = sock.getsockname()[:2]
                else:
                    self.server.server_address = ("127.0.0.1", self.port)
                return
            time.sleep(0.05)
        raise RuntimeError("FastAPI 服务启动超时。")

    def shutdown(self) -> None:
        if self._server:
            self._server.should_exit = True
        if self._thread:
            self._thread.join(timeout=5)


def create_server_controller(port: int = DEFAULT_PORT) -> ServerController:
    return ServerController(port=port)


def _is_port_available(host: str, port: int) -> bool:
    if port == 0:
        return True
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def main() -> None:
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    controller = create_server_controller(port)
    controller.start()
    actual_port = controller.server.server_address[1]
    print(f"OfferScope local server running at http://127.0.0.1:{actual_port}")
    print(f"SQLite storage: {DB_PATH}")
    print("Use Ctrl+C to stop.")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        controller.shutdown()


__all__ = ["DEFAULT_PORT", "StorageRepository", "create_server_controller"]
