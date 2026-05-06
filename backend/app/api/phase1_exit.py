from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.db import get_conn
from app.phase1_exit.engine import generate_phase1_exit_package, render_phase1_exit_markdown
from app.schemas import Phase1ExitPackage
from app.storage.repositories import (
    get_phase1_exit_package,
    list_phase1_exit_packages,
    save_phase1_exit_package,
)

router = APIRouter()


@router.post("/phase-1-exit/generate", response_model=Phase1ExitPackage)
def generate_phase1_exit() -> Phase1ExitPackage:
    with get_conn() as conn:
        report = generate_phase1_exit_package(conn)
        return save_phase1_exit_package(conn, report)


@router.get("/phase-1-exit", response_model=list[Phase1ExitPackage])
def list_phase1_exit_reports() -> list[Phase1ExitPackage]:
    with get_conn() as conn:
        return list_phase1_exit_packages(conn)


@router.get("/phase-1-exit/{package_id}", response_model=Phase1ExitPackage)
def get_phase1_exit_report(package_id: str) -> Phase1ExitPackage:
    with get_conn() as conn:
        report = get_phase1_exit_package(conn, package_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Phase 1.011 package not found")
    return report


@router.get("/phase-1-exit/{package_id}/export.md", response_class=PlainTextResponse)
def export_phase1_exit_markdown(package_id: str) -> str:
    with get_conn() as conn:
        report = get_phase1_exit_package(conn, package_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Phase 1.011 package not found")
    return render_phase1_exit_markdown(report)
