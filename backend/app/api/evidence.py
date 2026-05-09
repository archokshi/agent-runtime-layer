from fastapi import APIRouter

from app.db import get_conn
from app.evidence.quality import build_evidence_quality_report
from app.schemas import EvidenceQualityReport


router = APIRouter()


@router.get("/evidence/quality", response_model=EvidenceQualityReport)
def get_evidence_quality() -> EvidenceQualityReport:
    with get_conn() as conn:
        return build_evidence_quality_report(conn)
