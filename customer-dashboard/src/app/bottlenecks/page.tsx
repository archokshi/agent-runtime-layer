import Link from "next/link";
import { Shell } from "@/components/Shell";
import { getAllAnalyses, getPhase1ExitPackages, getTasks } from "@/lib/api";
import { ArrowLeft, ArrowRight } from "lucide-react";

function Badge({ q }: { q: string }) {
  const m: Record<string, string> = {
    verified: "bg-teal-50 text-teal-800 border-teal-200",
    estimated: "bg-amber-50 text-amber-800 border-amber-200",
    inferred: "bg-blue-50 text-blue-800 border-blue-200",
    nodata: "bg-slate-50 text-slate-500 border-slate-200",
  };
  const l: Record<string, string> = { verified: "✓ Verified", estimated: "~ Estimated", inferred: "≈ Inferred", nodata: "— No data" };
  return <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${m[q] ?? m.nodata}`}>{l[q] ?? q}</span>;
}

function Bar({ label, pct, avg, color, warn }: { label: string; pct: number; avg: string; color: string; warn?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <div className={`w-32 text-right text-sm font-medium ${warn ? "text-amber-700" : "text-slate-600"}`}>{label}{warn ? " ⚠" : ""}</div>
      <div className="flex-1">
        <div className="h-4 overflow-hidden rounded-full bg-slate-100">
          <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
        </div>
      </div>
      <div className={`w-32 text-sm font-semibold ${warn ? "text-amber-700" : "text-ink"}`}>{pct.toFixed(0)}% · {avg}</div>
    </div>
  );
}

type PatternCardProps = { title: string; count: number; total: number; desc: string; quality: string; upgrade?: string; priority: "high" | "med" | "low" };

function PatternCard({ title, count, total, desc, quality, upgrade, priority }: PatternCardProps) {
  const border = priority === "high" ? "border-red-200" : priority === "med" ? "border-amber-200" : "border-line";
  const bg = priority === "high" ? "bg-red-50" : priority === "med" ? "bg-amber-50" : "bg-white";
  const titleColor = priority === "high" ? "text-red-900" : priority === "med" ? "text-amber-900" : "text-ink";
  const descColor = priority === "high" ? "text-red-700" : priority === "med" ? "text-amber-700" : "text-slate-600";
  return (
    <div className={`rounded-xl border ${border} ${bg} p-5 shadow-sm`}>
      <div className="flex flex-wrap items-start justify-between gap-2 mb-2">
        <p className={`font-semibold ${titleColor}`}>{title}</p>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-slate-500">{count} / {total} runs</span>
          <Badge q={quality} />
        </div>
      </div>
      <p className={`text-sm ${descColor}`}>{desc}</p>
      {upgrade && (
        <p className="mt-3 inline-block rounded border border-blue-100 bg-blue-50 px-2 py-1 text-xs text-blue-700">
          Improve accuracy: {upgrade}
        </p>
      )}
    </div>
  );
}

export default async function BottlenecksPage() {
  const tasks = await getTasks().catch(() => []);
  const [analyses, reports] = await Promise.all([
    getAllAnalyses(tasks),
    getPhase1ExitPackages(),
  ]);
  const latestReport = reports?.[0] ?? null;
  const n = analyses.length;

  const totalModelMs = analyses.reduce((s, a) => s + a.model_time_ms, 0);
  const totalToolMs = analyses.reduce((s, a) => s + a.tool_time_ms, 0);
  const totalIdleMs = analyses.reduce((s, a) => s + a.orchestration_idle_ms, 0);
  const totalMs = totalModelMs + totalToolMs + totalIdleMs;
  const modelPct = totalMs > 0 ? (totalModelMs / totalMs) * 100 : 0;
  const toolPct = totalMs > 0 ? (totalToolMs / totalMs) * 100 : 0;
  const idlePct = totalMs > 0 ? (totalIdleMs / totalMs) * 100 : 0;
  const avgModelSec = n > 0 ? (totalModelMs / n / 1000).toFixed(1) + "s avg" : "—";
  const avgToolSec = n > 0 ? (totalToolMs / n / 1000).toFixed(1) + "s avg" : "—";
  const avgIdleSec = n > 0 ? (totalIdleMs / n / 1000).toFixed(1) + "s avg" : "—";

  const contextProfile = latestReport?.workload_evaluation_package?.context_kv_reuse_profile as Record<string, unknown> | undefined;
  const repeatedCtxPct = typeof contextProfile?.avg_repeated_context_percent === "number"
    ? contextProfile.avg_repeated_context_percent as number
    : n > 0 ? analyses.reduce((s, a) => s + a.repeated_context_percent, 0) / n : 0;

  const totalInputTokens = analyses.reduce((s, a) => s + a.total_input_tokens, 0);
  const totalOutputTokens = analyses.reduce((s, a) => s + a.total_output_tokens, 0);
  const inputOutputRatio = totalOutputTokens > 0 ? totalInputTokens / totalOutputTokens : 0;
  const totalRetries = analyses.reduce((s, a) => s + a.retry_count, 0);
  const avgRetries = n > 0 ? totalRetries / n : 0;

  const h1Count = analyses.filter((a) => a.total_task_duration_ms > 0 && a.tool_time_ms / a.total_task_duration_ms >= 0.25).length;
  const h2Count = analyses.filter((a) => a.repeated_context_percent >= 15).length;
  const h4Count = analyses.filter((a) => a.total_task_duration_ms > 0 && a.orchestration_idle_ms / a.total_task_duration_ms >= 0.20).length;
  const h5Count = analyses.filter((a) => a.total_output_tokens > 0 && a.total_input_tokens / a.total_output_tokens > 10).length;
  const h6Count = analyses.filter((a) => a.retry_count > 0).length;

  return (
    <Shell hasData>
      <div className="grid gap-5">

        {/* Header */}
        <div>
          <Link href="/" className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-mint mb-2">
            <ArrowLeft size={12} /> Overview
          </Link>
          <h1 className="text-2xl font-bold text-ink">Bottlenecks</h1>
          <p className="mt-1 text-sm text-slate-500">Where your agent loses time and money — across all {tasks.length} traced runs.</p>
        </div>

        {/* Time + Cost split */}
        <div className="grid gap-4 lg:grid-cols-2">
          <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold text-ink">Where does time go?</h2>
              <Badge q={n > 0 ? "estimated" : "nodata"} />
            </div>
            {n === 0 ? <p className="text-sm text-slate-400">No analysis data yet.</p> : (
              <div className="space-y-4">
                <Bar label="Model inference" pct={modelPct} avg={avgModelSec} color="bg-mint" />
                <Bar label="Tool wait" pct={toolPct} avg={avgToolSec} color="bg-amber-400" warn={toolPct >= 40} />
                <Bar label="CPU / idle" pct={idlePct} avg={avgIdleSec} color="bg-slate-300" />
                {toolPct >= 40 && (
                  <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                    ⚠ Tool wait dominates {toolPct.toFixed(0)}% of elapsed time. GPU likely idle during this window.
                  </p>
                )}
              </div>
            )}
          </section>

          <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold text-ink">Where does cost go?</h2>
              <Badge q={n > 0 ? "estimated" : "nodata"} />
            </div>
            {n === 0 ? <p className="text-sm text-slate-400">No token data yet.</p> : (
              <div className="space-y-4">
                <Bar label="Repeated input ⚠" pct={repeatedCtxPct} avg={`${repeatedCtxPct.toFixed(0)}% of input`} color="bg-red-300" warn={repeatedCtxPct >= 30} />
                <Bar label="Unique input" pct={Math.max(0, 100 - repeatedCtxPct)} avg="necessary" color="bg-mint" />
                <Bar label="Output tokens" pct={totalInputTokens > 0 ? Math.min((totalOutputTokens / totalInputTokens) * 100, 20) : 0} avg="~9% of input cost" color="bg-teal-300" />
                <Bar label="Retry overhead" pct={Math.min(avgRetries * 10, 40)} avg={`${avgRetries.toFixed(1)} retr/run avg`} color="bg-red-200" warn={avgRetries > 3} />
                {repeatedCtxPct >= 30 && (
                  <div className="flex items-center justify-between rounded-lg border border-red-200 bg-red-50 px-3 py-2">
                    <p className="text-sm text-red-800">⚠ {repeatedCtxPct.toFixed(0)}% of input is repeated context — recoverable with caching</p>
                    <Link href="/context" className="text-xs font-semibold text-red-700 hover:underline flex items-center gap-1">Inspect <ArrowRight size={12} /></Link>
                  </div>
                )}
              </div>
            )}
          </section>
        </div>

        {/* Patterns */}
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold text-ink">Detected patterns</h2>
            <span className="text-xs text-slate-400">across {n} analyzed runs</span>
          </div>
          <div className="grid gap-3">
            <PatternCard
              title="Repeated tokens detected"
              count={h2Count} total={n}
              desc={`${repeatedCtxPct.toFixed(1)}% of input tokens are repeated stable context — system prompt, tool definitions, repo summary. Re-sent identically on every model call.`}
              quality="estimated"
              upgrade="add backend cache hit/miss telemetry"
              priority={h2Count > n / 2 ? "high" : "med"}
            />
            <PatternCard
              title="Tool wait blocking progress"
              count={h1Count} total={n}
              desc={`Tool windows avg ${(totalToolMs / Math.max(n, 1) / 1000).toFixed(1)}s. GPU is likely idle during tool execution — this is the primary driver of wall-clock latency.`}
              quality="estimated"
              upgrade="import GPU utilization telemetry from your backend"
              priority={h1Count > n / 2 ? "high" : "med"}
            />
            <PatternCard
              title="Input-heavy model calls"
              count={h5Count} total={n}
              desc={`Input/output ratio avg ${inputOutputRatio > 0 ? inputOutputRatio.toFixed(0) : "—"}:1. Heavily prefill-bound workload. TTFT impact unknown without backend timing data.`}
              quality={h5Count > 0 ? "verified" : "nodata"}
              upgrade="add TTFT / ITL timing from your inference backend"
              priority={inputOutputRatio > 30 ? "med" : "low"}
            />
            <PatternCard
              title="Idle time detected"
              count={h4Count} total={n}
              desc={`Unexplained idle gaps avg ${(totalIdleMs / Math.max(n, 1) / 1000).toFixed(1)}s — ${idlePct.toFixed(0)}% of elapsed time. May reflect orchestration delays or missing spans.`}
              quality="inferred"
              priority="low"
            />
            <PatternCard
              title="Retry overhead detected"
              count={h6Count} total={n}
              desc={`${h6Count} runs have retries. Avg ${avgRetries.toFixed(1)} retries/run. Each retry re-sends full context — compounding token cost with no checkpointing.`}
              quality={h6Count > 0 ? "verified" : "nodata"}
              priority={avgRetries > 3 ? "high" : h6Count > 0 ? "med" : "low"}
            />
          </div>
        </section>

        {/* Cross-links */}
        <div className="flex flex-wrap gap-3">
          <Link href="/context" className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:border-mint hover:text-mint transition-colors">
            Inspect repeated context <ArrowRight size={14} />
          </Link>
          <Link href="/cost" className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:border-mint hover:text-mint transition-colors">
            Explore cost breakdown <ArrowRight size={14} />
          </Link>
          <Link href="/recommendations" className="inline-flex items-center gap-2 rounded-lg border border-mint bg-teal-50 px-4 py-2 text-sm font-semibold text-mint hover:bg-teal-100 transition-colors">
            Get ranked recommendations <ArrowRight size={14} />
          </Link>
        </div>

      </div>
    </Shell>
  );
}
