import type { AnalysisReport, BenchmarkSuiteSummary, Phase1ExitPackage, PlatformSummary, Task } from "@/lib/types";

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

function usd(n: number | null | undefined, digits = 4) {
  if (n == null) return "—";
  if (n < 0.01 && n > 0) return `$${n.toFixed(5)}`;
  return `$${n.toFixed(digits)}`;
}
function pct(n: number | null | undefined) {
  if (n == null) return "—";
  return `${n.toFixed(1)}%`;
}

export function CostExplorer({
  tasks,
  analyses,
  platform,
  latestReport,
  benchmarks,
}: {
  tasks: Task[];
  analyses: AnalysisReport[];
  platform: PlatformSummary | null;
  latestReport: Phase1ExitPackage | null;
  benchmarks: BenchmarkSuiteSummary | null;
}) {
  const n = analyses.length;

  // Aggregate cost metrics
  const totalCost = analyses.reduce((s, a) => s + a.estimated_total_cost_dollars, 0);
  const successCosts = analyses.filter((a) => {
    const task = tasks.find((t) => t.task_id === a.task_id);
    return task?.status === "completed";
  }).map((a) => a.estimated_total_cost_dollars);
  const failedCosts = analyses.filter((a) => {
    const task = tasks.find((t) => t.task_id === a.task_id);
    return task?.status === "failed";
  }).map((a) => a.estimated_total_cost_dollars);
  const avgSuccessCost = successCosts.length > 0 ? successCosts.reduce((s, c) => s + c, 0) / successCosts.length : null;
  const avgFailedCost = failedCosts.length > 0 ? failedCosts.reduce((s, c) => s + c, 0) / failedCosts.length : null;
  const failMultiplier = avgSuccessCost && avgFailedCost ? avgFailedCost / avgSuccessCost : null;

  // Repeated context cost
  const contextProfile = latestReport?.workload_evaluation_package?.context_kv_reuse_profile as Record<string, unknown> | undefined;
  const repeatedCtxPct = typeof contextProfile?.avg_repeated_context_percent === "number" ? contextProfile.avg_repeated_context_percent as number : null;
  const avgCost = n > 0 ? totalCost / n : 0;
  const repeatedCostPerRun = avgCost > 0 && repeatedCtxPct !== null ? avgCost * (repeatedCtxPct / 100) : null;

  // Retry overhead
  const totalRetries = analyses.reduce((s, a) => s + a.retry_count, 0);
  const retryCostEstimate = totalRetries > 0 && avgCost > 0 ? avgCost * (totalRetries / n) * 0.08 : null;

  // Before/after comparison
  const measuredExperiment = platform?.measured_validation?.[0] ?? null;

  // Success rate
  const successRate = benchmarks?.task_success_rate_percent ?? null;
  const successCount = tasks.filter((t) => t.status === "completed").length;
  const failedCount = tasks.filter((t) => t.status === "failed").length;

  // Scatter data (sorted by cost for rendering)
  const scatterData = analyses
    .map((a) => {
      const task = tasks.find((t) => t.task_id === a.task_id);
      return {
        cost: a.estimated_total_cost_dollars,
        retries: a.retry_count,
        success: task?.status === "completed",
        goal: task?.goal ?? a.task_id,
      };
    })
    .filter((d) => d.cost > 0)
    .sort((a, b) => a.cost - b.cost);
  const maxCost = scatterData.length > 0 ? Math.max(...scatterData.map((d) => d.cost)) : 0;

  return (
    <div className="grid gap-5">
      <div>
        <p className="text-sm font-medium text-teal-700">Cost analysis · {tasks.length} runs</p>
        <h1 className="mt-1 text-3xl font-semibold">Cost Explorer</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Where money goes across all traced runs — and what would actually reduce it. Cost per successful task is the most practical metric for agent cost management.
        </p>
      </div>

      {/* Top 4 cards */}
      <section className="grid gap-3 md:grid-cols-4">
        <div className="rounded-lg border border-line bg-white p-4">
          <p className="text-xs font-semibold uppercase text-muted">Total cost</p>
          <p className="mt-3 text-3xl font-semibold">{usd(totalCost)}</p>
          <p className="mt-1 text-sm text-muted">{n} runs · {usd(avgCost)} avg</p>
          <div className="mt-2"><Badge quality={n > 0 ? "estimated" : "missing"} /></div>
        </div>
        <div className="rounded-lg border border-teal-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase text-teal-700">Cost / successful task</p>
          <p className="mt-3 text-3xl font-semibold text-teal-700">{usd(avgSuccessCost)}</p>
          <p className="mt-1 text-sm text-muted">{successCount} successful runs</p>
          <div className="mt-2"><Badge quality={avgSuccessCost !== null ? "estimated" : "missing"} /></div>
        </div>
        <div className="rounded-lg border border-red-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase text-red-600">Cost / failed task</p>
          <p className="mt-3 text-3xl font-semibold text-red-600">{usd(avgFailedCost)}</p>
          <p className="mt-1 text-sm text-muted">
            {failMultiplier !== null ? `${failMultiplier.toFixed(2)}× more than success` : `${failedCount} failed runs`}
          </p>
          <div className="mt-2"><Badge quality={avgFailedCost !== null ? "estimated" : "missing"} /></div>
        </div>
        <div className="rounded-lg border border-amber-200 bg-white p-4">
          <p className="text-xs font-semibold uppercase text-amber-700">Retry overhead / run</p>
          <p className="mt-3 text-3xl font-semibold text-amber-600">{usd(retryCostEstimate)}</p>
          <p className="mt-1 text-sm text-muted">
            {n > 0 ? `avg ${(totalRetries / n).toFixed(1)} retries/run` : "no retry data"}
          </p>
          <div className="mt-2"><Badge quality={retryCostEstimate !== null ? "estimated" : "missing"} /></div>
        </div>
      </section>

      {/* Cost breakdown + Before/After */}
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-lg border border-line bg-white p-5">
          <div className="mb-4 flex items-start justify-between">
            <h2 className="text-base font-semibold">Cost breakdown <span className="text-xs font-normal text-muted">per run average</span></h2>
            <Badge quality={n > 0 ? "estimated" : "missing"} />
          </div>
          {n === 0 ? (
            <p className="text-sm text-muted">No cost data yet. Import traces with token metadata to see the breakdown.</p>
          ) : (
            <div className="space-y-4">
              {repeatedCtxPct !== null && (
                <div>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className={`font-medium ${repeatedCtxPct >= 30 ? "text-red-600" : "text-slate-700"}`}>
                      Input tokens (repeated) {repeatedCtxPct >= 30 ? "⚠" : ""}
                    </span>
                    <span className={`font-semibold ${repeatedCtxPct >= 30 ? "text-red-600" : "text-slate-900"}`}>
                      {pct(repeatedCtxPct)} · {usd(repeatedCostPerRun)}
                    </span>
                  </div>
                  <div className="h-4 overflow-hidden rounded-full bg-slate-100">
                    <div className="h-full rounded-full bg-red-300" style={{ width: `${repeatedCtxPct}%` }} />
                  </div>
                  {repeatedCtxPct >= 30 && (
                    <p className="mt-1 text-xs text-red-600">⚠ {pct(repeatedCtxPct)} is repeated context — recoverable with prefix caching</p>
                  )}
                </div>
              )}
              <div>
                <div className="mb-1 flex justify-between text-sm">
                  <span className="font-medium text-slate-700">Input tokens (unique)</span>
                  <span className="font-semibold text-slate-900">{repeatedCtxPct !== null ? pct(100 - repeatedCtxPct) : "—"}</span>
                </div>
                <div className="h-4 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-teal-700" style={{ width: `${100 - (repeatedCtxPct ?? 0)}%` }} />
                </div>
              </div>
              <div>
                <div className="mb-1 flex justify-between text-sm">
                  <span className="font-medium text-slate-700">Output tokens</span>
                  <span className="font-semibold text-slate-600">~9% of input cost</span>
                </div>
                <div className="h-4 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-teal-400" style={{ width: "9%" }} />
                </div>
              </div>
              {successRate !== null && (
                <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">
                  Task success rate: <span className="font-semibold">{pct(successRate)}</span>
                  {avgFailedCost && avgSuccessCost ? (
                    <span className="ml-2 text-muted">· failed runs cost {(avgFailedCost / avgSuccessCost).toFixed(2)}× more</span>
                  ) : null}
                </div>
              )}
            </div>
          )}
        </section>

        {/* Before / After */}
        <section className="rounded-lg border border-line bg-white p-5">
          <div className="mb-4 flex items-start justify-between">
            <h2 className="text-base font-semibold">Before / After comparison</h2>
            <Badge quality={measuredExperiment ? "measured" : "missing"} />
          </div>
          {measuredExperiment ? (
            <>
              <div className="space-y-3 mb-4">
                <div>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="font-medium text-slate-600">Baseline</span>
                    <span className="font-semibold text-slate-900">
                      {measuredExperiment.measured_input_token_reduction_percent != null ? "before optimization" : measuredExperiment.scenario_name}
                    </span>
                  </div>
                  <div className="h-6 overflow-hidden rounded-full bg-slate-100">
                    <div className="flex h-full items-center justify-end rounded-full bg-slate-400 pr-2" style={{ width: "100%" }}>
                      <span className="text-xs font-medium text-white">baseline</span>
                    </div>
                  </div>
                </div>
                <div>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="font-medium text-teal-700">Optimized</span>
                    <span className="font-semibold text-teal-700">
                      {measuredExperiment.measured_input_token_reduction_percent != null
                        ? `−${measuredExperiment.measured_input_token_reduction_percent.toFixed(1)}% tokens`
                        : `−${measuredExperiment.measured_duration_reduction_percent?.toFixed(1) ?? 0}% duration`}
                    </span>
                  </div>
                  <div className="h-6 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="flex h-full items-center justify-end rounded-full bg-teal-600 pr-2"
                      style={{ width: `${100 - (measuredExperiment.measured_input_token_reduction_percent ?? measuredExperiment.measured_duration_reduction_percent ?? 0)}%` }}
                    >
                      <span className="text-xs font-medium text-white">optimized</span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {measuredExperiment.measured_cost_reduction_percent != null && (
                  <span className="rounded-md border border-teal-200 bg-teal-50 px-3 py-1.5 text-sm font-semibold text-teal-700">
                    −{measuredExperiment.measured_cost_reduction_percent.toFixed(1)}% cost
                  </span>
                )}
                {measuredExperiment.measured_input_token_reduction_percent != null && (
                  <span className="rounded-md border border-teal-200 bg-teal-50 px-3 py-1.5 text-sm font-semibold text-teal-700">
                    −{measuredExperiment.measured_input_token_reduction_percent.toFixed(1)}% tokens
                  </span>
                )}
                {measuredExperiment.success_preserved != null && (
                  <span className="rounded-md border border-teal-200 bg-teal-50 px-3 py-1.5 text-sm font-semibold text-teal-700">
                    Success preserved: {measuredExperiment.success_preserved ? "yes ✓" : "no"}
                  </span>
                )}
              </div>
            </>
          ) : (
            <div className="rounded-lg border border-line bg-panel p-4">
              <p className="text-sm font-medium text-slate-700">No measured comparison yet</p>
              <p className="mt-2 text-sm text-muted">
                Run the context optimizer on a task, then capture the same task again with the optimized prompt. The before/after pair will appear here.
              </p>
            </div>
          )}
        </section>
      </div>

      {/* Scatter plot */}
      {scatterData.length > 0 && (
        <section className="rounded-lg border border-line bg-white p-5">
          <div className="mb-4 flex items-start justify-between">
            <div>
              <h2 className="text-base font-semibold">Cost per run — scatter view</h2>
              <p className="mt-1 text-sm text-muted">Failed runs and high-retry runs cluster at the top. Success runs along the bottom.</p>
            </div>
            <Badge quality="estimated" />
          </div>
          <div className="space-y-2">
            {scatterData.slice(-20).reverse().map((d, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className={`h-2.5 w-2.5 flex-shrink-0 rounded-full ${d.success ? "bg-teal-600" : "bg-red-500"}`} />
                <div className="w-48 truncate text-xs text-slate-600">{d.goal}</div>
                <div className="flex-1">
                  <div className="h-3 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className={`h-full rounded-full ${d.success ? "bg-teal-600" : "bg-red-400"}`}
                      style={{ width: maxCost > 0 ? `${(d.cost / maxCost) * 100}%` : "0%" }}
                    />
                  </div>
                </div>
                <span className={`w-20 text-right text-xs font-semibold ${d.success ? "text-slate-700" : "text-red-600"}`}>
                  {usd(d.cost)}{d.retries > 0 ? ` · ${d.retries}r` : ""}
                </span>
              </div>
            ))}
          </div>
          <div className="mt-4 flex items-center gap-4 text-xs text-muted">
            <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-teal-600 inline-block" /> Success</span>
            <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-red-500 inline-block" /> Failed · r = retries</span>
          </div>
        </section>
      )}
    </div>
  );
}
