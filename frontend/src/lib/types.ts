export type Task = {
  task_id: string;
  project_id: string;
  goal: string;
  agent_type: string;
  budget_dollars?: number;
  latency_slo_seconds?: number;
  priority?: string | null;
  status: string;
  summary?: string;
  started_at?: string;
  ended_at?: string;
};

export type TraceEvent = {
  event_id: string;
  task_id: string;
  timestamp: string;
  event_type: string;
  span_id: string;
  parent_span_id?: string | null;
  name: string;
  attributes: Record<string, unknown>;
  payload: Record<string, unknown>;
};

export type AnalysisReport = {
  task_id: string;
  total_task_duration_ms: number;
  model_time_ms: number;
  tool_time_ms: number;
  orchestration_idle_ms: number;
  model_call_count: number;
  tool_call_count: number;
  total_input_tokens: number;
  total_output_tokens: number;
  estimated_total_cost_dollars: number;
  repeated_context_tokens_estimate: number;
  repeated_context_percent: number;
  cache_reuse_opportunity_percent: number;
  retry_count: number;
  bottleneck_category: string;
};

export type BlueprintPreview = {
  task_id: string;
  recommendations: {
    recommendation_id: string;
    category: string;
    title: string;
    rationale: string;
    confidence: number;
    metrics: Record<string, unknown>;
  }[];
};

export type OptimizationReport = {
  task_id: string;
  recommendations: {
    recommendation_id: string;
    category: string;
    title: string;
    evidence: string;
    action: string;
    estimated_time_savings_ms: number;
    estimated_cost_savings_dollars: number;
    confidence: number;
    metrics: Record<string, unknown>;
  }[];
};

export type ValidationReport = {
  task_id: string;
  metadata: {
    benchmark_name?: string | null;
    benchmark_task_id?: string | null;
    repo_name?: string | null;
    issue_id?: string | null;
    agent_name?: string | null;
    baseline_or_optimized?: string | null;
    task_success?: boolean | null;
    tests_passed?: number | null;
    tests_failed?: number | null;
    patch_generated?: boolean | null;
    files_changed_count?: number | null;
    retry_count?: number | null;
    before_after_pair_id?: string | null;
  };
  comparison?: {
    before_after_pair_id: string;
    baseline_task_id?: string | null;
    optimized_task_id?: string | null;
    repeated_input_token_reduction_percent?: number | null;
    estimated_cost_reduction_percent?: number | null;
    latency_change_percent?: number | null;
    success_preserved?: boolean | null;
  } | null;
};

export type ContextOptimizationReport = {
  task_id: string;
  optimizer_version: string;
  baseline: {
    input_tokens: number;
    repeated_context_percent: number;
    estimated_cost: number;
  };
  optimized: {
    input_tokens: number;
    repeated_context_percent: number;
    estimated_cost: number;
  };
  savings: {
    input_token_reduction_percent: number;
    estimated_cost_reduction_percent: number;
    estimated_prefill_reduction_percent: number;
  };
  stable_context_blocks: {
    block_id: string;
    type: string;
    fingerprint: string;
    tokens: number;
    occurrences: number;
    action: string;
  }[];
  dynamic_context_blocks: {
    block_id: string;
    type: string;
    fingerprint: string;
    tokens: number;
    occurrences: number;
    action: string;
  }[];
  optimized_prompt_package: {
    stable_prefix_refs: string[];
    dynamic_payload_refs: string[];
    notes: string;
  };
  validation: {
    task_success_preserved?: boolean | null;
    confidence: string;
    next_validation_step: string;
  };
};

export type SchedulerReport = {
  task_id: string;
  scheduler_version: string;
  mode: string;
  lifecycle_state: string;
  task_priority: "foreground" | "background" | "high" | "normal" | "low";
  decisions: {
    decision_id: string;
    category: string;
    title: string;
    rationale: string;
    action: string;
    priority: "foreground" | "background" | "high" | "normal" | "low";
    estimated_time_savings_ms: number;
    estimated_idle_reduction_ms: number;
    confidence: number;
    metrics: Record<string, unknown>;
  }[];
  metrics: {
    naive_duration_ms: number;
    scheduled_estimated_duration_ms: number;
    estimated_time_savings_ms: number;
    idle_reduction_ms: number;
    naive_tasks_per_hour: number;
    scheduled_tasks_per_hour: number;
    tool_wait_ms: number;
    idle_ms: number;
    retry_count: number;
    slo_status: "met" | "at_risk" | "missed" | "unknown";
    budget_status: "within_budget" | "at_risk" | "over_budget" | "unknown";
  };
  notes: string;
};

