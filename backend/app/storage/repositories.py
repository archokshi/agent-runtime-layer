import json
import uuid
from sqlite3 import Connection

from app.redaction import redact_json
from app.schemas import (
    AnalysisReport,
    BackendAwareReport,
    BenchmarkSuiteRun,
    BlueprintPreview,
    ContextOptimizationReport,
    EvidenceCampaignReport,
    Event,
    HardwareAnalysisReport,
    HardwareTelemetrySample,
    MeasuredValidationExperiment,
    Phase1ExitPackage,
    Phase2HandoffPackage,
    SchedulerReport,
    SiliconBlueprintReport,
    Task,
    TaskCreate,
    TraceReplayReport,
)


def ensure_project(conn: Connection, project_id: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO projects(project_id, name) VALUES (?, ?)",
        (project_id, project_id),
    )


def create_task(conn: Connection, task: TaskCreate) -> str:
    task_id = task.task_id or f"task_{uuid.uuid4().hex[:12]}"
    ensure_project(conn, task.project_id)
    conn.execute(
        """
        INSERT OR REPLACE INTO tasks(
          task_id, project_id, goal, agent_type, budget_dollars, latency_slo_seconds, priority,
          benchmark_name, benchmark_task_id, repo_name, issue_id, agent_name,
          baseline_or_optimized, task_success, tests_passed, tests_failed,
          patch_generated, files_changed_count, retry_count, before_after_pair_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            task.project_id,
            task.goal,
            task.agent_type,
            task.budget_dollars,
            task.latency_slo_seconds,
            task.priority,
            task.benchmark_name,
            task.benchmark_task_id,
            task.repo_name,
            task.issue_id,
            task.agent_name,
            task.baseline_or_optimized,
            task.task_success,
            task.tests_passed,
            task.tests_failed,
            task.patch_generated,
            task.files_changed_count,
            task.retry_count,
            task.before_after_pair_id,
        ),
    )
    return task_id


def row_to_task(row) -> Task:
    data = dict(row)
    for key in ("task_success", "patch_generated"):
        if data.get(key) is not None:
            data[key] = bool(data[key])
    return Task(**data)


def list_tasks(conn: Connection) -> list[Task]:
    rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    return [row_to_task(row) for row in rows]


def get_task(conn: Connection, task_id: str) -> Task | None:
    row = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
    return row_to_task(row) if row else None


def list_tasks_by_pair(conn: Connection, before_after_pair_id: str) -> list[Task]:
    rows = conn.execute(
        "SELECT * FROM tasks WHERE before_after_pair_id = ? ORDER BY baseline_or_optimized ASC, created_at ASC",
        (before_after_pair_id,),
    ).fetchall()
    return [row_to_task(row) for row in rows]


def add_event(conn: Connection, event: Event) -> None:
    attributes_json = redact_json(event.attributes)
    payload_json = redact_json(event.payload)
    conn.execute(
        """
        INSERT OR REPLACE INTO events(
          event_id, task_id, timestamp, event_type, span_id, parent_span_id, name,
          attributes_json, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.event_id,
            event.task_id,
            event.timestamp,
            event.event_type,
            event.span_id,
            event.parent_span_id,
            event.name,
            attributes_json,
            payload_json,
        ),
    )
    if event.event_type == "task_start":
        conn.execute("UPDATE tasks SET started_at = ? WHERE task_id = ?", (event.timestamp, event.task_id))
    if event.event_type == "task_end":
        conn.execute(
            "UPDATE tasks SET ended_at = ?, status = ?, summary = ? WHERE task_id = ?",
            (
                event.timestamp,
                event.payload.get("status", "completed"),
                event.payload.get("summary"),
                event.task_id,
            ),
        )
    if event.event_type == "context_snapshot":
        conn.execute(
            """
            INSERT OR REPLACE INTO context_snapshots(
              context_id, task_id, event_id, size_tokens, repeated_tokens_estimate, context_kind
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event.attributes.get("context_id", event.event_id),
                event.task_id,
                event.event_id,
                int(event.attributes.get("size_tokens", 0)),
                int(event.attributes.get("repeated_tokens_estimate", 0)),
                event.attributes.get("context_kind"),
            ),
        )


def row_to_event(row) -> Event:
    return Event(
        event_id=row["event_id"],
        task_id=row["task_id"],
        timestamp=row["timestamp"],
        event_type=row["event_type"],
        span_id=row["span_id"],
        parent_span_id=row["parent_span_id"],
        name=row["name"],
        attributes=json.loads(row["attributes_json"]),
        payload=json.loads(row["payload_json"]),
    )


def list_events(conn: Connection, task_id: str) -> list[Event]:
    rows = conn.execute(
        "SELECT * FROM events WHERE task_id = ? ORDER BY timestamp ASC",
        (task_id,),
    ).fetchall()
    return [row_to_event(row) for row in rows]


def save_analysis(conn: Connection, report: AnalysisReport) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO analysis_reports(task_id, report_json) VALUES (?, ?)",
        (report.task_id, report.model_dump_json()),
    )


def save_blueprint(conn: Connection, preview: BlueprintPreview) -> None:
    conn.execute("DELETE FROM recommendations WHERE task_id = ?", (preview.task_id,))
    for rec in preview.recommendations:
        conn.execute(
            """
            INSERT INTO recommendations(
              recommendation_id, task_id, category, title, rationale, confidence, metrics_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rec.recommendation_id,
                preview.task_id,
                rec.category,
                rec.title,
                rec.rationale,
                rec.confidence,
                json.dumps(rec.metrics, sort_keys=True),
            ),
        )


