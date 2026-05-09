from fastapi import APIRouter

from app.corpus.summary import build_trace_corpus_report
from app.db import get_conn
from app.schemas import TraceCorpusReport


router = APIRouter()


@router.get("/corpus/summary", response_model=TraceCorpusReport)
def get_trace_corpus_summary() -> TraceCorpusReport:
    with get_conn() as conn:
        return build_trace_corpus_report(conn)
