from fastapi import APIRouter

from backend.config import DB_PATH, SCHEMA_VERSION


router = APIRouter()


@router.get("/api/health")
def health():
    return {
        "ok": True,
        "service": "offerscope-local-server",
        "dbPath": str(DB_PATH),
        "schemaVersion": SCHEMA_VERSION,
    }
