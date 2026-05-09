import type { AnalysisReport, ContextOptimizationReport, Phase1ExitPackage, Task } from "@/lib/types";

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

function tok(n: number) { return n.toLocaleString(); }
function pct(n: number) { return `${n.toFixed(1)}%`; }
function usd(n: number) { return n < 0.01 && n > 0 ? `$${n.toFixed(5)}` : `$${n.toFixed(4)}`; }

export function ContextInspector({
  tasks,
  analyses,
  contextReport,
  latestReport,
}: {
  tasks: Task[];
  analyses: AnalysisReport[];
  contextReport: ContextOptimizationReport | null;
  latestReport: Phase1ExitPackage | null;
}) {
  const contextProfile = latestReport?.workload_evaluation_package?.context_kv_reuse_profile as Record<string, unknown> | undefined;
  const avgRepeatedFromReport = typeof contextProfile?.avg_repeated_context_percent === "number"
    ? contextProfile.avg_repeated_context_percent as number
    : null;

  const runsWithCtx = analyses.filter((a) => a.repeated_context_percent > 0);
  const avgCtxPct = runsWithCtx.length > 0
    ? runsWithCtx.reduce((s, a) => s + a.repeated_context_percent, 0) / runsWithCtx.length
    : (avgRepeatedFromReport ?? 0);
  const highWasteRuns = analyses.filter((a) => a.repeated_context_percent >= 55).length;

  const stableBlocks = contextReport?.stable_context_blocks ?? [];
  const dynamicBlocks = contextReport?.dynamic_context_blocks ?? [];
  const stableTotal = stableBlocks.reduce((s, b) => s + b.tokens, 0);
  const dynamicTotal = dynamicBlocks.reduce((s, b) => s + b.tokens, 0);
  const baseline = contextReport?.baseline;
  const savings = contextReport?.savings;
  const repeatedTokens = baseline
    ? Math.round(baseline.input_tokens * baseline.repeated_context_percent / 100)
    : stableTotal;
  const recoverableCost = baseline && savings
    ? baseline.estimated_cost * (savings.estimated_cost_reduction_percent / 100)
    : null;

  const featuredTask = contextReport
    ? tasks.find((t) => t.task_id === contextReport.task_id)
    : null;

  return (
    <div className="grid gap-5">
      <div>
        <p className="text-sm font-medium text-teal-700">Context efficiency · {tasks.length} runs</p>
        <h1 className="mt-1 text-3xl font-semibold">Context Inspector</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Shows which tokens you are re-sending on every model call. Stable context — system prompt, tool definitions, repo summary — is identical across calls and is the primary optimization target.
        </p>
      </div>

      {/* Corpus summary cards */}
      <section className="grid gap-3 md:grid-cols-4">
        <div className="rounded-lg border border-line bg-white p-4">
          <p className="text-xs font-semibold uppercase text-muted">Avg repeated ctx</p>
          <p className="mt-3 text-3xl font-semibold">{pct(avgCtxPct)}</p>
          <p className="mt-1 text-sm text-muted">across {tasks.length} runs</p>
          <div className="mt-2"><Badge quality={runsWithCtx.length > 0 ? "estimated" : "missing"} /></div>
        </div>
        <div className="rounded-lg border border-line bg-white p-4">
          <p className="text-xs font-semibold uppercase text-muted">Runs above 55%</p>
          <p className={`mt-3 text-3xl font-semibold ${highWasteRuns > 0 ? "text-red-600" : "text-slate-900"}`}>{highWasteRuns}</p>
          <p className="mt-1 text-sm text-muted">highest waste priority</p>
          <div className="mt-2"><Badge quality="measured" /></div>
        </div>
        <div className="rounded-lg border border-line bg-white p-4">
          <p className="text-xs font-semibold uppercase text-muted">Stable block size</p>
          <p className="mt-3 text-3xl font-semibold">{stableTotal > 0 ? tok(stableTotal) : "—"}</p>
          <p className="mt-1 text-sm text-muted">tokens cacheable / call</p>
          <div className="mt-2"><Badge quality={stableTotal > 0 ? "estimated" : "missing"} /></div>
        </div>
        <div className="rounded-lg border border-line bg-white p-4">
          <p className="text-xs font-semibold uppercase text-muted">Recoverable cost</p>
          <p className="mt-3 text-3xl font-semibold text-teal-700">{recoverableCost !== null ? usd(recoverableCost) : "—"}</p>
          <p className="mt-1 text-sm text-muted">estimated per featured run</p>
          <div className="mt-2"><Badge quality={recoverableCost !== null ? "estimated" : "missing"} /></div>
        </div>
      </section>

      {contextReport ? (
        <>
          {/* Featured run efficiency */}
          <section className="rounded-lg border border-line bg-white p-5">
            <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-base font-semibold">
                  Context efficiency — {featuredTask?.goal ?? contextReport.task_id}
                </h2>
                <p className="mt-1 text-sm text-muted">
                  Run with highest repeated context selected for detailed inspection.
                </p>
              </div>
              <Badge quality="estimated" />
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-lg border border-line bg-panel p-4 text-center">
                <p className="text-xs font-semibold uppercase text-muted">Total input tokens sent</p>
                <p className="mt-2 text-2xl font-semibold">{tok(baseline?.input_tokens ?? 0)}</p>
                <p className="mt-1 text-xs text-muted">all model calls</p>
              </div>
              <div className="rounded-lg border border-teal-200 bg-teal-50 p-4 text-center">
                <p className="text-xs font-semibold uppercase text-teal-700">Unique content</p>
                <p className="mt-2 text-2xl font-semibold text-teal-700">
                  {tok((baseline?.input_tokens ?? 0) - repeatedTokens)}
                </p>
                <p className="mt-1 text-xs text-teal-600">necessary tokens</p>
              </div>
              <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center">
                <p className="text-xs font-semibold uppercase text-red-700">Repeated / wasteable</p>
                <p className="mt-2 text-2xl font-semibold text-red-600">{tok(repeatedTokens)}</p>
                <p className="mt-1 text-xs text-red-600 font-medium">
                  {pct(baseline?.repeated_context_percent ?? 0)} of total
                </p>
              </div>
            </div>
            {savings && (
              <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                If stable context is cached: −{pct(savings.input_token_reduction_percent)} input tokens · estimated {pct(savings.estimated_cost_reduction_percent)} cost saving per run
                <span className="ml-2 inline-flex items-center rounded-full border border-amber-300 bg-amber-100 px-2 py-0.5 text-xs font-semibold">estimated</span>
              </div>
            )}
          </section>

          {/* Block breakdown */}
          <div className="grid gap-4 lg:grid-cols-2">
            <section className="rounded-lg border-2 border-teal-200 bg-white p-5">
              <div className="mb-3 flex items-center gap-2">
                <span className="h-3 w-3 rounded-sm bg-teal-700" />
                <h2 className="font-semibold">Stable — {tok(stableTotal)} tokens</h2>
              </div>
              <p className="mb-4 rounded border border-teal-200 bg-teal-50 px-2 py-1 text-xs text-teal-700">
                Identical across all calls → primary caching target
              </p>
              {stableBlocks.length === 0 ? (
                <p className="text-sm text-muted">
                  No stable blocks detected. Run the context optimizer from a task detail page to classify context blocks.
                </p>
              ) : (
                <div className="space-y-3">
                  {stableBlocks.map((block) => (
                    <div key={block.block_id}>
                      <div className="flex items-center justify-between text-sm">
                        <span className="capitalize text-slate-700">{block.type.replaceAll("_", " ")}</span>
                        <span className="font-semibold text-slate-900">{tok(block.tokens)} tok · {block.occurrences}× seen</span>
                      </div>
                      <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-teal-700"
                          style={{ width: stableTotal > 0 ? `${(block.tokens / stableTotal) * 100}%` : "0%" }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="rounded-lg border border-line bg-white p-5">
              <div className="mb-3 flex items-center gap-2">
                <span className="h-3 w-3 rounded-sm bg-teal-400" />
                <h2 className="font-semibold">Dynamic — {tok(dynamicTotal)} tokens</h2>
              </div>
              <p className="mb-4 rounded border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-600">
                Changes each call → necessary, cannot be cached
              </p>
              {dynamicBlocks.length === 0 ? (
                <p className="text-sm text-muted">
                  No dynamic blocks detected. Run the context optimizer to classify dynamic payload.
                </p>
              ) : (
                <div className="space-y-3">
                  {dynamicBlocks.map((block) => (
                    <div key={block.block_id}>
                      <div className="flex items-center justify-between text-sm">
                        <span className="capitalize text-slate-700">{block.type.replaceAll("_", " ")}</span>
                        <span className="font-semibold text-slate-900">{tok(block.tokens)} tok</span>
                      </div>
                      <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-teal-400"
                          style={{ width: dynamicTotal > 0 ? `${(block.tokens / dynamicTotal) * 100}%` : "0%" }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {contextReport.optimized_prompt_package.notes && (
                <p className="mt-4 rounded border border-slate-200 bg-slate-50 px-2 py-1.5 text-xs text-slate-600">
                  {contextReport.optimized_prompt_package.notes}
                </p>
              )}
            </section>
          </div>
        </>
      ) : (
        <section className="rounded-lg border border-line bg-white p-6">
          <h2 className="font-semibold">No context report available yet</h2>
          <p className="mt-2 max-w-xl text-sm text-muted">
            Open any run, scroll to the Optimizer section, and run the context optimizer. The result will appear here as the featured run for deep inspection.
          </p>
        </section>
      )}

      {/* Corpus table */}
      <section className="rounded-lg border border-line bg-white">
        <div className="border-b border-line px-5 py-4">
          <h2 className="font-semibold">All runs — repeated context %</h2>
          <p className="mt-1 text-sm text-muted">⚠ = repeated context above 55% threshold — highest optimization priority.</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-slate-50 text-xs font-semibold uppercase text-muted">
                <th className="px-4 py-3 text-left">Task Goal</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Repeated CTX%</th>
                <th className="px-4 py-3 text-left">Input Tokens</th>
                <th className="px-4 py-3 text-left">Retries</th>
                <th className="px-4 py-3 text-left">Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {tasks.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-sm text-muted">No runs traced yet. Import a trace or run the demo to see context data.</td>
                </tr>
              ) : (
                tasks.map((task) => {
                  const analysis = analyses.find((a) => a.task_id === task.task_id);
                  const ctxPct = analysis?.repeated_context_percent ?? 0;
                  const isHigh = ctxPct >= 55;
                  return (
                    <tr key={task.task_id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 font-medium">{task.goal}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${
                          task.status === "completed"
                            ? "border-teal-200 bg-teal-50 text-teal-700"
                            : task.status === "failed"
                              ? "border-red-200 bg-red-50 text-red-700"
                              : "border-amber-200 bg-amber-50 text-amber-700"
                        }`}>
                          {task.status === "completed" ? "Success" : task.status === "failed" ? "Failed" : task.status}
                        </span>
                      </td>
                      <td className={`px-4 py-3 font-semibold ${isHigh ? "text-red-600" : ctxPct > 30 ? "text-amber-700" : "text-teal-700"}`}>
                        {analysis ? `${ctxPct.toFixed(1)}%${isHigh ? " ⚠" : ""}` : "—"}
                      </td>
                      <td className="px-4 py-3 text-slate-600">{analysis ? tok(analysis.total_input_tokens) : "—"}</td>
                      <td className="px-4 py-3 text-slate-600">{analysis ? analysis.retry_count : "—"}</td>
                      <td className="px-4 py-3 text-slate-600">
                        {analysis ? usd(analysis.estimated_total_cost_dollars) : "—"}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
