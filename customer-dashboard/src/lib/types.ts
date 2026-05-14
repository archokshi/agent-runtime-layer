export type Task = {
  task_id: string;
  project_id: string;
  goal: string;
  agent_type: string;
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

export type ContextOptimizationReport = {
  task_id: string;
  optimizer_version: string;
  baseline: { input_tokens: number; repeated_context_percent: number; estimated_cost: number };
  optimized: { input_tokens: number; repeated_context_percent: number; estimated_cost: number };
  savings: { input_token_reduction_percent: number; estimated_cost_reduction_percent: number; estimated_prefill_reduction_percent: number };
  stable_context_blocks: { block_id: string; type: string; fingerprint: string; tokens: number; occurrences: number; action: string }[];
  dynamic_context_blocks: { block_id: string; type: string; fingerprint: string; tokens: number; occurrences: number; action: string }[];
  optimized_prompt_package: { stable_prefix_refs: string[]; dynamic_payload_refs: string[]; notes: string };
  validation: { task_success_preserved?: boolean | null; confidence: string; next_validation_step: string };
};

export type PlatformSummary = {
  platform_version: string;
  mode: string;
  generated_at: string;
  metrics: { label: string; value: string; detail?: string | null }[];
  measured_validation: {
    scenario_name: string;
    measured_input_token_reduction_percent?: number | null;
    measured_cost_reduction_percent?: number | null;
    measured_duration_reduction_percent?: number | null;
    success_preserved?: boolean | null;
  }[];
  benchmark_suite?: { task_count: number; run_count: number; task_success_rate_percent?: number | null } | null;
};

export type Phase1ExitPackage = {
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
  metric_quality_scorecard: { name: string; value: string; evidence: string; quality: "measured" | "estimated" | "inferred" | "missing" }[];
  architecture_readiness_score: number;
};

// Phase 1.7
export type OptimizationProofRecord = {
  proof_id: string;
  baseline_task_id: string;
  optimized_task_id: string | null;
  baseline_input_tokens: number;
  optimized_input_tokens: number;
  baseline_cost_dollars: number;
  optimized_cost_dollars: number;
  token_reduction_percent: number;
  cost_reduction_percent: number;
  success_preserved: boolean | null;
  evidence_quality: string;
  created_at: string | null;
};

// Phase 1.8
export type BudgetConfig = {
  max_cost_per_run: number;
  max_retries_per_task: number;
  alert_threshold: number;
  token_limit_per_call: number;
  enabled: boolean;
};

export type BudgetEvent = {
  event_id: string;
  session_id: string;
  task_id: string | null;
  event_type: string;
  reason: string;
  cost_at_block: number | null;
  retries_at_block: number | null;
  budget_limit: number | null;
  retry_limit: number | null;
  created_at: string | null;
};

export type BudgetGovernorSummary = {
  total_blocked_runs: number;
  total_saved_dollars: number;
  blocks_by_type: Record<string, number>;
  recent_events: BudgetEvent[];
  config: BudgetConfig;
};

// Phase 1.9
export type ContextMemoryEntry = {
  fingerprint: string;
  content_type: string;
  token_count: number;
  source_repo: string | null;
  agent_type: string | null;
  first_seen_at: string | null;
  last_seen_at: string | null;
  hit_count: number;
  cache_savings_dollars: number;
};

export type ContextMemorySummary = {
  total_entries: number;
  total_tokens_memorized: number;
  total_hit_count: number;
  total_cache_savings_dollars: number;
  top_entries: ContextMemoryEntry[];
  evidence_quality: string;
  message: string;
};
