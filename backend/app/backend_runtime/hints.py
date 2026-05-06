from app.analyzer.engine import analyze_events
from app.schemas import (
    BackendAwareMetrics,
    BackendAwareReport,
    BackendProfile,
    BackendRoutingHint,
    Event,
    ModelCallProfile,
    Task,
)


DEFAULT_BACKENDS = [
    BackendProfile(
        backend_id="local_default",
        name="Local default backend",
        backend_type="generic",
        supports_prefix_cache=False,
        supports_kv_reuse=False,
        queue_depth=0,
        max_context_tokens=None,
    ),
    BackendProfile(
        backend_id="prefix_cache_capable",
        name="Prefix-cache-capable backend",
        backend_type="vllm_sglang_lmcache_class",
        supports_prefix_cache=True,
        supports_kv_reuse=True,
        queue_depth=0,
        max_context_tokens=None,
    ),
]


def _classification(input_tokens: int, output_tokens: int) -> str:
    if input_tokens <= 0 and output_tokens <= 0:
        return "unknown"
    if input_tokens >= max(1000, output_tokens * 8):
        return "prefill_heavy"
    if output_tokens >= max(500, input_tokens):
        return "decode_heavy"
    return "balanced"


def _cache_locality(prefix_overlap: float) -> str:
    if prefix_overlap >= 30:
        return "high"
    if prefix_overlap >= 10:
        return "medium"
    if prefix_overlap > 0:
        return "low"
    return "unknown"


def _queue_depth(events: list[Event]) -> int:
    values: list[int] = []
    for event in events:
        for key in ("queue_depth", "backend_queue_depth"):
            if key in event.attributes:
                try:
                    values.append(int(event.attributes[key]))
                except (TypeError, ValueError):
                    pass
    return max(values) if values else 0


def _model_call_profiles(events: list[Event], prefix_overlap: float) -> list[ModelCallProfile]:
    starts = {event.span_id: event for event in events if event.event_type == "model_call_start"}
    profiles: list[ModelCallProfile] = []
    for event in events:
        if event.event_type != "model_call_end":
            continue
        start = starts.get(event.span_id)
        input_tokens = int(event.attributes.get("input_tokens", 0))
        output_tokens = int(event.attributes.get("output_tokens", 0))
        profiles.append(ModelCallProfile(
            span_id=event.span_id,
            model=str((start.attributes if start else {}).get("model") or event.attributes.get("model") or "") or None,
            role=str((start.attributes if start else {}).get("role") or event.attributes.get("role") or "") or None,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=int(event.attributes.get("latency_ms", 0)),
            cost_dollars=float(event.attributes.get("cost_dollars", 0.0)),
            prefill_decode_classification=_classification(input_tokens, output_tokens),  # type: ignore[arg-type]
            prefix_overlap_percent=prefix_overlap,
            cache_locality=_cache_locality(prefix_overlap),  # type: ignore[arg-type]
        ))
    return profiles


def generate_backend_hints(task: Task, events: list[Event]) -> BackendAwareReport:
    analysis = analyze_events(task.task_id, events)
    prefix_overlap = max(analysis.repeated_context_percent, analysis.cache_reuse_opportunity_percent)
    classification = _classification(analysis.total_input_tokens, analysis.total_output_tokens)
    cache_locality = _cache_locality(prefix_overlap)
    queue_depth = _queue_depth(events)
    profiles = _model_call_profiles(events, prefix_overlap)
    hints: list[BackendRoutingHint] = []

    if prefix_overlap >= 20:
        hints.append(BackendRoutingHint(
            hint_id=f"{task.task_id}:backend-prefix-cache",
            category="cache_locality",
            title="Prefer a prefix-cache-capable backend",
            rationale=f"Estimated prefix overlap is {prefix_overlap:.1f}%, indicating reusable context.",
            action="Route similar-prefix requests to the same prefix-cache-capable backend class when a real backend integration exists.",
            target_backend_id="prefix_cache_capable",
            confidence=min(0.92, 0.55 + prefix_overlap / 100),
            metrics={"prefix_overlap_estimate_percent": prefix_overlap, "cache_locality": cache_locality},
        ))

    if classification == "prefill_heavy":
        hints.append(BackendRoutingHint(
            hint_id=f"{task.task_id}:backend-prefill-heavy",
            category="prefill_decode",
            title="Mark task as prefill-heavy",
            rationale="Input tokens dominate output tokens, so prefill capacity is likely the critical backend path.",
            action="Prefer a backend pool optimized for high-throughput prefill or prefix reuse when available.",
            target_backend_id="prefix_cache_capable" if prefix_overlap >= 10 else "local_default",
            confidence=0.74,
            metrics={"total_input_tokens": analysis.total_input_tokens, "total_output_tokens": analysis.total_output_tokens},
        ))
    elif classification == "decode_heavy":
        hints.append(BackendRoutingHint(
            hint_id=f"{task.task_id}:backend-decode-heavy",
            category="prefill_decode",
            title="Mark task as decode-heavy",
            rationale="Output tokens are a large share of the model workload.",
            action="Prefer backend capacity with decode throughput headroom when available.",
            target_backend_id="local_default",
            confidence=0.68,
            metrics={"total_input_tokens": analysis.total_input_tokens, "total_output_tokens": analysis.total_output_tokens},
        ))

    if queue_depth >= 4:
        hints.append(BackendRoutingHint(
            hint_id=f"{task.task_id}:backend-queue-aware",
            category="queue_depth",
            title="Avoid saturated backend queue",
            rationale=f"Observed backend queue depth reached {queue_depth}.",
            action="Prefer an equivalent backend with lower queue depth before dispatching non-foreground work.",
            target_backend_id=None,
            confidence=0.66,
            metrics={"queue_depth_observed": queue_depth},
        ))

    if not hints:
        hints.append(BackendRoutingHint(
            hint_id=f"{task.task_id}:backend-noop",
            category="no_action",
            title="No backend routing hint needed",
            rationale="The trace does not show enough prefix overlap, queue pressure, or prefill/decode skew for a backend hint.",
            action="Keep the default backend assignment.",
            target_backend_id="local_default",
            confidence=0.55,
            metrics={"prefix_overlap_estimate_percent": prefix_overlap, "classification": classification},
        ))

    return BackendAwareReport(
        task_id=task.task_id,
        backend_registry=DEFAULT_BACKENDS,
        model_call_profiles=profiles,
        metrics=BackendAwareMetrics(
            prefix_overlap_estimate_percent=prefix_overlap,
            cache_locality=cache_locality,  # type: ignore[arg-type]
            prefill_decode_classification=classification,  # type: ignore[arg-type]
            total_input_tokens=analysis.total_input_tokens,
            total_output_tokens=analysis.total_output_tokens,
            model_call_count=analysis.model_call_count,
            queue_depth_observed=queue_depth,
        ),
        routing_hints=hints,
        notes="Backend-agnostic hint generation only. v2.5 does not call real vLLM, SGLang, LMCache, Dynamo, or perform production load balancing.",
    )
