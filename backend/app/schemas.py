from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


EventType = Literal[
    "task_start",
    "task_end",
    "model_call_start",
    "model_call_end",
    "tool_call_start",
    "tool_call_end",
    "context_snapshot",
    "file_event",
    "terminal_event",
    "cache_event",
    "error_event",
    "recommendation_event",
]


class TaskCreate(BaseModel):
    project_id: str = "default"
    goal: str
    agent_type: str = "coding_agent"
    budget_dollars: float | None = None
    latency_slo_seconds: int | None = None
    priority: Literal["foreground", "background", "high", "normal", "low"] | None = None
    task_id: str | None = None
    benchmark_name: str | None = None
    benchmark_task_id: str | None = None
    repo_name: str | None = None
    issue_id: str | None = None
    agent_name: str | None = None
    baseline_or_optimized: Literal["baseline", "optimized"] | None = None
    task_success: bool | None = None
    tests_passed: int | None = None
    tests_failed: int | None = None
    patch_generated: bool | None = None
    files_changed_count: int | None = None
    retry_count: int | None = None
    before_after_pair_id: str | None = None


class Task(BaseModel):
    task_id: str
    project_id: str
    goal: str
    agent_type: str
    budget_dollars: float | None = None
    latency_slo_seconds: int | None = None
    priority: str | None = None
    status: str = "running"
    summary: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    benchmark_name: str | None = None
    benchmark_task_id: str | None = None
    repo_name: str | None = None
    issue_id: str | None = None
    agent_name: str | None = None
    baseline_or_optimized: str | None = None
    task_success: bool | None = None
    tests_passed: int | None = None
    tests_failed: int | None = None
    patch_generated: bool | None = None
    files_changed_count: int | None = None
    retry_count: int | None = None
    before_after_pair_id: str | None = None


class Event(BaseModel):
    event_id: str
    task_id: str
    timestamp: str
    event_type: EventType
    span_id: str
    parent_span_id: str | None = None
    name: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    payload: dict[str, Any] = Field(default_factory=dict)


class TraceImport(BaseModel):
    project_id: str = "default"
    task: TaskCreate
    events: list[Event]


class TaskCreateResponse(BaseModel):
    task_id: str


class TraceImportResponse(BaseModel):
    task_id: str
    event_count: int


