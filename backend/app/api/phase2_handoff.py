from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.db import get_conn
from app.phase2_handoff.engine import generate_phase2_handoff_package, render_phase2_handoff_markdown
from app.schemas import Phase2HandoffPackage
from app.storage.repositories import (
    get_phase2_handoff_package,
    list_phase2_handoff_packages,
    save_phase2_handoff_package,
)


router = APIRouter()


@router.post("/phase-2-handoff/generate", response_model=Phase2HandoffPackage)
def generate_phase2_handoff() -> Phase2HandoffPackage:
    with get_conn() as conn:
        report = generate_phase2_handoff_package(conn)
        return save_phase2_handoff_package(conn, report)


@router.get("/phase-2-handoff", response_model=list[Phase2HandoffPackage])
def list_phase2_handoff_reports() -> list[Phase2HandoffPackage]:
    with get_conn() as conn:
        return list_phase2_handoff_packages(conn)


@router.get("/phase-2-handoff/{handoff_id}", response_model=Phase2HandoffPackage)
def get_phase2_handoff_report(handoff_id: str) -> Phase2HandoffPackage:
    with get_conn() as conn:
        report = get_phase2_handoff_package(conn, handoff_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Phase 2 handoff package not found")
    return report


@router.get("/phase-2-handoff/{handoff_id}/export.md", response_class=PlainTextResponse)
def export_phase2_handoff_markdown(handoff_id: str) -> str:
    with get_conn() as conn:
        report = get_phase2_handoff_package(conn, handoff_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Phase 2 handoff package not found")
    return render_phase2_handoff_markdown(report)
