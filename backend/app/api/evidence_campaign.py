from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.db import get_conn
from app.evidence_campaign.engine import generate_evidence_campaign_report, render_evidence_campaign_markdown
from app.schemas import EvidenceCampaignReport
from app.storage.repositories import (
    get_evidence_campaign_report,
    list_evidence_campaign_reports,
    save_evidence_campaign_report,
)


router = APIRouter()


@router.post("/evidence-campaign/generate", response_model=EvidenceCampaignReport)
def generate_campaign_report() -> EvidenceCampaignReport:
    with get_conn() as conn:
        report = generate_evidence_campaign_report(conn, persist_handoff=True)
        return save_evidence_campaign_report(conn, report)


@router.get("/evidence-campaign", response_model=list[EvidenceCampaignReport])
def list_campaign_reports() -> list[EvidenceCampaignReport]:
    with get_conn() as conn:
        return list_evidence_campaign_reports(conn)


@router.get("/evidence-campaign/{campaign_id}", response_model=EvidenceCampaignReport)
def get_campaign_report(campaign_id: str) -> EvidenceCampaignReport:
    with get_conn() as conn:
        report = get_evidence_campaign_report(conn, campaign_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Evidence campaign report not found")
    return report


@router.get("/evidence-campaign/{campaign_id}/export.md", response_class=PlainTextResponse)
def export_campaign_markdown(campaign_id: str) -> str:
    with get_conn() as conn:
        report = get_evidence_campaign_report(conn, campaign_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Evidence campaign report not found")
    return render_evidence_campaign_markdown(report)