class AnalysisReport(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    task_id: str
    total_task_duration_ms: int
    model_time_ms: int
    tool_time_ms: int
    orchestration_idle_ms: int
    model_call_count: int
    tool_call_count: int
    total_input_tokens: int
    total_output_tokens: int
    estimated_total_cost_dollars: float
    repeated_context_tokens_estimate: int
    repeated_context_percent: float
    cache_reuse_opportunity_percent: float
    retry_count: int
    bottleneck_category: str


class BlueprintRecommendation(BaseModel):
    recommendation_id: str
    category: str
    title: str
    rationale: str
    confidence: float
    metrics: dict[str, Any] = Field(default_factory=dict)


class BlueprintPreview(BaseModel):
    task_id: str
    recommendations: list[BlueprintRecommendation]


class OptimizationRecommendation(BaseModel):
    recommendation_id: str
    category: str
    title: str
    evidence: str
    action: str
    estimated_time_savings_ms: int = 0
    estimated_cost_savings_dollars: float = 0.0
    confidence: float
    metrics: dict[str, Any] = Field(default_factory=dict)


class OptimizationReport(BaseModel):
    task_id: str
    recommendations: list[OptimizationRecommendation]


class ValidationComparison(BaseModel):
    before_after_pair_id: str
    baseline_task_id: str | None = None
    optimized_task_id: str | None = None
    repeated_input_token_reduction_percent: float | None = None
    estimated_cost_reduction_percent: float | None = None
    latency_change_percent: float | None = None
    success_preserved: bool | None = None


class ValidationReport(BaseModel):
    task_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    comparison: ValidationComparison | None = None


class ContextBlock(BaseModel):
    block_id: str
    type: str
    fingerprint: str
    tokens: int
    occurrences: int = 1
    action: str


class ContextOptimizationSavings(BaseModel):
    input_token_reduction_percent: float
    estimated_cost_reduction_percent: float
    estimated_prefill_reduction_percent: float


class OptimizedPromptPackage(BaseModel):
    stable_prefix_refs: list[str] = Field(default_factory=list)
    dynamic_payload_refs: list[str] = Field(default_factory=list)
    notes: str


class ContextOptimizationMetrics(BaseModel):
    input_tokens: int
    repeated_context_percent: float
    estimated_cost: float


class ContextOptimizationValidation(BaseModel):
    task_success_preserved: bool | None = None
    confidence: str
    next_validation_step: str


class ContextOptimizationReport(BaseModel):
    task_id: str
    optimizer_version: str = "v1.5"
    baseline: ContextOptimizationMetrics
    optimized: ContextOptimizationMetrics
    savings: ContextOptimizationSavings
    stable_context_blocks: list[ContextBlock] = Field(default_factory=list)
    dynamic_context_blocks: list[ContextBlock] = Field(default_factory=list)
    optimized_prompt_package: OptimizedPromptPackage
    validation: ContextOptimizationValidation


class SchedulerDecision(BaseModel):
    decision_id: str
    category: str
    title: str
    rationale: str
    action: str
    priority: Literal["foreground", "background", "high", "normal", "low"]
    estimated_time_savings_ms: int = 0
    estimated_idle_reduction_ms: int = 0
    confidence: float
    metrics: dict[str, Any] = Field(default_factory=dict)


class SchedulerMetrics(BaseModel):
    naive_duration_ms: int
    scheduled_estimated_duration_ms: int
    estimated_time_savings_ms: int
    idle_reduction_ms: int
    naive_tasks_per_hour: float
    scheduled_tasks_per_hour: float
    tool_wait_ms: int
    idle_ms: int
    retry_count: int
    slo_status: Literal["met", "at_risk", "missed", "unknown"]
    budget_status: Literal["within_budget", "at_risk", "over_budget", "unknown"]


class SchedulerReport(BaseModel):
    task_id: str
    scheduler_version: str = "v2.0"
    mode: str = "local_deterministic_simulation"
    lifecycle_state: str
    task_priority: Literal["foreground", "background", "high", "normal", "low"] = "normal"
    decisions: list[SchedulerDecision] = Field(default_factory=list)
    metrics: SchedulerMetrics
    notes: str


class BackendProfile(BaseModel):
    backend_id: str
    name: str
    backend_type: str
    supports_prefix_cache: bool
    supports_kv_reuse: bool
    queue_depth: int = 0
    max_context_tokens: int | None = None


class ModelCallProfile(BaseModel):
    span_id: str
    model: str | None = None
    role: str | None = None
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cost_dollars: float
    prefill_decode_classification: Literal["prefill_heavy", "decode_heavy", "balanced", "unknown"]
    prefix_overlap_percent: float
    cache_locality: Literal["high", "medium", "low", "unknown"]


class BackendRoutingHint(BaseModel):
    hint_id: str
    category: str
    title: str
    rationale: str
    action: str
    target_backend_id: str | None = None
    confidence: float
    metrics: dict[str, Any] = Field(default_factory=dict)


class BackendAwareMetrics(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    prefix_overlap_estimate_percent: float
    cache_locality: Literal["high", "medium", "low", "unknown"]
    prefill_decode_classification: Literal["prefill_heavy", "decode_heavy", "balanced", "unknown"]
    total_input_tokens: int
    total_output_tokens: int
    model_call_count: int
    queue_depth_observed: int


class BackendAwareReport(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    task_id: str
    backend_runtime_version: str = "v2.5"
    mode: str = "backend_agnostic_hint_generation"
    backend_registry: list[BackendProfile] = Field(default_factory=list)
    model_call_profiles: list[ModelCallProfile] = Field(default_factory=list)
    metrics: BackendAwareMetrics
    routing_hints: list[BackendRoutingHint] = Field(default_factory=list)
    notes: str


class HardwareTelemetrySample(BaseModel):
    sample_id: str | None = None
    task_id: str
    timestamp: str
    backend_id: str
    gpu_utilization_percent: float | None = None
    cpu_utilization_percent: float | None = None
    gpu_memory_used_percent: float | None = None
    queue_depth: int | None = None
    prefill_ms: int | None = None
    decode_ms: int | None = None
    kv_cache_hit_rate: float | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class HardwareTelemetryImport(BaseModel):
    task_id: str
    samples: list[HardwareTelemetrySample]


class HardwareTelemetryImportResponse(BaseModel):
    task_id: str
    sample_count: int


class HardwareBottleneck(BaseModel):
    bottleneck_id: str
    category: str
    title: str
    evidence: str
    recommendation: str
    confidence: float
    metrics: dict[str, Any] = Field(default_factory=dict)


class CorrelatedHardwareWindow(BaseModel):
    span_id: str
    event_name: str
    event_type: str
    start_timestamp: str
    end_timestamp: str
    sample_count: int
    avg_gpu_utilization_percent: float | None = None
    avg_gpu_memory_used_percent: float | None = None
    avg_queue_depth: float | None = None
    avg_prefill_ms: float | None = None
    avg_decode_ms: float | None = None
    avg_kv_cache_hit_rate: float | None = None


class HardwareSummary(BaseModel):
    sample_count: int
    avg_gpu_utilization_percent: float | None = None
    avg_cpu_utilization_percent: float | None = None
    avg_gpu_memory_used_percent: float | None = None
    max_queue_depth: int | None = None
    avg_prefill_ms: float | None = None
    avg_decode_ms: float | None = None
    avg_kv_cache_hit_rate: float | None = None


class HardwareAnalysisReport(BaseModel):
    task_id: str
    hardware_runtime_version: str = "v3.0"
    mode: str = "imported_telemetry_correlation"
    summary: HardwareSummary
    correlated_windows: list[CorrelatedHardwareWindow] = Field(default_factory=list)
    bottlenecks: list[HardwareBottleneck] = Field(default_factory=list)
    notes: str


class SiliconBlueprintGenerateRequest(BaseModel):
    name: str = "Agent Silicon Blueprint"
    task_ids: list[str] | None = None


class WorkloadProfile(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    task_count: int
    model_call_count: int
    tool_call_count: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_dollars: float
    avg_repeated_context_percent: float
    avg_cache_reuse_opportunity_percent: float
    bottleneck_counts: dict[str, int] = Field(default_factory=dict)


class BlueprintArchitectureRecommendation(BaseModel):
    recommendation_id: str
    category: str
    title: str
    rationale: str
    priority: Literal["critical", "high", "medium", "low"]
    confidence: float
    metrics: dict[str, Any] = Field(default_factory=dict)


class HardwarePrimitiveScore(BaseModel):
    primitive: str
    score: float
    rationale: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class SiliconBlueprintValidationSummary(BaseModel):
    local_trace_count: int
    target_trace_count: int = 100
    target_progress_percent: float
    tasks_with_hardware_telemetry: int
    real_world_validation_status: str
    remaining_validation_items: list[str] = Field(default_factory=list)


class SiliconBlueprintReport(BaseModel):
    blueprint_id: str
    name: str
    blueprint_version: str = "v3.5"
    mode: str = "rule_based_architecture_report"
    task_ids: list[str]
    workload_profile: WorkloadProfile
    bottleneck_map: dict[str, int] = Field(default_factory=dict)
    memory_hierarchy_recommendations: list[BlueprintArchitectureRecommendation] = Field(default_factory=list)
    hardware_primitive_rankings: list[HardwarePrimitiveScore] = Field(default_factory=list)
    backend_runtime_recommendations: list[BlueprintArchitectureRecommendation] = Field(default_factory=list)
    benchmark_proposals: list[BlueprintArchitectureRecommendation] = Field(default_factory=list)
    validation_summary: SiliconBlueprintValidationSummary = Field(
        default_factory=lambda: SiliconBlueprintValidationSummary(
            local_trace_count=0,
            target_progress_percent=0.0,
            tasks_with_hardware_telemetry=0,
            real_world_validation_status="legacy_report_without_validation_summary",
            remaining_validation_items=[
                "Regenerate this blueprint report to include current v3.5 validation coverage.",
            ],
        )
    )
    limitations: list[str] = Field(default_factory=list)
    created_at: str | None = None


TraceReplayScenarioId = Literal[
    "persistent_prefix_cache",
    "tool_wait_scheduler",
    "prefill_decode_split",
    "warm_context_tier",
    "kv_compression",
]


class TraceReplayRequest(BaseModel):
    scenario_ids: list[TraceReplayScenarioId] | None = None


class TraceReplayMetrics(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    total_duration_ms: int
    model_time_ms: int
    tool_time_ms: int
    orchestration_idle_ms: int
    input_tokens: int
    output_tokens: int
    estimated_cost_dollars: float
    estimated_prefill_ms: int
    queue_pressure_score: float


class TraceReplayDelta(BaseModel):
    duration_reduction_percent: float
    input_token_reduction_percent: float
    estimated_cost_reduction_percent: float
    estimated_prefill_reduction_percent: float
    queue_pressure_reduction_percent: float


class TraceReplayScenarioResult(BaseModel):
    scenario_id: TraceReplayScenarioId
    name: str
    description: str
    baseline: TraceReplayMetrics
    projected: TraceReplayMetrics
    delta: TraceReplayDelta
    evidence: dict[str, Any] = Field(default_factory=dict)
    confidence: float
    projection_confidence_reason: str = "Rule-based projection from available trace evidence."
    requires_real_backend_validation: bool = True
    validation_evidence_needed: list[str] = Field(default_factory=list)
    notes: str


class TraceReplayReport(BaseModel):
    replay_id: str
    blueprint_id: str
    simulator_version: str = "v4.5"
    mode: str = "rule_based_trace_replay_projection"
    scenario_selection: list[TraceReplayScenarioId] = Field(default_factory=list)
    scenario_results: list[TraceReplayScenarioResult] = Field(default_factory=list)
    best_scenario_id: TraceReplayScenarioId | None = None
    comparison_summary: dict[str, Any] = Field(default_factory=dict)
    aggregate_notes: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    created_at: str | None = None


class PlatformMetricCard(BaseModel):
    label: str
    value: str
    detail: str | None = None


class MeasuredValidationExperiment(BaseModel):
    experiment_id: str | None = None
    scenario_id: str
    scenario_name: str
    baseline_task_id: str | None = None
    optimized_task_id: str | None = None
    projected_duration_reduction_percent: float | None = None
    measured_duration_reduction_percent: float | None = None
    projected_input_token_reduction_percent: float | None = None
    measured_input_token_reduction_percent: float | None = None
    projected_cost_reduction_percent: float | None = None
    measured_cost_reduction_percent: float | None = None
    success_preserved: bool | None = None
    projection_error_percent: float | None = None
    evidence: str
    notes: str
    created_at: str | None = None


class MeasuredValidationExperimentCreate(BaseModel):
    scenario_id: str
    scenario_name: str
    baseline_task_id: str | None = None
    optimized_task_id: str | None = None
    projected_duration_reduction_percent: float | None = None
    measured_duration_reduction_percent: float | None = None
    projected_input_token_reduction_percent: float | None = None
    measured_input_token_reduction_percent: float | None = None
    projected_cost_reduction_percent: float | None = None
    measured_cost_reduction_percent: float | None = None
    success_preserved: bool | None = None
    evidence: str
    notes: str


class BenchmarkSuiteTaskResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    benchmark_task_id: str
    repo_name: str | None = None
    issue_id: str | None = None
    task_id: str | None = None
    trace_complete: bool
    task_success: bool | None = None
    tests_passed: int | None = None
    tests_failed: int | None = None
    patch_generated: bool | None = None
    model_call_count: int = 0
    tool_call_count: int = 0
    retry_count: int = 0
    total_cost_dollars: float = 0.0
    duration_seconds: float = 0.0
    top_bottleneck: str | None = None
    actionable_recommendation: bool | None = None
    notes: str | None = None


class BenchmarkSuiteRunCreate(BaseModel):
    suite_name: Literal["swe-bench", "swe-bench-lite", "swe-bench-verified", "aider", "openhands", "custom"]
    suite_version: str | None = None
    agent_name: str
    agent_version: str | None = None
    run_mode: Literal["official", "smoke", "local", "imported", "dry_run"] = "imported"
    source: str | None = None
    task_results: list[BenchmarkSuiteTaskResult] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class BenchmarkSuiteMetrics(BaseModel):
    task_count: int
    trace_completion_rate_percent: float
    task_success_rate_percent: float | None = None
    actionable_recommendation_rate_percent: float | None = None
    avg_retry_count: float
    avg_duration_seconds: float
    total_cost_dollars: float


class BenchmarkSuiteRun(BaseModel):
    benchmark_run_id: str | None = None
    suite_name: str
    suite_version: str | None = None
    agent_name: str
    agent_version: str | None = None
    run_mode: str
    source: str | None = None
    task_results: list[BenchmarkSuiteTaskResult] = Field(default_factory=list)
    metrics: BenchmarkSuiteMetrics
    limitations: list[str] = Field(default_factory=list)
    created_at: str | None = None


class BenchmarkSuiteSummary(BaseModel):
    run_count: int
    task_count: int
    suite_counts: dict[str, int] = Field(default_factory=dict)
    trace_completion_rate_percent: float
    task_success_rate_percent: float | None = None
    actionable_recommendation_rate_percent: float | None = None
    latest_runs: list[BenchmarkSuiteRun] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class Phase1Metric(BaseModel):
    name: str
    value: str
    evidence: str
    quality: Literal["measured", "estimated", "inferred", "missing"]


class Phase1Recommendation(BaseModel):
    priority: Literal["P0", "P1", "P2", "P3"]
    title: str
    evidence: str
    action: str
    impact: int
    confidence: int
    effort: int
    risk: int
    score: int


class Phase1TestPlanItem(BaseModel):
    platform: str
    test: str
    metrics: list[str] = Field(default_factory=list)
    success_criteria: str


class Phase1ArchitectureSignal(BaseModel):
    signal: str
    strength: Literal["strong", "medium", "weak", "missing"]
    evidence: str
    implication: str


class Phase1ExitPackage(BaseModel):
    package_id: str | None = None
    package_version: str = "phase-1.011"
    mode: str = "phase_1_exit_artifact"
    generated_at: str
    workload_evaluation_package: dict[str, Any] = Field(default_factory=dict)
    workload_recommendation_package: dict[str, Any] = Field(default_factory=dict)
    metric_quality_scorecard: list[Phase1Metric] = Field(default_factory=list)
    architecture_readiness_score: int
    architecture_readiness_rationale: str
    phase_1_5_hardware_test_plan: list[Phase1TestPlanItem] = Field(default_factory=list)
    phase_2_architecture_signals: list[Phase1ArchitectureSignal] = Field(default_factory=list)
    do_not_do_yet: list[str] = Field(default_factory=list)
    created_at: str | None = None


class PlatformReadinessItem(BaseModel):
    category: str
    score: int
    status: Literal["ready", "partial", "missing"]
    rationale: str
    next_step: str


class PlatformRunbookStep(BaseModel):
    step_id: str
    label: str
    status: Literal["complete", "partial", "missing"]
    evidence: str
    next_step: str


class PlatformModuleCoverage(BaseModel):
    module: str
    status: Literal["complete", "partial", "missing"]
    count: int
    description: str


class PlatformSummary(BaseModel):
    platform_version: str = "v5.0"
    mode: str = "local_project_readiness_overview"
    generated_at: str
    metrics: list[PlatformMetricCard] = Field(default_factory=list)
    module_coverage: list[PlatformModuleCoverage] = Field(default_factory=list)
    readiness: list[PlatformReadinessItem] = Field(default_factory=list)
    runbook: list[PlatformRunbookStep] = Field(default_factory=list)
    measured_validation: list[MeasuredValidationExperiment] = Field(default_factory=list)
    benchmark_suite: BenchmarkSuiteSummary | None = None
    latest_blueprint_id: str | None = None
    latest_replay_id: str | None = None
    limitations: list[str] = Field(default_factory=list)
