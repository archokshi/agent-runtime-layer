import Link from "next/link";
import { Shell } from "@/components/Shell";
import { getAllAnalyses, getPhase1ExitPackages, getPlatformSummary, getTasks } from "@/lib/api";
import { ArrowLeft, ArrowRight } from "lucide-react";

function Badge({ q }: { q: string }) {
  const m: Record<string, string> = { verified: "bg-teal-50 text-teal-800 border-teal-200", estimated: "bg-amber-50 text-amber-800 border-amber-200", inferred: "bg-blue-50 text-blue-800 border-blue-200", nodata: "bg-slate-50 text-slate-500 border-slate-200" };
  const l: Record<string, string> = { verified: "✓ Verified", estimated: "~ Estimated", inferred: "≈ Inferred", nodata: "— No data" };
  return <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${m[q] ?? m.nodata}`}>{l[q] ?? q}</span>;
}

function usd(n: number | null | undefined) {
  if (n == null) return "—";
  if (n < 0.01 && n > 0) return `$${n.toFixed(5)}`;
  return `$${n.toFixed(4)}`;
}

export default async function CostPage() {
  const tasks = await getTasks().catch(() => []);
  const [analyses, platform, reports] = await Promise.all([
    getAllAnalyses(tasks),
    getPlatformSummary(),
    getPhase1ExitPackages(),
  ]);
  const latestReport = reports?.[0] ?? null;
  const n = analyses.length;

  const totalCost = analyses.reduce((s, a) => s + a.estimated_total_cost_dollars, 0);
  const avgCost = n > 0 ? totalCost / n : 0;

  const successAnalyses = analyses.filter((a) => tasks.find((t) => t.task_id === a.task_id)?.status === "completed");
  const failedAnalyses = analyses.filter((a) => tasks.find((t) => t.task_id === a.task_id)?.status === "failed");
  const avgSuccessCost = successAnalyses.length > 0 ? successAnalyses.reduce((s, a) => s + a.estimated_total_cost_dollars, 0) / successAnalyses.length : null;
  const avgFailedCost = failedAnalyses.length > 0 ? failedAnalyses.reduce((s, a) => s + a.estimated_total_cost_dollars, 0) / failedAnalyses.length : null;
  const failMultiplier = avgSuccessCost && avgFailedCost && avgSuccessCost > 0 ? avgFailedCost / avgSuccessCost : null;
  const totalRetries = analyses.reduce((s, a) => s + a.retry_count, 0);
  const avgRetries = n > 0 ? totalRetries / n : 0;
  const retryCostEstimate = avgCost > 0 && avgRetries > 0 ? avgCost * avgRetries * 0.08 : null;

  const contextProfile = latestReport?.workload_evaluation_package?.context_kv_reuse_profile as Record<string, unknown> | undefined;
  const repeatedCtxPct = typeof contextProfile?.avg_repeated_context_percent === "number"
    ? contextProfile.avg_repeated_context_percent as number
    : n > 0 ? analyses.reduce((s, a) => s + a.repeated_context_percent, 0) / n : 0;
  const repeatedCostPerRun = avgCost > 0 && repeatedCtxPct > 0 ? avgCost * (repeatedCtxPct / 100) : null;

  const measuredExp = platform?.measured_validation?.[0] ?? null;

  const scatterData = analyses
    .map((a) => ({ cost: a.estimated_total_cost_dollars, retries: a.retry_count, success: tasks.find((t) => t.task_id === a.task_id)?.status === "completed", goal: tasks.find((t) => t.task_id === a.task_id)?.goal ?? a.task_id, taskId: a.task_id }))
    .filter((d) => d.cost > 0)
    .sort((a, b) => b.cost - a.cost)
    .slice(0, 20);
  const maxCost = scatterData.length > 0 ? Math.max(...scatterData.map((d) => d.cost)) : 0;

  return (
    <Shell hasData>
      <div className="grid gap-5">
        <div>
          <Link href="/" className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-mint mb-2"><ArrowLeft size={12} /> Overview</Link>
          <h1 className="text-2xl font-bold text-ink">Cost Explorer</h1>
          <p className="mt-1 text-sm text-slate-500">Where money goes — and what would actually reduce it.</p>
        </div>

        {/* Top 4 cards */}
        <section className="grid gap-3 sm:grid-cols-4">
          {[
            { label: "Total cost", value: usd(totalCost), sub: `${n} runs · ${usd(avgCost)} avg`, q: n > 0 ? "estimated" : "nodata" },
            { label: "Cost / successful task", value: usd(avgSuccessCost), sub: `${successAnalyses.length} successful runs`, q: avgSuccessCost ? "estimated" : "nodata", teal: true },
            { label: "Cost / failed task", value: usd(avgFailedCost), sub: failMultiplier ? `${failMultiplier.toFixed(2)}× more than success` : `${failedAnalyses.length} failed runs`, q: avgFailedCost ? "estimated" : "nodata", red: true },
            { label: "Retry overhead / run", value: usd(retryCostEstimate), sub: `avg ${avgRetries.toFixed(1)} retries/run`, q: retryCostEstimate ? "estimated" : "nodata" },
          ].map(({ label, value, sub, q, teal, red }) => (
            <div key={label} className={`rounded-xl border p-4 shadow-sm ${teal ? "border-teal-200" : red ? "border-red-200" : "border-line"} bg-white`}>
              <p className={`text-xs font-semibold uppercase ${teal ? "text-teal-700" : red ? "text-red-600" : "text-slate-400"}`}>{label}</p>
              <p className={`mt-2 text-3xl font-bold ${teal ? "text-teal-700" : red ? "text-red-600" : "text-ink"}`}>{value}</p>
              <p className="mt-1 text-xs text-slate-400">{sub}</p>
              <div className="mt-2"><Badge q={q} /></div>
            </div>
          ))}
        </section>

        {/* Breakdown + Before/After */}
        <div className="grid gap-4 lg:grid-cols-2">
          <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold text-ink">Cost breakdown <span className="text-xs font-normal text-slate-400">per run average</span></h2>
              <Badge q={n > 0 ? "estimated" : "nodata"} />
            </div>
            {n === 0 ? <p className="text-sm text-slate-400">No cost data yet.</p> : (
              <div className="space-y-4">
                <div>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className={`font-medium ${repeatedCtxPct >= 30 ? "text-red-600" : "text-slate-600"}`}>Repeated input tokens {repeatedCtxPct >= 30 ? "⚠" : ""}</span>
                    <span className={`font-semibold ${repeatedCtxPct >= 30 ? "text-red-600" : "text-ink"}`}>{repeatedCtxPct.toFixed(0)}% · {usd(repeatedCostPerRun)}</span>
                  </div>
                  <div className="h-4 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-red-300" style={{ width: `${repeatedCtxPct}%` }} /></div>
                  {repeatedCtxPct >= 30 && <p className="mt-1 text-xs text-red-600">⚠ Recoverable with prefix caching <Link href="/context" className="font-semibold hover:underline">— Inspect →</Link></p>}
                </div>
                <div>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="font-medium text-slate-600">Unique input tokens</span>
                    <span className="font-semibold text-ink">{(100 - repeatedCtxPct).toFixed(0)}%</span>
                  </div>
                  <div className="h-4 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-mint" style={{ width: `${100 - repeatedCtxPct}%` }} /></div>
                </div>
                <div>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="font-medium text-slate-600">Output tokens</span>
                    <span className="font-semibold text-slate-500">~9% of input cost</span>
                  </div>
                  <div className="h-4 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-teal-300" style={{ width: "9%" }} /></div>
                </div>
              </div>
            )}
          </section>

          <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold text-ink">Before / after comparison</h2>
              <Badge q={measuredExp ? "verified" : "nodata"} />
            </div>
            {measuredExp ? (
              <>
                <div className="space-y-3 mb-4">
                  <div>
                    <div className="mb-1 flex justify-between text-sm"><span className="text-slate-500">Baseline</span><span className="text-ink font-medium">before optimization</span></div>
                    <div className="h-6 rounded-full bg-slate-300 flex items-center justify-end pr-2"><span className="text-xs text-white font-medium">baseline</span></div>
                  </div>
                  <div>
                    <div className="mb-1 flex justify-between text-sm">
                      <span className="text-teal-700 font-medium">Optimized</span>
                      <span className="text-teal-700 font-semibold">
                        {measuredExp.measured_input_token_reduction_percent ? `−${measuredExp.measured_input_token_reduction_percent.toFixed(1)}% tokens` : `−${(measuredExp.measured_duration_reduction_percent ?? 0).toFixed(1)}% duration`}
                      </span>
                    </div>
                    <div className="h-6 overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full bg-mint rounded-full flex items-center justify-end pr-2" style={{ width: `${100 - (measuredExp.measured_input_token_reduction_percent ?? measuredExp.measured_duration_reduction_percent ?? 0)}%` }}>
                        <span className="text-xs text-white font-medium">optimized</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {measuredExp.measured_cost_reduction_percent != null && <span className="rounded-lg border border-teal-200 bg-teal-50 px-3 py-1.5 text-sm font-semibold text-teal-700">−{measuredExp.measured_cost_reduction_percent.toFixed(1)}% cost</span>}
                  {measuredExp.measured_input_token_reduction_percent != null && <span className="rounded-lg border border-teal-200 bg-teal-50 px-3 py-1.5 text-sm font-semibold text-teal-700">−{measuredExp.measured_input_token_reduction_percent.toFixed(1)}% tokens</span>}
                  {measuredExp.success_preserved != null && <span className="rounded-lg border border-teal-200 bg-teal-50 px-3 py-1.5 text-sm font-semibold text-teal-700">Success preserved: {measuredExp.success_preserved ? "yes ✓" : "no"}</span>}
                </div>
              </>
            ) : (
              <div className="rounded-lg border border-line bg-panel p-4">
                <p className="font-medium text-ink">No measured comparison yet</p>
                <p className="mt-2 text-sm text-slate-500">Run the context optimizer on a task, then re-run the same task. The before/after pair will appear here.</p>
                <Link href="/runs" className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-mint hover:underline">Go to runs <ArrowRight size={12} /></Link>
              </div>
            )}
          </section>
        </div>

        {/* Scatter — horizontal bars */}
        {scatterData.length > 0 && (
          <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-ink">Cost per run</h2>
                <p className="mt-0.5 text-xs text-slate-400">Failed runs and high-retry runs cluster at the top</p>
              </div>
              <Badge q="estimated" />
            </div>
            <div className="space-y-2">
              {scatterData.map((d) => (
                <div key={d.taskId} className="flex items-center gap-3">
                  <span className={`h-2.5 w-2.5 flex-shrink-0 rounded-full ${d.success ? "bg-mint" : "bg-red-400"}`} />
                  <Link href={`/runs/${d.taskId}`} className="w-44 truncate text-xs text-slate-600 hover:text-mint transition-colors">{d.goal}</Link>
                  <div className="flex-1">
                    <div className="h-3 overflow-hidden rounded-full bg-slate-100">
                      <div className={`h-full rounded-full ${d.success ? "bg-mint" : "bg-red-400"}`} style={{ width: maxCost > 0 ? `${(d.cost / maxCost) * 100}%` : "0%" }} />
                    </div>
                  </div>
                  <span className={`w-24 text-right text-xs font-semibold ${d.success ? "text-slate-700" : "text-red-600"}`}>
                    {usd(d.cost)}{d.retries > 0 ? ` · ${d.retries}r` : ""}
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-4 flex items-center gap-4 text-xs text-slate-400">
              <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-mint inline-block" /> Success</span>
              <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-red-400 inline-block" /> Failed · r = retries</span>
            </div>
          </section>
        )}

        <div className="flex flex-wrap gap-3">
          <Link href="/bottlenecks" className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:border-mint hover:text-mint transition-colors">← Bottlenecks</Link>
          <Link href="/context" className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:border-mint hover:text-mint transition-colors">Inspect context <ArrowRight size={14} /></Link>
          <Link href="/recommendations" className="inline-flex items-center gap-2 rounded-lg border border-mint bg-teal-50 px-4 py-2 text-sm font-semibold text-mint hover:bg-teal-100 transition-colors">Get recommendations <ArrowRight size={14} /></Link>
        </div>
      </div>
    </Shell>
  );
}
