from fastapi import APIRouter

from app.db import get_conn
from app.schemas import TelemetryCorpusReport
from app.telemetry.summary import build_telemetry_corpus_report


router = APIRouter()


@router.get("/telemetry/summary", response_model=TelemetryCorpusReport)
def get_telemetry_summary() -> TelemetryCorpusReport:
    with get_conn() as conn:
        return build_telemetry_corpus_report(conn)