export type BackendAwareReport = {
  task_id: string;
  backend_runtime_version: string;
  mode: string;
  backend_registry: {
    backend_id: string;
    name: string;
    backend_type: string;
    supports_prefix_cache: boolean;
    supports_kv_reuse: boolean;
    queue_depth: number;
    max_context_tokens?: number | null;
  }[];
  model_call_profiles: {
    span_id: string;
    model?: string | null;
    role?: string | null;
    input_tokens: number;
    output_tokens: number;
    latency_ms: number;
    cost_dollars: number;
    prefill_decode_classification: "prefill_heavy" | "decode_heavy" | "balanced" | "unknown";
    prefix_overlap_percent: number;
    cache_locality: "high" | "medium" | "low" | "unknown";
  }[];
  metrics: {
    prefix_overlap_estimate_percent: number;
    cache_locality: "high" | "medium" | "low" | "unknown";
    prefill_decode_classification: "prefill_heavy" | "decode_heavy" | "balanced" | "unknown";
    total_input_tokens: number;
    total_output_tokens: number;
    model_call_count: number;
    queue_depth_observed: number;
  };
  routing_hints: {
    hint_id: string;
    category: string;
    title: string;
    rationale: string;
    action: string;
    target_backend_id?: string | null;
    confidence: number;
    metrics: Record<string, unknown>;
  }[];
  notes: string;
};

export type HardwareAnalysisReport = {
  task_id: string;
  hardware_runtime_version: string;
  mode: string;
  summary: {
    sample_count: number;
    avg_gpu_utilization_percent?: number | null;
    avg_cpu_utilization_percent?: number | null;
    avg_gpu_memory_used_percent?: number | null;
    max_queue_depth?: number | null;
    avg_prefill_ms?: number | null;
    avg_decode_ms?: number | null;
    avg_kv_cache_hit_rate?: number | null;
  };
  correlated_windows: {
    span_id: string;
    event_name: string;
    event_type: string;
    start_timestamp: string;
    end_timestamp: string;
    sample_count: number;
    avg_gpu_utilization_percent?: number | null;
    avg_gpu_memory_used_percent?: number | null;
    avg_queue_depth?: number | null;
    avg_prefill_ms?: number | null;
    avg_decode_ms?: number | null;
    avg_kv_cache_hit_rate?: number | null;
  }[];
  bottlenecks: {
    bottleneck_id: string;
    category: string;
    title: string;
    evidence: string;
    recommendation: string;
    confidence: number;
    metrics: Record<string, unknown>;
  }[];
  notes: string;
};

export type SiliconBlueprintReport = {
  blueprint_id: string;
  name: string;
  blueprint_version: string;
  mode: string;
  task_ids: string[];
  workload_profile: {
    task_count: number;
    model_call_count: number;
    tool_call_count: number;
    total_input_tokens: number;
    total_output_tokens: number;
    total_cost_dollars: number;
    avg_repeated_context_percent: number;
    avg_cache_reuse_opportunity_percent: number;
    bottleneck_counts: Record<string, number>;
  };
  bottleneck_map: Record<string, number>;
  memory_hierarchy_recommendations: {
    recommendation_id: string;
    category: string;
    title: string;
    rationale: string;
    priority: "critical" | "high" | "medium" | "low";
    confidence: number;
    metrics: Record<string, unknown>;
  }[];
  hardware_primitive_rankings: {
    primitive: string;
    score: number;
    rationale: string;
    evidence: Record<string, unknown>;
  }[];
  backend_runtime_recommendations: {
    recommendation_id: string;
    category: string;
    title: string;
    rationale: string;
    priority: "critical" | "high" | "medium" | "low";
    confidence: number;
    metrics: Record<string, unknown>;
  }[];
  benchmark_proposals: {
    recommendation_id: string;
    category: string;
    title: string;
    rationale: string;
    priority: "critical" | "high" | "medium" | "low";
    confidence: number;
    metrics: Record<string, unknown>;
  }[];
  validation_summary: {
    local_trace_count: number;
    target_trace_count: number;
    target_progress_percent: number;
    tasks_with_hardware_telemetry: number;
    real_world_validation_status: string;
    remaining_validation_items: string[];
  };
  limitations: string[];
  created_at?: string | null;
};

export type TraceReplayScenarioId =
  | "persistent_prefix_cache"
  | "tool_wait_scheduler"
  | "prefill_decode_split"
  | "warm_context_tier"
  | "kv_compression";

export type TraceReplayMetrics = {
  total_duration_ms: number;
  model_time_ms: number;
  tool_time_ms: number;
  orchestration_idle_ms: number;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_dollars: number;
  estimated_prefill_ms: number;
  queue_pressure_score: number;
};

