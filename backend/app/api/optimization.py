"""Phase 1.7: Context Optimizer Runtime — apply optimization + proof endpoints."""

from uuid import uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.db import get_conn
from app.optimizer.context import optimize_context
from app.schemas import ApplyOptimizationResponse, OptimizationProofRecord
from app.storage.repositories import (
    get_context_optimization_report,
    get_task,
    list_events,
    save_context_optimization_report,
)

router = APIRouter()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _store_proof(conn, proof: OptimizationProofRecord) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO optimization_proofs
           (proof_id, baseline_task_id, optimized_task_id,
            baseline_input_tokens, optimized_input_tokens,
            baseline_cost_dollars, optimized_cost_dollars,
            token_reduction_percent, cost_reduction_percent,
            success_preserved, evidence_quality, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            proof.proof_id,
            proof.baseline_task_id,
            proof.optimized_task_id,
            proof.baseline_input_tokens,
            proof.optimized_input_tokens,
            proof.baseline_cost_dollars,
            proof.optimized_cost_dollars,
            proof.token_reduction_percent,
            proof.cost_reduction_percent,
            int(proof.success_preserved) if proof.success_preserved is not None else None,
            proof.evidence_quality,
            proof.created_at or _utc_now(),
        ),
    )


def _load_proof(conn, proof_id: str) -> OptimizationProofRecord | None:
    row = conn.execute(
        "SELECT * FROM optimization_proofs WHERE proof_id = ?", (proof_id,)
    ).fetchone()
    if not row:
        return None
    return OptimizationProofRecord(
        proof_id=row["proof_id"],
        baseline_task_id=row["baseline_task_id"],
        optimized_task_id=row["optimized_task_id"],
        baseline_input_tokens=row["baseline_input_tokens"],
        optimized_input_tokens=row["optimized_input_tokens"],
        baseline_cost_dollars=row["baseline_cost_dollars"],
        optimized_cost_dollars=row["optimized_cost_dollars"],
        token_reduction_percent=row["token_reduction_percent"],
        cost_reduction_percent=row["cost_reduction_percent"],
        success_preserved=bool(row["success_preserved"]) if row["success_preserved"] is not None else None,
        evidence_quality=row["evidence_quality"],
        created_at=row["created_at"],
    )


def _list_proofs(conn) -> list[OptimizationProofRecord]:
    rows = conn.execute(
        "SELECT * FROM optimization_proofs ORDER BY created_at DESC"
    ).fetchall()
    return [_load_proof(conn, row["proof_id"]) for row in rows if row]


@router.post("/tasks/{task_id}/apply-optimization", response_model=ApplyOptimizationResponse)
def apply_optimization(task_id: str) -> ApplyOptimizationResponse:
    """Run the context optimizer on this task and store a before/after proof record.

    This is the Phase 1.7 'Fix it' action. The optimizer already computes the
    analysis — this endpoint applies it and produces a measurable proof record.
    """
    with get_conn() as conn:
        task = get_task(conn, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        events = list_events(conn, task_id)
        if not events:
            raise HTTPException(status_code=422, detail="No events found for this task — cannot optimize.")

        # Run optimizer (generates or retrieves the ContextOptimizationReport)
        existing = get_context_optimization_report(conn, task_id)
        if existing is None:
            report = optimize_context(task, events)
            save_context_optimization_report(conn, task_id, report)
        else:
            report = existing

        # Build proof record from optimizer results
        baseline_tokens = report.baseline.input_tokens
        optimized_tokens = report.optimized.input_tokens
        baseline_cost = report.baseline.estimated_cost
        optimized_cost = report.optimized.estimated_cost

        token_reduction = report.savings.input_token_reduction_percent
        cost_reduction = report.savings.estimated_cost_reduction_percent

        # Evidence quality: estimated until a real optimized run is captured
        evidence_quality = "estimated"

        proof_id = f"proof_{uuid4().hex[:12]}"
        proof = OptimizationProofRecord(
            proof_id=proof_id,
            baseline_task_id=task_id,
            optimized_task_id=None,
            baseline_input_tokens=baseline_tokens,
            optimized_input_tokens=optimized_tokens,
            baseline_cost_dollars=baseline_cost,
            optimized_cost_dollars=optimized_cost,
            token_reduction_percent=token_reduction,
            cost_reduction_percent=cost_reduction,
            success_preserved=None,
            evidence_quality=evidence_quality,
            created_at=_utc_now(),
        )
        _store_proof(conn, proof)

    return ApplyOptimizationResponse(
        proof_id=proof_id,
        baseline_task_id=task_id,
        token_reduction_percent=token_reduction,
        cost_reduction_percent=cost_reduction,
        evidence_quality=evidence_quality,
        message=(
            f"Optimization applied. ~ Estimated: −{token_reduction:.1f}% tokens, "
            f"−{cost_reduction:.1f}% cost. "
            f"Run your agent again with the optimized context to upgrade to ✓ Verified."
        ),
    )


@router.get("/optimization-proofs/{proof_id}", response_model=OptimizationProofRecord)
def get_proof(proof_id: str) -> OptimizationProofRecord:
    with get_conn() as conn:
        proof = _load_proof(conn, proof_id)
        if proof is None:
            raise HTTPException(status_code=404, detail="Proof record not found")
        return proof


@router.get("/optimization-proofs", response_model=list[OptimizationProofRecord])
def list_proofs() -> list[OptimizationProofRecord]:
    with get_conn() as conn:
        return _list_proofs(conn)


@router.patch("/optimization-proofs/{proof_id}/verify", response_model=OptimizationProofRecord)
def verify_proof(proof_id: str, optimized_task_id: str, success_preserved: bool) -> OptimizationProofRecord:
    """Upgrade a proof from estimated to verified by linking a real optimized run."""
    with get_conn() as conn:
        proof = _load_proof(conn, proof_id)
        if proof is None:
            raise HTTPException(status_code=404, detail="Proof record not found")

        opt_task = get_task(conn, optimized_task_id)
        if opt_task is None:
            raise HTTPException(status_code=404, detail="Optimized task not found")

        opt_events = list_events(conn, optimized_task_id)
        opt_report = optimize_context(opt_task, opt_events)

        real_token_reduction = (
            (proof.baseline_input_tokens - opt_report.baseline.input_tokens) /
            proof.baseline_input_tokens * 100
            if proof.baseline_input_tokens > 0 else 0.0
        )
        real_cost_reduction = (
            (proof.baseline_cost_dollars - opt_report.baseline.estimated_cost) /
            proof.baseline_cost_dollars * 100
            if proof.baseline_cost_dollars > 0 else 0.0
        )

        proof.optimized_task_id = optimized_task_id
        proof.optimized_input_tokens = opt_report.baseline.input_tokens
        proof.optimized_cost_dollars = opt_report.baseline.estimated_cost
        proof.token_reduction_percent = real_token_reduction
        proof.cost_reduction_percent = real_cost_reduction
        proof.success_preserved = success_preserved
        proof.evidence_quality = "measured"
        _store_proof(conn, proof)
        return proof
