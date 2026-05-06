from datetime import datetime, timezone

from fastapi import APIRouter

from app.benchmarking import build_benchmark_run, summarize_benchmark_runs
from app.db import get_conn
from app.schemas import BenchmarkSuiteRun, BenchmarkSuiteRunCreate, BenchmarkSuiteSummary
from app.storage.repositories import list_benchmark_suite_runs, save_benchmark_suite_run

router = APIRouter()


@router.post("/benchmarks/runs", response_model=BenchmarkSuiteRun)
def create_benchmark_run(payload: BenchmarkSuiteRunCreate) -> BenchmarkSuiteRun:
    run = build_benchmark_run(payload, datetime.now(timezone.utc).isoformat())
    with get_conn() as conn:
        return save_benchmark_suite_run(conn, run)


@router.get("/benchmarks/runs", response_model=list[BenchmarkSuiteRun])
def list_benchmark_runs() -> list[BenchmarkSuiteRun]:
    with get_conn() as conn:
        return list_benchmark_suite_runs(conn)


@router.get("/benchmarks/summary", response_model=BenchmarkSuiteSummary)
def get_benchmark_summary() -> BenchmarkSuiteSummary:
    with get_conn() as conn:
        return summarize_benchmark_runs(list_benchmark_suite_runs(conn))
