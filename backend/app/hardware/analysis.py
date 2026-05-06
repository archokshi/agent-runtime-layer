from datetime import datetime
from statistics import mean

from app.analyzer.engine import parse_ts
from app.schemas import (
    CorrelatedHardwareWindow,
    Event,
    HardwareAnalysisReport,
    HardwareBottleneck,
    HardwareSummary,
    HardwareTelemetrySample,
)


def _avg(values: list[float | int | None]) -> float | None:
    clean = [float(value) for value in values if value is not None]
    return round(mean(clean), 2) if clean else None


def _max_int(values: list[int | None]) -> int | None:
    clean = [int(value) for value in values if value is not None]
    return max(clean) if clean else None


def summarize(samples: list[HardwareTelemetrySample]) -> HardwareSummary:
    return HardwareSummary(
        sample_count=len(samples),
        avg_gpu_utilization_percent=_avg([sample.gpu_utilization_percent for sample in samples]),
        avg_cpu_utilization_percent=_avg([sample.cpu_utilization_percent for sample in samples]),
        avg_gpu_memory_used_percent=_avg([sample.gpu_memory_used_percent for sample in samples]),
        max_queue_depth=_max_int([sample.queue_depth for sample in samples]),
        avg_prefill_ms=_avg([sample.prefill_ms for sample in samples]),
        avg_decode_ms=_avg([sample.decode_ms for sample in samples]),
        avg_kv_cache_hit_rate=_avg([sample.kv_cache_hit_rate for sample in samples]),
    )


def _samples_between(samples: list[HardwareTelemetrySample], start: datetime, end: datetime) -> list[HardwareTelemetrySample]:
    return [
        sample for sample in samples
        if start <= parse_ts(sample.timestamp) <= end
    ]


def correlate_windows(events: list[Event], samples: list[HardwareTelemetrySample]) -> list[CorrelatedHardwareWindow]:
    starts = {
        event.span_id: event
        for event in events
        if event.event_type in {"model_call_start", "tool_call_start"}
    }
    windows: list[CorrelatedHardwareWindow] = []
    for event in events:
        if event.event_type not in {"model_call_end", "tool_call_end"}:
            continue
        start_event = starts.get(event.span_id)
        if start_event is None:
            continue
        start_ts = parse_ts(start_event.timestamp)
        end_ts = parse_ts(event.timestamp)
        window_samples = _samples_between(samples, start_ts, end_ts)
        windows.append(CorrelatedHardwareWindow(
            span_id=event.span_id,
            event_name=start_event.name,
            event_type=start_event.event_type.replace("_start", ""),
            start_timestamp=start_event.timestamp,
            end_timestamp=event.timestamp,
            sample_count=len(window_samples),
            avg_gpu_utilization_percent=_avg([sample.gpu_utilization_percent for sample in window_samples]),
            avg_gpu_memory_used_percent=_avg([sample.gpu_memory_used_percent for sample in window_samples]),
            avg_queue_depth=_avg([sample.queue_depth for sample in window_samples]),
            avg_prefill_ms=_avg([sample.prefill_ms for sample in window_samples]),
            avg_decode_ms=_avg([sample.decode_ms for sample in window_samples]),
            avg_kv_cache_hit_rate=_avg([sample.kv_cache_hit_rate for sample in window_samples]),
        ))
    return windows


