import Link from "next/link";
import { Shell } from "@/components/Shell";
import { getAllAnalyses, getBudgetSummary, getContextMemorySummary, getPhase1ExitPackages, getPlatformSummary, getTasks } from "@/lib/api";
import { ArrowRight, Shield, Brain } from "lucide-react";

function Badge({ quality }: { quality: string }) {
  const map: Record<string, string> = {
    verified: "bg-teal-50 text-teal-800 border-teal-200",
    estimated: "bg-amber-50 text-amber-800 border-amber-200",
    inferred: "bg-blue-50 text-blue-800 border-blue-200",
    nodata: "bg-slate-50 text-slate-500 border-slate-200",
  };
  const labels: Record<string, string> = {
    verified: "✓ Verified", estimated: "~ Estimated", inferred: "≈ Inferred", nodata: "— No data"
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${map[quality] ?? map.nodata}`}>
      {labels[quality] ?? quality}
    </span>
  );
}

function SplitBar({ label, pct, avg, color, warn }: { label: string; pct: number; avg: string; color: string; warn?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <div className={`w-32 text-right text-sm font-medium ${warn ? "text-amber-700" : "text-slate-600"}`}>{label}</div>
      <div className="flex-1">
        <div className="h-4 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full" style={{ width: `${Math.max(pct, 0)}%`, backgroundColor: color }} />
        </div>
      </div>
      <div className={`w-28 text-sm font-semibold ${warn ? "text-amber-700" : "text-ink"}`}>
        {pct.toFixed(0)}%{warn ? " ⚠" : ""} · {avg}
      </div>
    </div>
  );
}

function MetricCard({ label, value, sub, quality }: { label: string; value: string; sub: string; quality: string }) {
  return (
    <div className="rounded-xl border border-line bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-3 text-4xl font-bold text-ink">{value}</p>
      <p className="mt-1 text-sm text-slate-500">{sub}</p>
      <div className="mt-3"><Badge quality={quality} /></div>
    </div>
  );
}

export default async function OverviewPage() {
  const tasks = await getTasks().catch(() => []);
  const [platform, reports, budgetSummary, memSummary] = await Promise.all([
    getPlatformSummary(),
    getPhase1ExitPackages(),
    getBudgetSummary(),
    getContextMemorySummary(),
  ]);
  const analyses = await getAllAnalyses(tasks);
  const latestReport = reports?.[0] ?? null;

  const n = analyses.length;
  const totalModelMs = analyses.reduce((s, a) => s + a.model_time_ms, 0);
  const totalToolMs = analyses.reduce((s, a) => s + a.tool_time_ms, 0);
  const totalIdleMs = analyses.reduce((s, a) => s + a.orchestration_idle_ms, 0);
  const totalMs = totalModelMs + totalToolMs + totalIdleMs;
  const modelPct = totalMs > 0 ? (totalModelMs / totalMs) * 100 : 0;
  const toolPct = totalMs > 0 ? (totalToolMs / totalMs) * 100 : 0;
  const idlePct = totalMs > 0 ? (totalIdleMs / totalMs) * 100 : 0;
  const avgModelSec = n > 0 ? (totalModelMs / n / 1000).toFixed(1) : "0";
  const avgToolSec = n > 0 ? (totalToolMs / n / 1000).toFixed(1) : "0";
  const avgIdleSec = n > 0 ? (totalIdleMs / n / 1000).toFixed(1) : "0";

  const contextProfile = latestReport?.workload_evaluation_package?.context_kv_reuse_profile as Record<string, unknown> | undefined;
  const repeatedCtxPct = typeof contextProfile?.avg_repeated_context_percent === "number"
    ? contextProfile.avg_repeated_context_percent as number
    : analyses.length > 0 ? analyses.reduce((s, a) => s + a.repeated_context_percent, 0) / analyses.length : 0;

  const successTasks = tasks.filter((t) => t.status === "completed");
  const failedTasks = tasks.filter((t) => t.status === "failed");
  const successRate = tasks.length > 0 ? (successTasks.length / tasks.length) * 100 : 0;
  const successAnalyses = analyses.filter((a) => tasks.find((t) => t.task_id === a.task_id)?.status === "completed");
  const avgSuccessCost = successAnalyses.length > 0
    ? successAnalyses.reduce((s, a) => s + a.estimated_total_cost_dollars, 0) / successAnalyses.length
    : null;

  const totalRetries = analyses.reduce((s, a) => s + a.retry_count, 0);
  // Phase 1.8: estimate waste from retries (retry cost ≈ retry_count / model_call_count × total_cost)
  const estimatedRetryWaste = analyses.reduce((s, a) => {
    const retryFraction = a.model_call_count > 0 ? a.retry_count / a.model_call_count : 0;
    return s + a.estimated_total_cost_dollars * retryFraction;
  }, 0);
  const highCostRun = analyses.length > 0 ? Math.max(...analyses.map((a) => a.estimated_total_cost_dollars)) : 0;

  // Phase 1.9: estimate cache savings (repeated tokens × Anthropic cache discount ≈ $2.70/MTok)
  const avgInputTokens = n > 0 ? analyses.reduce((s, a) => s + a.total_input_tokens, 0) / n : 0;
  const avgRepeatedTokens = avgInputTokens * (repeatedCtxPct / 100);
  const estimatedCacheSavingsPerRun = avgRepeatedTokens * (2.70 / 1_000_000);

  const h1Count = analyses.filter((a) => a.total_task_duration_ms > 0 && a.tool_time_ms / a.total_task_duration_ms >= 0.25).length;
  const h2Count = analyses.filter((a) => a.repeated_context_percent >= 15).length;
  const h6Count = analyses.filter((a) => a.retry_count > 0).length;

  if (tasks.length === 0) {
    return (
      <Shell hasData={false}>
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <h1 className="text-2xl font-bold text-ink">No traces yet</h1>
          <p className="mt-3 max-w-md text-slate-500">
            Import a trace or connect an integration to see your agent dashboard.
          </p>
          <div className="mt-6 flex gap-3">
            <Link href="/import" className="inline-flex h-10 items-center gap-2 rounded-lg bg-mint px-5 text-sm font-semibold text-white hover:opacity-90">
              Import a trace <ArrowRight size={14} />
            </Link>
            <Link href="/" className="inline-flex h-10 items-center gap-2 rounded-lg border border-line bg-white px-5 text-sm font-semibold text-ink hover:bg-panel">
              Back to home
            </Link>
          </div>
        </div>
      </Shell>
    );
  }

  return (
    <Shell hasData>
      <div className="grid gap-6">

        <div className="flex items-end justify-between">
          <div>
            <h1 className="text-2xl font-bold text-ink">Overview</h1>
            <p className="mt-1 text-sm text-slate-500">{tasks.length} agent runs traced · live data</p>
          </div>
        </div>

        {/* Hero 3 cards */}
        <section className="grid gap-4 md:grid-cols-3">
          <MetricCard label="Repeated tokens" value={`${repeatedCtxPct.toFixed(1)}%`} sub="of input tokens re-sent every call" quality={n > 0 ? "estimated" : "nodata"} />
          <MetricCard label="Cost per successful task" value={avgSuccessCost !== null ? `$${avgSuccessCost.toFixed(4)}` : "—"} sub={`${successTasks.length} successful · ${failedTasks.length} failed`} quality={avgSuccessCost !== null ? "estimated" : "nodata"} />
          <MetricCard label="Task success rate" value={tasks.length > 0 ? `${successRate.toFixed(0)}%` : "—"} sub={`${successTasks.length} of ${tasks.length} runs`} quality={tasks.length > 0 ? "verified" : "nodata"} />
        </section>

        {/* Time split */}
        {n > 0 && (
          <section className="rounded-xl border border-line bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-ink">Where does your agent&apos;s time go?</h2>
                <p className="mt-0.5 text-xs text-slate-400">Average across {n} traced runs</p>
              </div>
              <Badge quality="estimated" />
            </div>
            <div className="space-y-3">
              <SplitBar label="Model inference" pct={modelPct} avg={`${avgModelSec}s avg`} color="#1d7f70" />
              <SplitBar label="Tool wait" pct={toolPct} avg={`${avgToolSec}s avg`} color="#f59e0b" warn={toolPct >= 40} />
              <SplitBar label="CPU / idle" pct={idlePct} avg={`${avgIdleSec}s avg`} color="#94a3b8" />
            </div>
            {toolPct >= 40 && (
              <div className="mt-4 flex items-center justify-between rounded-lg border border-amber-200 bg-amber-50 px-4 py-2">
                <p className="text-sm text-amber-800">⚠ Tool wait is using {toolPct.toFixed(0)}% of elapsed time</p>
                <Link href="/bottlenecks" className="text-xs font-semibold text-amber-700 hover:underline">See Bottlenecks →</Link>
              </div>
            )}
          </section>
        )}

        {/* Patterns + Recent runs */}
        <div className="grid gap-4 lg:grid-cols-2">
          <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold text-ink">Detected patterns</h2>
              <Link href="/bottlenecks" className="text-xs font-semibold text-mint hover:underline">Full analysis →</Link>
            </div>
            <div className="space-y-3">
              {[
                { label: "Repeated tokens detected", count: h2Count, total: n, desc: `${repeatedCtxPct.toFixed(1)}% of input tokens re-sent on every call`, href: "/context", linkLabel: "Inspect context →", priority: h2Count > n / 2 ? "high" : "med" },
                { label: "Tool wait blocking progress", count: h1Count, total: n, desc: `Tool windows avg ${avgToolSec}s while model may be idle`, href: "/bottlenecks", linkLabel: "See bottlenecks →", priority: h1Count > n / 2 ? "high" : "med" },
                { label: "Retry overhead detected", count: h6Count, total: n, desc: `${(totalRetries / Math.max(n, 1)).toFixed(1)} retries per run avg`, href: "/cost", linkLabel: "See cost impact →", priority: h6Count > n / 3 ? "med" : "low" },
              ].map(({ label, count, total, desc, href, linkLabel, priority }) => (
                <div key={label} className={`rounded-lg border p-3 ${priority === "high" ? "border-red-200 bg-red-50" : priority === "med" ? "border-amber-200 bg-amber-50" : "border-line bg-panel"}`}>
                  <div className="flex items-center justify-between gap-2">
                    <p className={`font-medium text-sm ${priority === "high" ? "text-red-900" : priority === "med" ? "text-amber-900" : "text-ink"}`}>{label}</p>
                    <span className="text-xs text-slate-500 font-medium">{count}/{total} runs</span>
                  </div>
                  <p className={`text-xs mt-1 ${priority === "high" ? "text-red-700" : priority === "med" ? "text-amber-700" : "text-slate-500"}`}>{desc}</p>
                  <Link href={href} className="mt-2 inline-block text-xs font-semibold text-mint hover:underline">{linkLabel}</Link>
                </div>
              ))}
            </div>
            <Link href="/recommendations" className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg border border-mint bg-teal-50 py-2 text-sm font-semibold text-mint hover:bg-teal-100 transition-colors">
              See ranked recommendations <ArrowRight size={14} />
            </Link>
          </section>

          <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold text-ink">Recent runs</h2>
              <Link href="/runs" className="text-xs font-semibold text-mint hover:underline">View all {tasks.length} →</Link>
            </div>
            <div className="space-y-2">
              {tasks.slice(0, 6).map((task) => {
                const analysis = analyses.find((a) => a.task_id === task.task_id);
                return (
                  <Link key={task.task_id} href={`/runs/${task.task_id}`} className="flex items-center gap-3 rounded-lg border border-line p-3 hover:border-mint hover:bg-teal-50 transition-colors">
                    <span className={`h-2.5 w-2.5 flex-shrink-0 rounded-full ${task.status === "completed" ? "bg-mint" : task.status === "failed" ? "bg-red-400" : "bg-amber-400"}`} />
                    <div className="flex-1 min-w-0">
                      <p className="truncate text-sm font-medium text-ink">{task.goal}</p>
                      <p className="text-xs text-slate-400">
                        {analysis ? `${(analysis.total_task_duration_ms / 1000).toFixed(1)}s · $${analysis.estimated_total_cost_dollars.toFixed(4)} · ${analysis.retry_count} retr${analysis.retry_count === 1 ? "y" : "ies"}` : "—"}
                      </p>
                    </div>
                    <span className={`flex-shrink-0 rounded-full border px-2 py-0.5 text-xs font-semibold ${task.status === "completed" ? "border-teal-200 bg-teal-50 text-teal-700" : task.status === "failed" ? "border-red-200 bg-red-50 text-red-700" : "border-amber-200 bg-amber-50 text-amber-700"}`}>
                      {task.status === "completed" ? "Success" : task.status === "failed" ? "Failed" : task.status}
                    </span>
                  </Link>
                );
              })}
            </div>
          </section>
        </div>

        {/* Phase 1.8 — Budget Governor + Phase 1.9 — Context Memory */}
        <div className="grid gap-4 lg:grid-cols-2">

          {/* Budget Governor */}
          <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <Shield size={16} className="text-mint flex-shrink-0" />
              <h2 className="font-semibold text-ink">Budget Governor</h2>
              <span className="ml-auto text-xs font-semibold px-2 py-0.5 rounded-full border bg-slate-50 text-slate-500 border-slate-200">Phase 1.8</span>
            </div>
            {budgetSummary && budgetSummary.total_blocked_runs > 0 ? (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-lg bg-teal-50 border border-teal-200 p-3 text-center">
                    <p className="text-xs text-teal-700 font-medium">Runs stopped</p>
                    <p className="text-2xl font-bold text-teal-700 mt-1">{budgetSummary.total_blocked_runs}</p>
                  </div>
                  <div className="rounded-lg bg-teal-50 border border-teal-200 p-3 text-center">
                    <p className="text-xs text-teal-700 font-medium">Saved</p>
                    <p className="text-2xl font-bold text-teal-700 mt-1">${budgetSummary.total_saved_dollars.toFixed(4)}</p>
                  </div>
                </div>
                <div className="text-xs text-slate-500">
                  Budget: ${budgetSummary.config.max_cost_per_run}/run · Max retries: {budgetSummary.config.max_retries_per_task}
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {totalRetries > 0 || highCostRun > 0 ? (
                  <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
                    <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">Cost risk in your runs</p>
                    <div className="mt-2 grid grid-cols-2 gap-2">
                      {totalRetries > 0 && (
                        <div>
                          <p className="text-xl font-bold text-amber-700">{totalRetries} retries</p>
                          <p className="text-xs text-amber-600">~${estimatedRetryWaste.toFixed(4)} wasted</p>
                        </div>
                      )}
                      {highCostRun > 0 && (
                        <div>
                          <p className="text-xl font-bold text-amber-700">${highCostRun.toFixed(4)}</p>
                          <p className="text-xs text-amber-600">highest single run</p>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">No retry overhead detected yet.</p>
                )}
                <p className="text-xs text-slate-500">Budget Governor caps cost per run and stops retry spirals automatically.</p>
                <pre className="text-xs bg-ink text-teal-300 rounded-lg p-2 overflow-x-auto">{"agent-runtime budget-init --repo ."}</pre>
              </div>
            )}
          </section>

          {/* Context Memory */}
          <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <Brain size={16} className="text-mint flex-shrink-0" />
              <h2 className="font-semibold text-ink">Context Memory</h2>
              <span className="ml-auto text-xs font-semibold px-2 py-0.5 rounded-full border bg-slate-50 text-slate-500 border-slate-200">Phase 1.9</span>
            </div>
            {memSummary && memSummary.total_entries > 0 ? (
              <div className="space-y-3">
                <div className="grid grid-cols-3 gap-2">
                  <div className="rounded-lg bg-teal-50 border border-teal-200 p-2 text-center">
                    <p className="text-xs text-teal-700">Blocks</p>
                    <p className="text-xl font-bold text-teal-700">{memSummary.total_entries}</p>
                  </div>
                  <div className="rounded-lg bg-teal-50 border border-teal-200 p-2 text-center">
                    <p className="text-xs text-teal-700">Hits</p>
                    <p className="text-xl font-bold text-teal-700">{memSummary.total_hit_count}</p>
                  </div>
                  <div className="rounded-lg bg-teal-50 border border-teal-200 p-2 text-center">
                    <p className="text-xs text-teal-700">Saved</p>
                    <p className="text-xl font-bold text-teal-700">${memSummary.total_cache_savings_dollars.toFixed(3)}</p>
                  </div>
                </div>
                <p className="text-xs text-slate-500">{memSummary.message}</p>
              </div>
            ) : (
              <div className="space-y-3">
                {estimatedCacheSavingsPerRun > 0 ? (
                  <div className="rounded-lg border border-teal-200 bg-teal-50 p-3">
                    <p className="text-xs font-semibold uppercase tracking-wide text-teal-800">Caching opportunity detected</p>
                    <div className="mt-2 grid grid-cols-2 gap-2">
                      <div>
                        <p className="text-xl font-bold text-teal-700">~${estimatedCacheSavingsPerRun.toFixed(4)}</p>
                        <p className="text-xs text-teal-600">saved per run</p>
                      </div>
                      <div>
                        <p className="text-xl font-bold text-teal-700">{repeatedCtxPct.toFixed(0)}%</p>
                        <p className="text-xs text-teal-600">tokens re-sent every call</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">Run more traces to see your caching opportunity.</p>
                )}
                <p className="text-xs text-slate-500">Context Memory fingerprints your stable context and caches it at 10× cheaper Anthropic rates.</p>
                <pre className="text-xs bg-ink text-teal-300 rounded-lg p-2 overflow-x-auto">{"agent-runtime proxy --port 8100"}</pre>
                <p className="text-xs text-slate-400">Then: <code className="bg-slate-100 px-1 rounded">ANTHROPIC_BASE_URL=http://localhost:8100</code></p>
              </div>
            )}
          </section>
        </div>

        {/* Quick links */}
        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { href: "/bottlenecks", label: "Bottleneck analysis", sub: "Time + cost split across all runs" },
            { href: "/context", label: "Context inspector", sub: "Which tokens are you re-sending?" },
            { href: "/cost", label: "Cost explorer", sub: "Cost per task, failure, and retry" },
            { href: "/recommendations", label: "Recommendations", sub: "What to fix first — ranked" },
          ].map(({ href, label, sub }) => (
            <Link key={href} href={href} className="rounded-xl border border-line bg-white p-4 hover:border-mint hover:shadow-sm transition-all">
              <p className="font-semibold text-sm text-ink">{label}</p>
              <p className="mt-1 text-xs text-slate-500">{sub}</p>
              <span className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-mint">Open <ArrowRight size={12} /></span>
            </Link>
          ))}
        </section>

      </div>
    </Shell>
  );
}
