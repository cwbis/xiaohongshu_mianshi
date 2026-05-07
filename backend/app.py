from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

from backend.api.agent import router as agent_router
from backend.api.health import router as health_router
from backend.api.storage import router as storage_router
from backend.api.xhs import router as xhs_router
from backend.config import DIST_DIR, ROOT
from backend.errors import ApiError


def create_app() -> FastAPI:
    app = FastAPI(title="OfferScope Local Server", version="0.3.0")
    app.include_router(health_router)
    app.include_router(storage_router)
    app.include_router(xhs_router)
    app.include_router(agent_router)

    @app.exception_handler(ApiError)
    async def api_error_handler(_: Request, exc: ApiError):
        return JSONResponse(status_code=int(exc.status), content={"ok": False, "error": str(exc)})

    @app.exception_handler(Exception)
    async def unexpected_error_handler(_: Request, exc: Exception):
        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})

    static_root = DIST_DIR if DIST_DIR.exists() else ROOT

    @app.get("/{full_path:path}")
    async def frontend_entry(full_path: str):
        target = static_root / full_path
        if full_path and target.exists() and target.is_file():
            return FileResponse(target)
        index_path = static_root / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
        raise ApiError("前端入口不存在。")

    return app
