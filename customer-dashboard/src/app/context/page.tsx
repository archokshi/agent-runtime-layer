import Link from "next/link";
import { Shell } from "@/components/Shell";
import { getAllAnalyses, getOptimizedContext, getPhase1ExitPackages, getTasks } from "@/lib/api";
import { ArrowLeft, ArrowRight } from "lucide-react";

function Badge({ q }: { q: string }) {
  const m: Record<string, string> = { verified: "bg-teal-50 text-teal-800 border-teal-200", estimated: "bg-amber-50 text-amber-800 border-amber-200", inferred: "bg-blue-50 text-blue-800 border-blue-200", nodata: "bg-slate-50 text-slate-500 border-slate-200" };
  const l: Record<string, string> = { verified: "✓ Verified", estimated: "~ Estimated", inferred: "≈ Inferred", nodata: "— No data" };
  return <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${m[q] ?? m.nodata}`}>{l[q] ?? q}</span>;
}

export default async function ContextPage() {
  const tasks = await getTasks().catch(() => []);
  const [analyses, reports] = await Promise.all([getAllAnalyses(tasks), getPhase1ExitPackages()]);
  const latestReport = reports?.[0] ?? null;

  const sorted = [...analyses].sort((a, b) => b.repeated_context_percent - a.repeated_context_percent);
  const featuredTaskId = sorted[0]?.task_id ?? null;
  const contextReport = featuredTaskId ? await getOptimizedContext(featuredTaskId) : null;
  const featuredTask = featuredTaskId ? tasks.find((t) => t.task_id === featuredTaskId) : null;

  const n = analyses.length;
  const avgCtxPct = n > 0 ? analyses.reduce((s, a) => s + a.repeated_context_percent, 0) / n : 0;
  const highWasteRuns = analyses.filter((a) => a.repeated_context_percent >= 55).length;
  const stableBlocks = contextReport?.stable_context_blocks ?? [];
  const dynamicBlocks = contextReport?.dynamic_context_blocks ?? [];
  const stableTotal = stableBlocks.reduce((s, b) => s + b.tokens, 0);
  const dynamicTotal = dynamicBlocks.reduce((s, b) => s + b.tokens, 0);
  const savings = contextReport?.savings;
  const baseline = contextReport?.baseline;
  const repeatedTokens = baseline ? Math.round(baseline.input_tokens * baseline.repeated_context_percent / 100) : stableTotal;
  const recoverableCost = baseline && savings ? baseline.estimated_cost * savings.estimated_cost_reduction_percent / 100 : null;

  return (
    <Shell hasData>
      <div className="grid gap-5">

        <div>
          <Link href="/" className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-mint mb-2"><ArrowLeft size={12} /> Overview</Link>
          <h1 className="text-2xl font-bold text-ink">Context Inspector</h1>
          <p className="mt-1 text-sm text-slate-500">The only view that shows which tokens you re-send on every model call. Stable context is the primary optimization target.</p>
        </div>

        {/* Summary cards */}
        <section className="grid gap-3 sm:grid-cols-4">
          {[
            { label: "Avg repeated tokens", value: `${avgCtxPct.toFixed(1)}%`, sub: `across ${tasks.length} runs`, q: n > 0 ? "estimated" : "nodata", warn: avgCtxPct >= 30 },
            { label: "Runs above 55%", value: String(highWasteRuns), sub: "highest priority", q: "verified", warn: highWasteRuns > 0 },
            { label: "Stable block size", value: stableTotal > 0 ? `${(stableTotal / 1000).toFixed(0)}k tok` : "—", sub: "cacheable per call", q: stableTotal > 0 ? "estimated" : "nodata", warn: false },
            { label: "Recoverable cost", value: recoverableCost !== null ? `$${recoverableCost.toFixed(5)}` : "—", sub: "per featured run", q: recoverableCost !== null ? "estimated" : "nodata", warn: false },
          ].map(({ label, value, sub, q, warn }) => (
            <div key={label} className={`rounded-xl border p-4 shadow-sm ${warn ? "border-amber-200 bg-amber-50" : "border-line bg-white"}`}>
              <p className="text-xs font-semibold uppercase text-slate-400">{label}</p>
              <p className={`mt-2 text-2xl font-bold ${warn ? "text-amber-700" : "text-ink"}`}>{value}</p>
              <p className="mt-1 text-xs text-slate-400">{sub}</p>
              <div className="mt-2"><Badge q={q} /></div>
            </div>
          ))}
        </section>

        {contextReport ? (
          <>
            {/* Featured run */}
            <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
              <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="font-semibold text-ink">Context breakdown — {featuredTask?.goal ?? featuredTaskId}</h2>
                  <p className="mt-0.5 text-xs text-slate-400">Run with highest repeated context selected automatically.</p>
                </div>
                <Badge q="estimated" />
              </div>
              <div className="grid gap-3 md:grid-cols-3">
                <div className="rounded-lg border border-line bg-panel p-4 text-center">
                  <p className="text-xs font-semibold uppercase text-slate-400">Total input tokens</p>
                  <p className="mt-2 text-2xl font-bold text-ink">{baseline ? `${(baseline.input_tokens / 1000).toFixed(0)}k` : "—"}</p>
                  <p className="text-xs text-slate-400 mt-1">all model calls combined</p>
                </div>
                <div className="rounded-lg border border-teal-200 bg-teal-50 p-4 text-center">
                  <p className="text-xs font-semibold uppercase text-teal-700">Unique content</p>
                  <p className="mt-2 text-2xl font-bold text-teal-700">{baseline ? `${((baseline.input_tokens - repeatedTokens) / 1000).toFixed(0)}k` : "—"}</p>
                  <p className="text-xs text-teal-600 mt-1">necessary — cannot cache</p>
                </div>
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-center">
                  <p className="text-xs font-semibold uppercase text-red-700">Repeated / cacheable</p>
                  <p className="mt-2 text-2xl font-bold text-red-600">{baseline ? `${(repeatedTokens / 1000).toFixed(0)}k` : "—"}</p>
                  <p className="text-xs font-semibold text-red-600 mt-1">{baseline?.repeated_context_percent.toFixed(1)}% of total</p>
                </div>
              </div>
              {savings && (
                <div className="mt-3 flex items-center justify-between rounded-lg border border-amber-200 bg-amber-50 px-4 py-2">
                  <p className="text-sm text-amber-800">
                    If cached: −{savings.input_token_reduction_percent.toFixed(0)}% input tokens · ~{savings.estimated_cost_reduction_percent.toFixed(0)}% cost saving per run
                  </p>
                  <Badge q="estimated" />
                </div>
              )}
            </section>

            {/* Stable + Dynamic blocks */}
            <div className="grid gap-4 lg:grid-cols-2">
              <section className="rounded-xl border-2 border-teal-300 bg-white p-5 shadow-sm">
                <div className="mb-3 flex items-center gap-2">
                  <span className="h-3 w-3 rounded-sm bg-mint" />
                  <h2 className="font-semibold text-ink">Stable — {(stableTotal / 1000).toFixed(0)}k tokens</h2>
                </div>
                <p className="mb-4 rounded border border-teal-200 bg-teal-50 px-2 py-1 text-xs text-teal-700">Same on every call → primary caching target</p>
                {stableBlocks.length === 0 ? (
                  <p className="text-sm text-slate-400">No stable blocks detected. Run the optimizer from a task detail page.</p>
                ) : (
                  <div className="space-y-3">
                    {stableBlocks.map((b) => (
                      <div key={b.block_id}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="capitalize text-slate-600">{b.type.replaceAll("_", " ")}</span>
                          <span className="font-semibold text-ink">{(b.tokens / 1000).toFixed(1)}k · {b.occurrences}× seen</span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                          <div className="h-full rounded-full bg-mint" style={{ width: stableTotal > 0 ? `${(b.tokens / stableTotal) * 100}%` : "0%" }} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
                <div className="mb-3 flex items-center gap-2">
                  <span className="h-3 w-3 rounded-sm bg-teal-400" />
                  <h2 className="font-semibold text-ink">Dynamic — {(dynamicTotal / 1000).toFixed(0)}k tokens</h2>
                </div>
                <p className="mb-4 rounded border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-600">Changes each call → necessary, cannot be cached</p>
                {dynamicBlocks.length === 0 ? (
                  <p className="text-sm text-slate-400">No dynamic blocks detected. Run the optimizer to classify payload.</p>
                ) : (
                  <div className="space-y-3">
                    {dynamicBlocks.map((b) => (
                      <div key={b.block_id}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="capitalize text-slate-600">{b.type.replaceAll("_", " ")}</span>
                          <span className="font-semibold text-ink">{(b.tokens / 1000).toFixed(1)}k</span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                          <div className="h-full rounded-full bg-teal-400" style={{ width: dynamicTotal > 0 ? `${(b.tokens / dynamicTotal) * 100}%` : "0%" }} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>
          </>
        ) : (
          <section className="rounded-xl border border-line bg-white p-6 shadow-sm">
            <h2 className="font-semibold text-ink">No context breakdown available yet</h2>
            <p className="mt-2 max-w-xl text-sm text-slate-500">
              Open any run, scroll to the Optimizer section, and run the context optimizer. The result will appear here as the featured run.
            </p>
            <Link href="/runs" className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-mint hover:underline">
              Go to Runs <ArrowRight size={14} />
            </Link>
          </section>
        )}

        {/* Corpus table */}
        <section className="rounded-xl border border-line bg-white shadow-sm overflow-hidden">
          <div className="border-b border-line px-5 py-4">
            <h2 className="font-semibold text-ink">All runs — repeated token %</h2>
            <p className="mt-0.5 text-xs text-slate-400">⚠ = above 55% — highest caching opportunity</p>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-slate-50 text-xs font-semibold uppercase text-slate-400">
                <th className="px-5 py-3 text-left">Task goal</th>
                <th className="px-5 py-3 text-left">Status</th>
                <th className="px-5 py-3 text-left">Repeated %</th>
                <th className="px-5 py-3 text-left">Input tokens</th>
                <th className="px-5 py-3 text-left">Retries</th>
                <th className="px-5 py-3 text-left">Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {tasks.length === 0 ? (
                <tr><td colSpan={6} className="px-5 py-6 text-center text-sm text-slate-400">No runs yet.</td></tr>
              ) : (
                tasks.map((task) => {
                  const a = analyses.find((x) => x.task_id === task.task_id);
                  const p = a?.repeated_context_percent ?? 0;
                  const high = p >= 55;
                  return (
                    <tr key={task.task_id} className="hover:bg-teal-50 transition-colors">
                      <td className="px-5 py-3">
                        <Link href={`/runs/${task.task_id}`} className="font-medium text-ink hover:text-mint transition-colors">{task.goal}</Link>
                      </td>
                      <td className="px-5 py-3">
                        <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${task.status === "completed" ? "border-teal-200 bg-teal-50 text-teal-700" : task.status === "failed" ? "border-red-200 bg-red-50 text-red-700" : "border-amber-200 bg-amber-50 text-amber-700"}`}>
                          {task.status === "completed" ? "Success" : task.status === "failed" ? "Failed" : task.status}
                        </span>
                      </td>
                      <td className={`px-5 py-3 font-semibold ${high ? "text-red-600" : p > 30 ? "text-amber-700" : "text-teal-700"}`}>
                        {a ? `${p.toFixed(1)}%${high ? " ⚠" : ""}` : "—"}
                      </td>
                      <td className="px-5 py-3 text-slate-600">{a ? `${(a.total_input_tokens / 1000).toFixed(0)}k` : "—"}</td>
                      <td className="px-5 py-3 text-slate-600">{a ? a.retry_count : "—"}</td>
                      <td className="px-5 py-3 text-slate-600">{a ? `$${a.estimated_total_cost_dollars.toFixed(4)}` : "—"}</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </section>

        <div className="flex flex-wrap gap-3">
          <Link href="/bottlenecks" className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:border-mint hover:text-mint transition-colors">← Bottlenecks</Link>
          <Link href="/recommendations" className="inline-flex items-center gap-2 rounded-lg border border-mint bg-teal-50 px-4 py-2 text-sm font-semibold text-mint hover:bg-teal-100 transition-colors">Get recommendations <ArrowRight size={14} /></Link>
        </div>

      </div>
    </Shell>
  );
}
