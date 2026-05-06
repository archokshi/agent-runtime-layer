from app.analyzer.engine import analyze_events
from app.schemas import Event, SchedulerDecision, SchedulerMetrics, SchedulerReport, Task


def _priority(task: Task) -> str:
    if task.priority in {"foreground", "background", "high", "normal", "low"}:
        return task.priority
    if task.latency_slo_seconds and task.latency_slo_seconds <= 30:
        return "foreground"
    return "normal"


def _slo_status(task: Task, duration_ms: int) -> str:
    if not task.latency_slo_seconds:
        return "unknown"
    slo_ms = task.latency_slo_seconds * 1000
    if duration_ms <= slo_ms:
        return "met"
    if duration_ms <= int(slo_ms * 1.2):
        return "at_risk"
    return "missed"


def _budget_status(task: Task, cost: float) -> str:
    if task.budget_dollars is None:
        return "unknown"
    if cost <= task.budget_dollars:
        return "within_budget"
    if cost <= task.budget_dollars * 1.2:
        return "at_risk"
    return "over_budget"


def _tasks_per_hour(duration_ms: int) -> float:
    if duration_ms <= 0:
        return 0.0
    return round(3_600_000 / duration_ms, 2)


def schedule_task(task: Task, events: list[Event]) -> SchedulerReport:
    analysis = analyze_events(task.task_id, events)
    priority = _priority(task)
    decisions: list[SchedulerDecision] = []

    if analysis.tool_time_ms >= max(1000, analysis.total_task_duration_ms * 0.35):
        savings = int(analysis.tool_time_ms * 0.25)
        decisions.append(SchedulerDecision(
            decision_id=f"{task.task_id}:schedule-tool-wait",
            category="tool_wait",
            title="Schedule around blocking tool calls",
            rationale=f"Tool spans consume {analysis.tool_time_ms}ms of the task timeline.",
            action="Run independent safe checks in parallel and prepare the next model step while long tools execute.",
            priority=priority,
            estimated_time_savings_ms=savings,
            estimated_idle_reduction_ms=min(savings, analysis.orchestration_idle_ms),
            confidence=0.78,
            metrics={"tool_time_ms": analysis.tool_time_ms, "tool_call_count": analysis.tool_call_count},
        ))

    if analysis.orchestration_idle_ms >= max(1000, analysis.total_task_duration_ms * 0.25):
        savings = int(analysis.orchestration_idle_ms * 0.3)
        decisions.append(SchedulerDecision(
            decision_id=f"{task.task_id}:schedule-idle-fill",
            category="orchestration_idle",
            title="Fill orchestration idle gaps",
            rationale=f"Idle time accounts for {analysis.orchestration_idle_ms}ms.",
            action="Move deterministic prep, log parsing, and next-step planning into known waiting windows.",
            priority=priority,
            estimated_time_savings_ms=savings,
            estimated_idle_reduction_ms=savings,
            confidence=0.64,
            metrics={"idle_ms": analysis.orchestration_idle_ms},
        ))

    if analysis.retry_count >= 1:
        savings = int((analysis.model_time_ms + analysis.tool_time_ms) * min(0.2, analysis.retry_count * 0.08))
        decisions.append(SchedulerDecision(
            decision_id=f"{task.task_id}:schedule-retry-throttle",
            category="retry_throttling",
            title="Throttle repeated retry loops",
            rationale=f"The trace includes {analysis.retry_count} retry signal(s).",
            action="Require a changed hypothesis or new evidence before another expensive model/tool retry.",
            priority=priority,
            estimated_time_savings_ms=savings,
            estimated_idle_reduction_ms=0,
            confidence=0.7,
            metrics={"retry_count": analysis.retry_count},
        ))

    slo_status = _slo_status(task, analysis.total_task_duration_ms)
    if slo_status in {"at_risk", "missed"}:
        decisions.append(SchedulerDecision(
            decision_id=f"{task.task_id}:schedule-slo-priority",
            category="slo",
            title="Promote SLO-risk task",
            rationale=f"Task duration is {slo_status} against the configured latency SLO.",
            action="Treat the task as foreground until the current critical path completes.",
            priority="foreground",
            estimated_time_savings_ms=0,
            estimated_idle_reduction_ms=0,
            confidence=0.68,
            metrics={"latency_slo_seconds": task.latency_slo_seconds, "duration_ms": analysis.total_task_duration_ms},
        ))

    budget_status = _budget_status(task, analysis.estimated_total_cost_dollars)
    if budget_status in {"at_risk", "over_budget"}:
        decisions.append(SchedulerDecision(
            decision_id=f"{task.task_id}:schedule-budget-stop",
            category="budget",
            title="Gate further expensive work",
            rationale=f"Estimated cost is {budget_status} for the configured budget.",
            action="Pause non-critical model calls and require explicit approval before additional high-cost retries.",
            priority=priority,
            estimated_time_savings_ms=0,
            estimated_idle_reduction_ms=0,
            confidence=0.66,
            metrics={"budget_dollars": task.budget_dollars, "estimated_cost": analysis.estimated_total_cost_dollars},
        ))

    total_savings = min(
        int(analysis.total_task_duration_ms * 0.45),
        sum(decision.estimated_time_savings_ms for decision in decisions),
    )
    idle_reduction = min(
        analysis.orchestration_idle_ms,
        sum(decision.estimated_idle_reduction_ms for decision in decisions),
    )
    scheduled_duration = max(0, analysis.total_task_duration_ms - total_savings)
    lifecycle_state = "completed" if task.status == "completed" else "simulated"
    return SchedulerReport(
        task_id=task.task_id,
        lifecycle_state=lifecycle_state,
        task_priority=priority,  # type: ignore[arg-type]
        decisions=decisions,
        metrics=SchedulerMetrics(
            naive_duration_ms=analysis.total_task_duration_ms,
            scheduled_estimated_duration_ms=scheduled_duration,
            estimated_time_savings_ms=total_savings,
            idle_reduction_ms=idle_reduction,
            naive_tasks_per_hour=_tasks_per_hour(analysis.total_task_duration_ms),
            scheduled_tasks_per_hour=_tasks_per_hour(scheduled_duration),
            tool_wait_ms=analysis.tool_time_ms,
            idle_ms=analysis.orchestration_idle_ms,
            retry_count=analysis.retry_count,
            slo_status=slo_status,  # type: ignore[arg-type]
            budget_status=budget_status,  # type: ignore[arg-type]
        ),
        notes="Local deterministic scheduler simulation. It emits scheduling decisions and estimated improvements; it does not run a production multi-agent scheduler.",
    )