export type TraceReplayReport = {
  replay_id: string;
  blueprint_id: string;
  simulator_version: string;
  mode: string;
  scenario_selection: TraceReplayScenarioId[];
  scenario_results: {
    scenario_id: TraceReplayScenarioId;
    name: string;
    description: string;
    baseline: TraceReplayMetrics;
    projected: TraceReplayMetrics;
    delta: {
      duration_reduction_percent: number;
      input_token_reduction_percent: number;
      estimated_cost_reduction_percent: number;
      estimated_prefill_reduction_percent: number;
      queue_pressure_reduction_percent: number;
    };
    evidence: Record<string, unknown>;
    confidence: number;
    projection_confidence_reason: string;
    requires_real_backend_validation: boolean;
    validation_evidence_needed: string[];
    notes: string;
  }[];
  best_scenario_id?: TraceReplayScenarioId | null;
  comparison_summary: Record<string, unknown>;
  aggregate_notes: string[];
  limitations: string[];
  created_at?: string | null;
};

export type PlatformSummary = {
  platform_version: string;
  mode: string;
  generated_at: string;
  metrics: {
    label: string;
    value: string;
    detail?: string | null;
  }[];
  module_coverage: {
    module: string;
    status: "complete" | "partial" | "missing";
    count: number;
    description: string;
  }[];
  readiness: {
    category: string;
    score: number;
    status: "ready" | "partial" | "missing";
    rationale: string;
    next_step: string;
  }[];
  measured_validation: {
    experiment_id?: string | null;
    scenario_id: string;
    scenario_name: string;
    baseline_task_id?: string | null;
    optimized_task_id?: string | null;
    projected_duration_reduction_percent?: number | null;
    measured_duration_reduction_percent?: number | null;
    projected_input_token_reduction_percent?: number | null;
    measured_input_token_reduction_percent?: number | null;
    projected_cost_reduction_percent?: number | null;
    measured_cost_reduction_percent?: number | null;
    success_preserved?: boolean | null;
    projection_error_percent?: number | null;
    evidence: string;
    notes: string;
    created_at?: string | null;
  }[];
  benchmark_suite?: BenchmarkSuiteSummary | null;
  runbook: {
    step_id: string;
    label: string;
    status: "complete" | "partial" | "missing";
    evidence: string;
    next_step: string;
  }[];
  latest_blueprint_id?: string | null;
  latest_replay_id?: string | null;
  limitations: string[];
};

export type BenchmarkSuiteTaskResult = {
  benchmark_task_id: string;
  repo_name?: string | null;
  issue_id?: string | null;
  task_id?: string | null;
  trace_complete: boolean;
  task_success?: boolean | null;
  tests_passed?: number | null;
  tests_failed?: number | null;
  patch_generated?: boolean | null;
  model_call_count: number;
  tool_call_count: number;
  retry_count: number;
  total_cost_dollars: number;
  duration_seconds: number;
  top_bottleneck?: string | null;
  actionable_recommendation?: boolean | null;
  notes?: string | null;
};

export type BenchmarkSuiteRun = {
  benchmark_run_id?: string | null;
  suite_name: string;
  suite_version?: string | null;
  agent_name: string;
  agent_version?: string | null;
  run_mode: string;
  source?: string | null;
  task_results: BenchmarkSuiteTaskResult[];
  metrics: {
    task_count: number;
    trace_completion_rate_percent: number;
    task_success_rate_percent?: number | null;
    actionable_recommendation_rate_percent?: number | null;
    avg_retry_count: number;
    avg_duration_seconds: number;
    total_cost_dollars: number;
  };
  limitations: string[];
  created_at?: string | null;
};

export type BenchmarkSuiteSummary = {
  run_count: number;
  task_count: number;
  suite_counts: Record<string, number>;
  trace_completion_rate_percent: number;
  task_success_rate_percent?: number | null;
  actionable_recommendation_rate_percent?: number | null;
  latest_runs: BenchmarkSuiteRun[];
  limitations: string[];
};

export type Phase1ExitPackage = {
  package_id?: string | null;
  package_version: string;
  mode: string;
  generated_at: string;
  workload_evaluation_package: Record<string, Record<string, unknown>>;
  workload_recommendation_package: {
    executive_recommendation_summary?: string[];
    prioritized_recommendations?: {
      priority: "P0" | "P1" | "P2" | "P3";
      title: string;
      evidence: string;
      action: string;
      impact: number;
      confidence: number;
      effort: number;
      risk: number;
      score: number;
    }[];
    current_infrastructure_action_plan?: string[];
  };
  metric_quality_scorecard: {
    name: string;
    value: string;
    evidence: string;
    quality: "measured" | "estimated" | "inferred" | "missing";
  }[];
  architecture_readiness_score: number;
  architecture_readiness_rationale: string;
  phase_1_5_hardware_test_plan: {
    platform: string;
    test: string;
    metrics: string[];
    success_criteria: string;
  }[];
  phase_2_architecture_signals: {
    signal: string;
    strength: "strong" | "medium" | "weak" | "missing";
    evidence: string;
    implication: string;
  }[];
  do_not_do_yet: string[];
  created_at?: string | null;
};