def save_context_optimization_report(conn: Connection, report: ContextOptimizationReport) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO context_optimization_reports(task_id, report_json)
        VALUES (?, ?)
        """,
        (report.task_id, report.model_dump_json()),
    )


def get_context_optimization_report(conn: Connection, task_id: str) -> ContextOptimizationReport | None:
    row = conn.execute(
        "SELECT report_json FROM context_optimization_reports WHERE task_id = ?",
        (task_id,),
    ).fetchone()
    if row is None:
        return None
    return ContextOptimizationReport.model_validate_json(row["report_json"])


def save_scheduler_report(conn: Connection, report: SchedulerReport) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO scheduler_reports(task_id, report_json)
        VALUES (?, ?)
        """,
        (report.task_id, report.model_dump_json()),
    )


def get_scheduler_report(conn: Connection, task_id: str) -> SchedulerReport | None:
    row = conn.execute(
        "SELECT report_json FROM scheduler_reports WHERE task_id = ?",
        (task_id,),
    ).fetchone()
    if row is None:
        return None
    return SchedulerReport.model_validate_json(row["report_json"])


def save_backend_aware_report(conn: Connection, report: BackendAwareReport) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO backend_hint_reports(task_id, report_json)
        VALUES (?, ?)
        """,
        (report.task_id, report.model_dump_json()),
    )


def get_backend_aware_report(conn: Connection, task_id: str) -> BackendAwareReport | None:
    row = conn.execute(
        "SELECT report_json FROM backend_hint_reports WHERE task_id = ?",
        (task_id,),
    ).fetchone()
    if row is None:
        return None
    return BackendAwareReport.model_validate_json(row["report_json"])


def add_hardware_telemetry_samples(conn: Connection, samples: list[HardwareTelemetrySample]) -> int:
    for sample in samples:
        sample_id = sample.sample_id or f"hw_{uuid.uuid4().hex[:12]}"
        conn.execute(
            """
            INSERT OR REPLACE INTO hardware_telemetry_samples(
              sample_id, task_id, timestamp, backend_id, gpu_utilization_percent,
              cpu_utilization_percent, gpu_memory_used_percent, queue_depth,
              prefill_ms, decode_ms, kv_cache_hit_rate, attributes_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sample_id,
                sample.task_id,
                sample.timestamp,
                sample.backend_id,
                sample.gpu_utilization_percent,
                sample.cpu_utilization_percent,
                sample.gpu_memory_used_percent,
                sample.queue_depth,
                sample.prefill_ms,
                sample.decode_ms,
                sample.kv_cache_hit_rate,
                redact_json(sample.attributes),
            ),
        )
    return len(samples)


def row_to_hardware_sample(row) -> HardwareTelemetrySample:
    return HardwareTelemetrySample(
        sample_id=row["sample_id"],
        task_id=row["task_id"],
        timestamp=row["timestamp"],
        backend_id=row["backend_id"],
        gpu_utilization_percent=row["gpu_utilization_percent"],
        cpu_utilization_percent=row["cpu_utilization_percent"],
        gpu_memory_used_percent=row["gpu_memory_used_percent"],
        queue_depth=row["queue_depth"],
        prefill_ms=row["prefill_ms"],
        decode_ms=row["decode_ms"],
        kv_cache_hit_rate=row["kv_cache_hit_rate"],
        attributes=json.loads(row["attributes_json"]),
    )


