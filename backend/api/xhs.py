from fastapi import APIRouter

from backend.services.xhs_service import XhsService


router = APIRouter()
xhs_service = XhsService()


@router.post("/api/xhs/search")
def search(payload: dict):
    return xhs_service.search(
        query=str(payload.get("query") or "").strip(),
        cookies_str=str(payload.get("cookiesStr") or "").strip(),
        page=int(payload.get("page") or 1),
        page_size=max(1, min(50, int(payload.get("pageSize") or 20))),
        sort_type_choice=int(payload.get("sortTypeChoice") or 0),
    )


@router.post("/api/xhs/note-detail")
def note_detail(payload: dict):
    return xhs_service.detail(
        url=str(payload.get("url") or "").strip(),
        cookies_str=str(payload.get("cookiesStr") or "").strip(),
    )
