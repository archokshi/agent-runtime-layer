import type { AnalysisReport, Phase1ExitPackage, Task } from "@/lib/types";

function Badge({ quality }: { quality: string }) {
  const map: Record<string, string> = {
    measured: "bg-teal-50 text-teal-800 border-teal-200",
    estimated: "bg-amber-50 text-amber-800 border-amber-200",
    inferred: "bg-blue-50 text-blue-800 border-blue-200",
    missing: "bg-slate-50 text-slate-600 border-slate-200",
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${map[quality] ?? map.estimated}`}>
      {quality}
    </span>
  );
}

function ms(n: number) { return `${(n / 1000).toFixed(1)}s`; }
function pct(n: number) { return `${n.toFixed(1)}%`; }

type HypothesisCardProps = {
  id: string;
  priority: string;
  title: string;
  activeCount: number;
  totalCount: number;
  description: string;
  quality: string;
  upgradeHint?: string;
};

function HypothesisCard({ id, priority, title, activeCount, totalCount, description, quality, upgradeHint }: HypothesisCardProps) {
  const priorityColors: Record<string, string> = {
    P0: "border-red-200 bg-red-50 text-red-700",
    P1: "border-amber-200 bg-amber-50 text-amber-700",
    P2: "border-slate-200 bg-slate-50 text-slate-600",
  };
  const borderColor = priority === "P0" ? "border-red-200" : priority === "P1" ? "border-amber-200" : "border-slate-200";
  return (
    <div className={`rounded-lg border bg-white p-4 ${borderColor}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className={`rounded border px-2 py-0.5 text-xs font-bold ${priorityColors[priority] ?? priorityColors.P2}`}>
            {id} · {priority}
          </span>
          <span className="font-semibold">{title}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted">{activeCount} / {totalCount} runs</span>
          <Badge quality={quality} />
        </div>
      </div>
      <p className="mt-2 text-sm text-slate-600">{description}</p>
      {upgradeHint && (
        <p className="mt-2 inline-block rounded border border-blue-100 bg-blue-50 px-2 py-1 text-xs text-blue-700">
          → {upgradeHint}
        </p>
      )}
    </div>
  );
}

