from collections import Counter, defaultdict
from datetime import UTC, datetime
from sqlite3 import Connection

from app.hardware.analysis import analyze_hardware
from app.schemas import (
    HardwareTelemetrySample,
    Phase2EvidenceNeed,
    TelemetryCorpusReport,
    TelemetryFieldCoverage,
    TelemetryTaskSummary,
)
from app.storage.repositories import list_all_hardware_telemetry_samples, list_events, list_tasks


def _percent(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((part / total) * 100, 2)


def _status(percent: float, ready_percent: float = 70.0) -> str:
    if percent <= 0:
        return "missing"
    if percent >= ready_percent:
        return "ready"
    return "partial"


def _field_coverage(
    field: str,
    samples_by_task: dict[str, list[HardwareTelemetrySample]],
    phase2_use: str,
    next_step: str,
) -> TelemetryFieldCoverage:
    sample_count = 0
    task_count = 0
    for samples in samples_by_task.values():
        present = [sample for sample in samples if getattr(sample, field) is not None]
        sample_count += len(present)
        task_count += int(bool(present))
    percent = _percent(task_count, len(samples_by_task))
    return TelemetryFieldCoverage(
        field=field,
        sample_count=sample_count,
        task_count=task_count,
        percent_of_telemetry_tasks=percent,
        status=_status(percent),
        phase2_use=phase2_use,
        next_step=next_step,
    )


def build_telemetry_corpus_report(conn: Connection) -> TelemetryCorpusReport:
    tasks = list_tasks(conn)
    task_by_id = {task.task_id: task for task in tasks}
    samples = list_all_hardware_telemetry_samples(conn)
    samples_by_task: dict[str, list[HardwareTelemetrySample]] = defaultdict(list)
    for sample in samples:
        samples_by_task[sample.task_id].append(sample)

    backend_ids = {sample.backend_id for sample in samples}
    telemetry_task_count = len(samples_by_task)
    telemetry_coverage = _percent(telemetry_task_count, len(tasks))

    field_coverage = [
        _field_coverage(
            "gpu_utilization_percent",
            samples_by_task,
            "Tests whether queued agent work corresponds to GPU underutilization or saturated GPU phases.",
            "Import backend/system telemetry with GPU utilization sampled during model and tool spans.",
        ),
        _field_coverage(
            "cpu_utilization_percent",
            samples_by_task,
            "Captures CPU-side orchestration pressure that can starve GPU work in agent loops.",
            "Add CPU utilization, orchestrator saturation, or runtime control-plane metrics to telemetry exports.",
        ),
        _field_coverage(
            "gpu_memory_used_percent",
            samples_by_task,
            "Measures memory pressure that informs HBM/DRAM/CXL/warm-context architecture decisions.",
            "Record memory usage during context-heavy and repeated-prefix tasks.",
        ),
        _field_coverage(
            "queue_depth",
            samples_by_task,
            "Feeds backend/system queueing and scheduler gap analysis for bursty agent workloads.",
            "Import queue depth from serving backend, runtime gateway, or fabric layer during each trace.",
        ),
        _field_coverage(
            "prefill_ms",
            samples_by_task,
            "Separates prefill-heavy context work from decode-heavy token generation.",
            "Record prefill and decode timing together for every model call when backend exposes it.",
        ),
        _field_coverage(
            "decode_ms",
            samples_by_task,
            "Separates decode-heavy interactive generation from prefill-heavy context ingestion.",
            "Record prefill and decode timing together for every model call when backend exposes it.",
        ),
        _field_coverage(
            "kv_cache_hit_rate",
            samples_by_task,
            "Validates whether repeated context actually becomes backend/system cache reuse.",
            "Import real cache hit/miss metrics from vLLM/SGLang/LMCache/Dynamo-style backends when available.",
        ),
    ]

    bottleneck_counts: Counter[str] = Counter()
    task_summaries: list[TelemetryTaskSummary] = []
    for task_id, task_samples in samples_by_task.items():
        task = task_by_id.get(task_id)
        report = analyze_hardware(task_id, list_events(conn, task_id), task_samples)
        categories = [bottleneck.category for bottleneck in report.bottlenecks]
        bottleneck_counts.update(categories)
        task_summaries.append(
            TelemetryTaskSummary(
                task_id=task_id,
                goal=task.goal if task else task_id,
                sample_count=len(task_samples),
                backend_ids=sorted({sample.backend_id for sample in task_samples}),
                has_gpu_utilization=any(sample.gpu_utilization_percent is not None for sample in task_samples),
                has_cpu_utilization=any(sample.cpu_utilization_percent is not None for sample in task_samples),
                has_memory_pressure=any(sample.gpu_memory_used_percent is not None for sample in task_samples),
                has_queue_depth=any(sample.queue_depth is not None for sample in task_samples),
                has_prefill_decode=any(sample.prefill_ms is not None for sample in task_samples)
                and any(sample.decode_ms is not None for sample in task_samples),
                has_cache_hit_rate=any(sample.kv_cache_hit_rate is not None for sample in task_samples),
                detected_bottlenecks=categories,
            )
        )

    gpu_percent = next(item.percent_of_telemetry_tasks for item in field_coverage if item.field == "gpu_utilization_percent")
    cpu_percent = next(item.percent_of_telemetry_tasks for item in field_coverage if item.field == "cpu_utilization_percent")
    memory_percent = next(item.percent_of_telemetry_tasks for item in field_coverage if item.field == "gpu_memory_used_percent")
    queue_percent = next(item.percent_of_telemetry_tasks for item in field_coverage if item.field == "queue_depth")
    prefill_percent = next(item.percent_of_telemetry_tasks for item in field_coverage if item.field == "prefill_ms")
    decode_percent = next(item.percent_of_telemetry_tasks for item in field_coverage if item.field == "decode_ms")
    cache_percent = next(item.percent_of_telemetry_tasks for item in field_coverage if item.field == "kv_cache_hit_rate")

    readiness_score = min(
        100,
        round(telemetry_coverage * 0.20)
        + round(gpu_percent * 0.12)
        + round(cpu_percent * 0.10)
        + round(memory_percent * 0.12)
        + round(queue_percent * 0.12)
        + round(((prefill_percent + decode_percent) / 2) * 0.14)
        + round(cache_percent * 0.12)
        + min(8, len(backend_ids) * 4),
    )
    readiness_status = "missing" if not samples else "ready" if readiness_score >= 75 and telemetry_task_count >= 10 else "partial"

    phase2_evidence_value = [
        Phase2EvidenceNeed(
            need_id="gpu_underutilization",
            label="GPU Utilization Collapse",
            status=_status(gpu_percent),
            evidence=f"{gpu_percent}% of telemetry tasks include GPU utilization.",
            phase2_use="Tests the YC RFS hypothesis that agentic loops leave GPUs underutilized while work is queued elsewhere.",
            next_step="Collect GPU utilization for more real agent runs with queue depth and span timestamps.",
        ),
        Phase2EvidenceNeed(
            need_id="cpu_orchestration_pressure",
            label="CPU Orchestration Pressure",
            status=_status(cpu_percent),
            evidence=f"{cpu_percent}% of telemetry tasks include CPU utilization.",
            phase2_use="Shows whether CPU-side orchestration, parsing, file I/O, or scheduling blocks backend/system acceleration.",
            next_step="Add CPU/orchestrator utilization metrics to backend/system telemetry fixtures.",
        ),
        Phase2EvidenceNeed(
            need_id="memory_pressure",
            label="Memory Pressure",
            status=_status(memory_percent),
            evidence=f"{memory_percent}% of telemetry tasks include GPU memory usage.",
            phase2_use="Feeds memory hierarchy sizing for HBM, DRAM, CXL, NVMe, and warm context tiers.",
            next_step="Record memory usage on context-heavy and repeated-prefix traces.",
        ),
        Phase2EvidenceNeed(
            need_id="prefill_decode_split",
            label="Prefill / Decode Split",
            status=_status(min(prefill_percent, decode_percent)),
            evidence=f"{prefill_percent}% include prefill timing and {decode_percent}% include decode timing.",
            phase2_use="Separates prompt/context ingestion from token generation for backend/system architecture choices.",
            next_step="Import backend/system timing that separates prefill and decode for every model call.",
        ),
        Phase2EvidenceNeed(
            need_id="cache_hit_miss_behavior",
            label="Cache Hit / Miss Behavior",
            status=_status(cache_percent),
            evidence=f"{cache_percent}% of telemetry tasks include KV/cache hit rate.",
            phase2_use="Validates whether Phase 1 repeated-context opportunities become real backend cache reuse.",
            next_step="Import real cache hit/miss metrics from cache-aware serving backends when available.",
        ),
    ]

    return TelemetryCorpusReport(
        generated_at=datetime.now(UTC).isoformat(),
        task_count=len(tasks),
        telemetry_task_count=telemetry_task_count,
        sample_count=len(samples),
        backend_count=len(backend_ids),
        telemetry_task_coverage_percent=telemetry_coverage,
        field_coverage=field_coverage,
        phase2_evidence_value=phase2_evidence_value,
        bottleneck_counts=dict(bottleneck_counts),
        task_summaries=task_summaries[:25],
        readiness_score=readiness_score,
        readiness_status=readiness_status,
        limitations=[
            "Phase 1.3 summarizes imported backend/system/hardware telemetry only; it does not poll live GPUs, clusters, gateways, or fabrics.",
            "Telemetry readiness is not backend/system/hardware validation and does not prove hardware speedup.",
            "KV/cache hit rate is measured only when backend/system telemetry provides it; repeated context alone is not a real cache hit.",
        ],
        next_steps=[
            "Import telemetry for more real coding-agent runs, not only controlled fixtures.",
            "Capture GPU, CPU, memory, queue, prefill/decode, cache, and fabric/network symptoms in the same trace window where available.",
            "Use telemetry coverage to decide which Phase 2 backend/system/hardware gap analyses are evidence-backed.",
        ],
    )