def classify_bottlenecks(summary: HardwareSummary, windows: list[CorrelatedHardwareWindow]) -> list[HardwareBottleneck]:
    bottlenecks: list[HardwareBottleneck] = []
    if summary.max_queue_depth is not None and summary.max_queue_depth >= 4:
        bottlenecks.append(HardwareBottleneck(
            bottleneck_id="hardware:queue-depth",
            category="queue_saturation",
            title="Backend queue saturation",
            evidence=f"Max imported backend queue depth reached {summary.max_queue_depth}.",
            recommendation="Route non-foreground work to a less saturated backend or defer it until queue depth drops.",
            confidence=0.78,
            metrics={"max_queue_depth": summary.max_queue_depth},
        ))
    if summary.avg_gpu_memory_used_percent is not None and summary.avg_gpu_memory_used_percent >= 85:
        bottlenecks.append(HardwareBottleneck(
            bottleneck_id="hardware:memory-pressure",
            category="memory_pressure",
            title="GPU memory pressure",
            evidence=f"Average GPU memory usage is {summary.avg_gpu_memory_used_percent:.1f}%.",
            recommendation="Reduce active context volume, lower concurrency, or route to a backend with more memory headroom.",
            confidence=0.74,
            metrics={"avg_gpu_memory_used_percent": summary.avg_gpu_memory_used_percent},
        ))
    if summary.avg_kv_cache_hit_rate is not None and summary.avg_kv_cache_hit_rate < 0.3:
        bottlenecks.append(HardwareBottleneck(
            bottleneck_id="hardware:cache-miss-pressure",
            category="cache_miss_pressure",
            title="Low KV/cache hit rate",
            evidence=f"Average imported KV/cache hit rate is {summary.avg_kv_cache_hit_rate:.2f}.",
            recommendation="Use stable-prefix packaging and cache-local routing for repeated context workloads.",
            confidence=0.72,
            metrics={"avg_kv_cache_hit_rate": summary.avg_kv_cache_hit_rate},
        ))
    if summary.avg_prefill_ms is not None and summary.avg_decode_ms is not None and summary.avg_prefill_ms >= max(1000, summary.avg_decode_ms * 2):
        bottlenecks.append(HardwareBottleneck(
            bottleneck_id="hardware:prefill",
            category="prefill_bottleneck",
            title="Prefill-heavy backend time",
            evidence=f"Average prefill time is {summary.avg_prefill_ms:.0f}ms versus decode {summary.avg_decode_ms:.0f}ms.",
            recommendation="Prefer prefix-cache-capable backends or prefill-optimized capacity for this task shape.",
            confidence=0.76,
            metrics={"avg_prefill_ms": summary.avg_prefill_ms, "avg_decode_ms": summary.avg_decode_ms},
        ))
    if summary.avg_decode_ms is not None and summary.avg_prefill_ms is not None and summary.avg_decode_ms >= max(1000, summary.avg_prefill_ms * 2):
        bottlenecks.append(HardwareBottleneck(
            bottleneck_id="hardware:decode",
            category="decode_bottleneck",
            title="Decode-heavy backend time",
            evidence=f"Average decode time is {summary.avg_decode_ms:.0f}ms versus prefill {summary.avg_prefill_ms:.0f}ms.",
            recommendation="Prefer backend capacity with decode throughput headroom for this workload.",
            confidence=0.7,
            metrics={"avg_prefill_ms": summary.avg_prefill_ms, "avg_decode_ms": summary.avg_decode_ms},
        ))
    if summary.avg_gpu_utilization_percent is not None and summary.avg_gpu_utilization_percent < 35 and summary.max_queue_depth is not None and summary.max_queue_depth >= 2:
        bottlenecks.append(HardwareBottleneck(
            bottleneck_id="hardware:gpu-underutilized",
            category="gpu_underutilized",
            title="GPU underutilized while work is queued",
            evidence=f"Average GPU utilization is {summary.avg_gpu_utilization_percent:.1f}% while queue depth reaches {summary.max_queue_depth}.",
            recommendation="Investigate scheduler/backpressure gaps or CPU-side bottlenecks before increasing GPU capacity.",
            confidence=0.66,
            metrics={"avg_gpu_utilization_percent": summary.avg_gpu_utilization_percent, "max_queue_depth": summary.max_queue_depth},
        ))
    if not bottlenecks:
        bottlenecks.append(HardwareBottleneck(
            bottleneck_id="hardware:no-clear-bottleneck",
            category="no_clear_bottleneck",
            title="No clear hardware bottleneck",
            evidence="Imported telemetry does not cross queue, memory, cache, prefill, decode, or utilization thresholds.",
            recommendation="Collect more telemetry samples or inspect the software trace bottlenecks first.",
            confidence=0.55,
            metrics={},
        ))
    return bottlenecks


def analyze_hardware(task_id: str, events: list[Event], samples: list[HardwareTelemetrySample]) -> HardwareAnalysisReport:
    summary = summarize(samples)
    windows = correlate_windows(events, samples)
    bottlenecks = classify_bottlenecks(summary, windows)
    return HardwareAnalysisReport(
        task_id=task_id,
        summary=summary,
        correlated_windows=windows,
        bottlenecks=bottlenecks,
        notes="Imported telemetry correlation only. v3.0 does not require live GPU metrics and is not full cluster monitoring.",
    )