def list_hardware_telemetry_samples(conn: Connection, task_id: str) -> list[HardwareTelemetrySample]:
    rows = conn.execute(
        "SELECT * FROM hardware_telemetry_samples WHERE task_id = ? ORDER BY timestamp ASC",
        (task_id,),
    ).fetchall()
    return [row_to_hardware_sample(row) for row in rows]


def list_all_hardware_telemetry_samples(conn: Connection) -> list[HardwareTelemetrySample]:
    rows = conn.execute(
        "SELECT * FROM hardware_telemetry_samples ORDER BY timestamp ASC",
    ).fetchall()
    return [row_to_hardware_sample(row) for row in rows]


def save_hardware_analysis_report(conn: Connection, report: HardwareAnalysisReport) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO hardware_analysis_reports(task_id, report_json)
        VALUES (?, ?)
        """,
        (report.task_id, report.model_dump_json()),
    )


def get_hardware_analysis_report(conn: Connection, task_id: str) -> HardwareAnalysisReport | None:
    row = conn.execute(
        "SELECT report_json FROM hardware_analysis_reports WHERE task_id = ?",
        (task_id,),
    ).fetchone()
    if row is None:
        return None
    return HardwareAnalysisReport.model_validate_json(row["report_json"])


def save_silicon_blueprint_report(conn: Connection, report: SiliconBlueprintReport) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO silicon_blueprint_reports(blueprint_id, name, report_json)
        VALUES (?, ?, ?)
        """,
        (report.blueprint_id, report.name, report.model_dump_json()),
    )


def get_silicon_blueprint_report(conn: Connection, blueprint_id: str) -> SiliconBlueprintReport | None:
    row = conn.execute(
        "SELECT report_json FROM silicon_blueprint_reports WHERE blueprint_id = ?",
        (blueprint_id,),
    ).fetchone()
    if row is None:
        return None
    return SiliconBlueprintReport.model_validate_json(row["report_json"])


def list_silicon_blueprint_reports(conn: Connection) -> list[SiliconBlueprintReport]:
    rows = conn.execute(
        "SELECT report_json FROM silicon_blueprint_reports ORDER BY created_at DESC"
    ).fetchall()
    return [SiliconBlueprintReport.model_validate_json(row["report_json"]) for row in rows]