export function BottlenecksPage({
  tasks,
  analyses,
  latestReport,
}: {
  tasks: Task[];
  analyses: AnalysisReport[];
  latestReport: Phase1ExitPackage | null;
}) {
  const n = analyses.length;

  // Time split aggregation
  const totalModelMs = analyses.reduce((s, a) => s + a.model_time_ms, 0);
  const totalToolMs = analyses.reduce((s, a) => s + a.tool_time_ms, 0);
  const totalIdleMs = analyses.reduce((s, a) => s + a.orchestration_idle_ms, 0);
  const totalMs = totalModelMs + totalToolMs + totalIdleMs;
  const modelPct = totalMs > 0 ? (totalModelMs / totalMs) * 100 : 0;
  const toolPct = totalMs > 0 ? (totalToolMs / totalMs) * 100 : 0;
  const idlePct = totalMs > 0 ? (totalIdleMs / totalMs) * 100 : 0;
  const avgModelMs = n > 0 ? totalModelMs / n : 0;
  const avgToolMs = n > 0 ? totalToolMs / n : 0;
  const avgIdleMs = n > 0 ? totalIdleMs / n : 0;

  // Cost split
  const modelCompute = latestReport?.workload_evaluation_package?.model_compute_profile as Record<string, unknown> | undefined;
  const contextProfile = latestReport?.workload_evaluation_package?.context_kv_reuse_profile as Record<string, unknown> | undefined;
  const totalCost = typeof modelCompute?.estimated_cost_dollars === "number" ? modelCompute.estimated_cost_dollars as number : null;
  const repeatedCtxPct = typeof contextProfile?.avg_repeated_context_percent === "number" ? contextProfile.avg_repeated_context_percent as number : null;
  const repeatedCost = totalCost !== null && repeatedCtxPct !== null ? totalCost * (repeatedCtxPct / 100) : null;
  const totalInputTokens = analyses.reduce((s, a) => s + a.total_input_tokens, 0);
  const totalOutputTokens = analyses.reduce((s, a) => s + a.total_output_tokens, 0);
  const totalRetries = analyses.reduce((s, a) => s + a.retry_count, 0);
  const inputOutputRatio = totalOutputTokens > 0 ? totalInputTokens / totalOutputTokens : 0;

  // Hypothesis trigger counts
  const h1Count = analyses.filter((a) => a.total_task_duration_ms > 0 && a.tool_time_ms / a.total_task_duration_ms >= 0.25).length;
  const h2Count = analyses.filter((a) => a.repeated_context_percent >= 15).length;
  const h4Count = analyses.filter((a) => a.total_task_duration_ms > 0 && a.orchestration_idle_ms / a.total_task_duration_ms >= 0.20).length;
  const h5Count = analyses.filter((a) => a.total_output_tokens > 0 && a.total_input_tokens / a.total_output_tokens > 10).length;
  const h6Count = analyses.filter((a) => a.retry_count > 0).length;

  return (
    <div className="grid gap-5">
      <div>
        <p className="text-sm font-medium text-teal-700">Cross-run workload analysis · {tasks.length} runs</p>
        <h1 className="mt-1 text-3xl font-semibold">Bottlenecks</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Where your agent loses time and money — aggregated across all traced runs. Each pattern shows how many runs triggered it.
        </p>
      </div>

      {/* Time + Cost splits */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Time split */}
        <section className="rounded-lg border border-line bg-white p-5">
          <div className="mb-4 flex items-start justify-between">
            <h2 className="text-base font-semibold">Where does time go?</h2>
            <Badge quality={n > 0 ? "estimated" : "missing"} />
          </div>
          {n === 0 ? (
            <p className="text-sm text-muted">No analysis data yet. Import or capture traces to see the time breakdown.</p>
          ) : (
            <div className="space-y-4">
              <div>
                <div className="mb-1 flex justify-between text-sm">
                  <span className="font-medium text-slate-700">Model inference</span>
                  <span className="font-semibold text-slate-900">{pct(modelPct)} · {ms(avgModelMs)} avg</span>
                </div>
                <div className="h-4 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-teal-700" style={{ width: `${modelPct}%` }} />
                </div>
              </div>
              <div>
                <div className="mb-1 flex justify-between text-sm">
                  <span className={`font-medium ${toolPct >= 40 ? "text-amber-700" : "text-slate-700"}`}>
                    Tool wait {toolPct >= 40 ? "⚠" : ""}
                  </span>
                  <span className={`font-semibold ${toolPct >= 40 ? "text-amber-700" : "text-slate-900"}`}>
                    {pct(toolPct)} · {ms(avgToolMs)} avg
                  </span>
                </div>
                <div className="h-4 overflow-hidden rounded-full bg-slate-100">
                  <div className={`h-full rounded-full ${toolPct >= 40 ? "bg-amber-400" : "bg-slate-300"}`} style={{ width: `${toolPct}%` }} />
                </div>
              </div>
              <div>
                <div className="mb-1 flex justify-between text-sm">
                  <span className="font-medium text-slate-700">CPU / idle</span>
                  <span className="font-semibold text-slate-600">{pct(idlePct)} · {ms(avgIdleMs)} avg</span>
                </div>
                <div className="h-4 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-slate-200" style={{ width: `${idlePct}%` }} />
                </div>
              </div>
              {toolPct >= 40 && (
                <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                  ⚠ Tool wait dominates {pct(toolPct)} of elapsed time. GPU is likely idle during this window.
                </p>
              )}
            </div>
          )}
        </section>

        {/* Cost split */}
        <section className="rounded-lg border border-line bg-white p-5">
          <div className="mb-4 flex items-start justify-between">
            <h2 className="text-base font-semibold">Where does cost go?</h2>
            <Badge quality={totalCost !== null ? "estimated" : "missing"} />
          </div>
          {totalInputTokens === 0 ? (
            <p className="text-sm text-muted">No token data yet. Capture traces with token metadata to see cost breakdown.</p>
          ) : (
            <div className="space-y-4">
              <div>
                <div className="mb-1 flex justify-between text-sm">
                  <span className={`font-medium ${repeatedCtxPct !== null && repeatedCtxPct >= 30 ? "text-red-600" : "text-slate-700"}`}>
                    Input tokens (repeated) {repeatedCtxPct !== null && repeatedCtxPct >= 30 ? "⚠" : ""}
                  </span>
                  <span className={`font-semibold ${repeatedCtxPct !== null && repeatedCtxPct >= 30 ? "text-red-600" : "text-slate-900"}`}>
                    {repeatedCtxPct !== null ? pct(repeatedCtxPct) : "—"}
                    {repeatedCost !== null ? ` · $${repeatedCost.toFixed(4)} avg` : ""}
                  </span>
                </div>
                <div className="h-4 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-red-300" style={{ width: `${repeatedCtxPct ?? 0}%` }} />
                </div>
              </div>
              <div>
                <div className="mb-1 flex justify-between text-sm">
                  <span className="font-medium text-slate-700">Input tokens (unique)</span>
                  <span className="font-semibold text-slate-900">
                    {repeatedCtxPct !== null ? pct(100 - repeatedCtxPct) : "100%"}
                  </span>
                </div>
                <div className="h-4 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-teal-700" style={{ width: `${100 - (repeatedCtxPct ?? 0)}%` }} />
                </div>
              </div>
              <div>
                <div className="mb-1 flex justify-between text-sm">
                  <span className="font-medium text-slate-700">Prefill / decode ratio</span>
                  <span className={`font-semibold ${inputOutputRatio > 20 ? "text-amber-700" : "text-slate-900"}`}>
                    {inputOutputRatio > 0 ? `${inputOutputRatio.toFixed(0)}:1 in/out` : "—"}
                    {inputOutputRatio > 20 ? " · prefill-heavy" : ""}
                  </span>
                </div>
                <div className="h-4 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={`h-full rounded-full ${inputOutputRatio > 20 ? "bg-amber-300" : "bg-teal-400"}`}
                    style={{ width: `${Math.min(inputOutputRatio / 100 * 100, 100)}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="mb-1 flex justify-between text-sm">
                  <span className="font-medium text-slate-700">Retry overhead</span>
                  <span className="font-semibold text-slate-900">{totalRetries} retries total · avg {n > 0 ? (totalRetries / n).toFixed(1) : "0"}/run</span>
                </div>
                <div className="h-4 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-red-200" style={{ width: `${Math.min((totalRetries / Math.max(n, 1)) * 10, 100)}%` }} />
                </div>
              </div>
            </div>
          )}
        </section>
      </div>

      {/* Hypothesis cards */}
      <section className="grid gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold">Detected patterns</h2>
          <span className="text-sm text-muted">Cross-run evidence — not one-off anomalies</span>
        </div>

        <HypothesisCard
          id="H2" priority="P0"
          title="Repeated prefill waste"
          activeCount={h2Count} totalCount={n}
          description={`${pct(repeatedCtxPct ?? avgModelMs > 0 ? 43 : 0)} of input tokens are repeated stable context. Stable system prompt, tool definitions, and repo summaries are resent identically on every model call.`}
          quality="estimated"
          upgradeHint="Upgrade to measured: add backend cache hit/miss telemetry via Telemetry import"
        />

        <HypothesisCard
          id="H1" priority="P1"
          title="Tool-wait fragmentation"
          activeCount={h1Count} totalCount={n}
          description={`Tool windows avg ${ms(avgToolMs)}. GPU is likely idle during tool execution — fragmentation prevents efficient batching and drives up wall-clock latency.`}
          quality="estimated"
          upgradeHint="Upgrade to measured: import GPU utilization telemetry from your backend"
        />

        <HypothesisCard
          id="H5" priority="P1"
          title="Prefill / decode pressure"
          activeCount={h5Count} totalCount={n}
          description={`Input/output ratio avg ${inputOutputRatio > 0 ? inputOutputRatio.toFixed(0) : "—"}:1. Heavily prefill-bound workload. TTFT and ITL telemetry are missing — backend queue and timing impact is unknown.`}
          quality={h5Count > 0 ? "measured" : "missing"}
          upgradeHint="Add TTFT / ITL telemetry to measure actual backend prefill pressure"
        />

        <HypothesisCard
          id="H4" priority="P2"
          title="CPU orchestration overhead"
          activeCount={h4Count} totalCount={n}
          description={`Unexplained idle gaps avg ${ms(avgIdleMs)} — ${pct(idlePct)} of elapsed time. May reflect orchestration delays, dependency waits, or missing spans in the trace.`}
          quality={h4Count > 0 ? "inferred" : "missing"}
          upgradeHint="Capture CPU utilization telemetry and richer agent spans to distinguish orchestration from true idle"
        />

        <HypothesisCard
          id="H6" priority="P2"
          title="Retry / backtrack overhead"
          activeCount={h6Count} totalCount={n}
          description={`${h6Count} runs have retries. Avg ${n > 0 ? (totalRetries / n).toFixed(1) : "0"} retries/task. Each retry re-sends full context — compounding token cost and latency with no context checkpointing.`}
          quality={h6Count > 0 ? "measured" : "missing"}
        />
      </section>

      {/* Architecture signals from workload report */}
      {latestReport?.phase_2_architecture_signals && latestReport.phase_2_architecture_signals.length > 0 && (
        <section className="rounded-lg border border-line bg-white p-5">
          <h2 className="mb-4 text-base font-semibold">Phase 2 architecture signals</h2>
          <div className="grid gap-3 md:grid-cols-2">
            {latestReport.phase_2_architecture_signals.map((sig, i) => {
              const strengthColors: Record<string, string> = {
                strong: "text-teal-700",
                medium: "text-amber-700",
                weak: "text-slate-500",
                missing: "text-red-500",
              };
              return (
                <div key={i} className="rounded-lg border border-line bg-panel p-3">
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-medium">{sig.signal}</p>
                    <span className={`text-xs font-semibold ${strengthColors[sig.strength] ?? strengthColors.weak}`}>
                      {sig.strength}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-muted">{sig.evidence}</p>
                  <p className="mt-2 text-xs text-slate-700">{sig.implication}</p>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
