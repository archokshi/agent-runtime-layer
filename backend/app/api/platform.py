from fastapi import APIRouter

from app.db import get_conn
from app.platform.summary import build_platform_summary
from app.schemas import PlatformSummary

router = APIRouter()


@router.get("/platform/summary", response_model=PlatformSummary)
def get_platform_summary() -> PlatformSummary:
    with get_conn() as conn:
        return build_platform_summary(conn)