def save_trace_replay_report(conn: Connection, report: TraceReplayReport) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO trace_replay_reports(replay_id, blueprint_id, report_json)
        VALUES (?, ?, ?)
        """,
        (report.replay_id, report.blueprint_id, report.model_dump_json()),
    )


def get_trace_replay_report(conn: Connection, replay_id: str) -> TraceReplayReport | None:
    row = conn.execute(
        "SELECT report_json FROM trace_replay_reports WHERE replay_id = ?",
        (replay_id,),
    ).fetchone()
    if row is None:
        return None
    return TraceReplayReport.model_validate_json(row["report_json"])


def list_trace_replay_reports(conn: Connection, blueprint_id: str) -> list[TraceReplayReport]:
    rows = conn.execute(
        "SELECT report_json FROM trace_replay_reports WHERE blueprint_id = ? ORDER BY created_at DESC",
        (blueprint_id,),
    ).fetchall()
    return [TraceReplayReport.model_validate_json(row["report_json"]) for row in rows]


def save_measured_validation_experiment(conn: Connection, experiment: MeasuredValidationExperiment) -> MeasuredValidationExperiment:
    experiment_id = experiment.experiment_id or f"experiment_{uuid.uuid4().hex[:12]}"
    saved = experiment.model_copy(update={"experiment_id": experiment_id})
    conn.execute(
        """
        INSERT OR REPLACE INTO measured_validation_experiments(experiment_id, scenario_id, report_json)
        VALUES (?, ?, ?)
        """,
        (experiment_id, saved.scenario_id, saved.model_dump_json()),
    )
    return saved


def list_measured_validation_experiments(conn: Connection) -> list[MeasuredValidationExperiment]:
    rows = conn.execute(
        "SELECT report_json FROM measured_validation_experiments ORDER BY created_at DESC"
    ).fetchall()
    return [MeasuredValidationExperiment.model_validate_json(row["report_json"]) for row in rows]


def save_benchmark_suite_run(conn: Connection, run: BenchmarkSuiteRun) -> BenchmarkSuiteRun:
    benchmark_run_id = run.benchmark_run_id or f"benchmark_{uuid.uuid4().hex[:12]}"
    saved = run.model_copy(update={"benchmark_run_id": benchmark_run_id})
    conn.execute(
        """
        INSERT OR REPLACE INTO benchmark_suite_runs(benchmark_run_id, suite_name, agent_name, report_json)
        VALUES (?, ?, ?, ?)
        """,
        (benchmark_run_id, saved.suite_name, saved.agent_name, saved.model_dump_json()),
    )
    return saved


def list_benchmark_suite_runs(conn: Connection) -> list[BenchmarkSuiteRun]:
    rows = conn.execute(
        "SELECT report_json FROM benchmark_suite_runs ORDER BY created_at DESC"
    ).fetchall()
    return [BenchmarkSuiteRun.model_validate_json(row["report_json"]) for row in rows]


def save_phase1_exit_package(conn: Connection, report: Phase1ExitPackage) -> Phase1ExitPackage:
    package_id = report.package_id or f"phase1_exit_{uuid.uuid4().hex[:12]}"
    saved = report.model_copy(update={"package_id": package_id})
    conn.execute(
        """
        INSERT OR REPLACE INTO phase1_exit_packages(package_id, report_json)
        VALUES (?, ?)
        """,
        (package_id, saved.model_dump_json()),
    )
    return saved


def get_phase1_exit_package(conn: Connection, package_id: str) -> Phase1ExitPackage | None:
    row = conn.execute(
        "SELECT report_json FROM phase1_exit_packages WHERE package_id = ?",
        (package_id,),
    ).fetchone()
    if row is None:
        return None
    return Phase1ExitPackage.model_validate_json(row["report_json"])


def list_phase1_exit_packages(conn: Connection) -> list[Phase1ExitPackage]:
    rows = conn.execute(
        "SELECT report_json FROM phase1_exit_packages ORDER BY created_at DESC"
    ).fetchall()
    return [Phase1ExitPackage.model_validate_json(row["report_json"]) for row in rows]


def save_phase2_handoff_package(conn: Connection, report: Phase2HandoffPackage) -> Phase2HandoffPackage:
    handoff_id = report.handoff_id or f"phase2_handoff_{uuid.uuid4().hex[:12]}"
    saved = report.model_copy(update={"handoff_id": handoff_id})
    conn.execute(
        """
        INSERT OR REPLACE INTO phase2_handoff_packages(handoff_id, report_json)
        VALUES (?, ?)
        """,
        (handoff_id, saved.model_dump_json()),
    )
    return saved


def get_phase2_handoff_package(conn: Connection, handoff_id: str) -> Phase2HandoffPackage | None:
    row = conn.execute(
        "SELECT report_json FROM phase2_handoff_packages WHERE handoff_id = ?",
        (handoff_id,),
    ).fetchone()
    if row is None:
        return None
    return Phase2HandoffPackage.model_validate_json(row["report_json"])


def list_phase2_handoff_packages(conn: Connection) -> list[Phase2HandoffPackage]:
    rows = conn.execute(
        "SELECT report_json FROM phase2_handoff_packages ORDER BY rowid DESC"
    ).fetchall()
    return [Phase2HandoffPackage.model_validate_json(row["report_json"]) for row in rows]


def save_evidence_campaign_report(conn: Connection, report: EvidenceCampaignReport) -> EvidenceCampaignReport:
    campaign_id = report.campaign_id or f"campaign_{uuid.uuid4().hex[:12]}"
    saved = report.model_copy(update={"campaign_id": campaign_id})
    conn.execute(
        """
        INSERT OR REPLACE INTO evidence_campaign_reports(campaign_id, report_json)
        VALUES (?, ?)
        """,
        (campaign_id, saved.model_dump_json()),
    )
    return saved


def get_evidence_campaign_report(conn: Connection, campaign_id: str) -> EvidenceCampaignReport | None:
    row = conn.execute(
        "SELECT report_json FROM evidence_campaign_reports WHERE campaign_id = ?",
        (campaign_id,),
    ).fetchone()
    if row is None:
        return None
    return EvidenceCampaignReport.model_validate_json(row["report_json"])


def list_evidence_campaign_reports(conn: Connection) -> list[EvidenceCampaignReport]:
    rows = conn.execute(
        "SELECT report_json FROM evidence_campaign_reports ORDER BY rowid DESC"
    ).fetchall()
    return [EvidenceCampaignReport.model_validate_json(row["report_json"]) for row in rows]
