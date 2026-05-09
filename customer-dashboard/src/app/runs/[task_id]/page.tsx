import Link from "next/link";
import { Shell } from "@/components/Shell";
import { getAnalysis, getEvents, getOptimizedContext, getOptimizations, getTask } from "@/lib/api";
import { ArrowLeft, ArrowRight } from "lucide-react";
import type { TraceEvent } from "@/lib/types";

function badge(q: string) {
  const m: Record<string, string> = {
    verified: "bg-teal-50 text-teal-800 border-teal-200",
    estimated: "bg-amber-50 text-amber-800 border-amber-200",
    inferred: "bg-blue-50 text-blue-800 border-blue-200",
    nodata: "bg-slate-50 text-slate-500 border-slate-200",
  };
  const l: Record<string, string> = { verified: "✓ Verified", estimated: "~ Estimated", inferred: "≈ Inferred", nodata: "— No data" };
  return <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${m[q] ?? m.nodata}`}>{l[q] ?? q}</span>;
}

async function optional<T>(p: Promise<T>): Promise<T | null> {
  try { return await p; } catch { return null; }
}

function eventColor(type: string) {
  if (type.startsWith("model_call")) return { bar: "bg-mint", text: "text-mint" };
  if (type.startsWith("tool_call") || type === "terminal_event") return { bar: "bg-slate-300", text: "text-slate-500" };
  if (type === "error_event") return { bar: "bg-red-400", text: "text-red-600" };
  if (type === "file_event") return { bar: "bg-slate-200", text: "text-slate-400" };
  if (type === "task_start" || type === "task_end") return { bar: "bg-teal-700", text: "text-teal-700" };
  return { bar: "bg-slate-100", text: "text-slate-400" };
}

function buildWaterfall(events: TraceEvent[], totalMs: number) {
  if (events.length < 2 || totalMs <= 0) return [];
  const sorted = [...events].sort((a, b) => a.timestamp.localeCompare(b.timestamp));
  const startTime = new Date(sorted[0].timestamp).getTime();
  const endTime = startTime + totalMs;
  const spans: { name: string; type: string; startPct: number; widthPct: number; tokens?: number; deltaTokens?: number }[] = [];
  let lastModelTokens = 0;

  for (const ev of sorted) {
    const attrs = (ev.attributes ?? {}) as Record<string, unknown>;
    const evStart = new Date(ev.timestamp).getTime();
    const startPct = Math.max(0, ((evStart - startTime) / (endTime - startTime)) * 100);
    const durationMs = typeof attrs.latency_ms === "number" ? attrs.latency_ms as number :
      typeof attrs.duration_ms === "number" ? attrs.duration_ms as number : 1000;
    const widthPct = Math.max(0.5, (durationMs / totalMs) * 100);
    const tokens = typeof attrs.input_tokens === "number" ? attrs.input_tokens as number : undefined;
    const deltaTokens = tokens && lastModelTokens > 0 && tokens > lastModelTokens ? tokens - lastModelTokens : undefined;
    if (tokens) lastModelTokens = tokens;
    if (["model_call_start", "model_call_end", "tool_call_start", "tool_call_end", "terminal_event", "error_event", "file_event", "task_start", "task_end"].includes(ev.event_type)) {
      spans.push({ name: ev.name || ev.event_type, type: ev.event_type, startPct, widthPct: Math.min(widthPct, 100 - startPct), tokens, deltaTokens });
    }
  }
  return spans.slice(0, 12);
}

export default async function RunDetailPage({ params }: { params: Promise<{ task_id: string }> }) {
  const { task_id } = await params;
  const [task, events, analysis] = await Promise.all([
    getTask(task_id),
    getEvents(task_id),
    getAnalysis(task_id),
  ]);
  const [optimizations, contextReport] = await Promise.all([
    optional(getOptimizations(task_id)),
    getOptimizedContext(task_id),
  ]);

  const totalMs = analysis.total_task_duration_ms;
  const totalDuration = totalMs > 0 ? `${(totalMs / 1000).toFixed(1)}s` : "—";
  const modelPct = totalMs > 0 ? (analysis.model_time_ms / totalMs) * 100 : 0;
  const toolPct = totalMs > 0 ? (analysis.tool_time_ms / totalMs) * 100 : 0;
  const idlePct = totalMs > 0 ? (analysis.orchestration_idle_ms / totalMs) * 100 : 0;
  const inputOutputRatio = analysis.total_output_tokens > 0 ? (analysis.total_input_tokens / analysis.total_output_tokens).toFixed(0) : "—";
  const prefillHeavy = analysis.total_output_tokens > 0 && analysis.total_input_tokens / analysis.total_output_tokens > 20;

  const waterfall = buildWaterfall(events, totalMs);

  const modelEvents = events.filter((e) => e.event_type === "model_call_end").sort((a, b) => a.timestamp.localeCompare(b.timestamp));
  const contextGrowth = modelEvents.map((e, i) => {
    const attrs = (e.attributes ?? {}) as Record<string, unknown>;
    const tokens = typeof attrs.input_tokens === "number" ? attrs.input_tokens as number : 0;
    const prev = i > 0 ? (() => { const pa = (modelEvents[i - 1].attributes ?? {}) as Record<string, unknown>; return typeof pa.input_tokens === "number" ? pa.input_tokens as number : 0; })() : 0;
    return { call: i + 1, tokens, delta: i > 0 ? tokens - prev : 0 };
  });
  const maxTokens = contextGrowth.length > 0 ? Math.max(...contextGrowth.map((c) => c.tokens)) : 0;

  const recentEvents = events
    .sort((a, b) => a.timestamp.localeCompare(b.timestamp))
    .slice(0, 20);

  return (
    <Shell hasData>
      <div className="grid gap-5">

        {/* Breadcrumb */}
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
            <Link href="/" className="hover:text-mint">Overview</Link>
            <span>›</span>
            <Link href="/runs" className="hover:text-mint">Runs</Link>
            <span>›</span>
            <span className="text-ink font-medium truncate max-w-xs">{task.goal}</span>
          </div>
          <Link href="/runs" className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-mint">
            <ArrowLeft size={12} /> Back to runs
          </Link>
        </div>

        {/* Title + status */}
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-ink">{task.goal}</h1>
            <p className="mt-1 text-xs text-slate-400">{task.task_id}</p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`rounded-full border px-3 py-1 text-sm font-semibold ${
              task.status === "completed" ? "border-teal-200 bg-teal-50 text-teal-700" :
              task.status === "failed" ? "border-red-200 bg-red-50 text-red-700" :
              "border-amber-200 bg-amber-50 text-amber-700"
            }`}>
              {task.status === "completed" ? "Success" : task.status === "failed" ? "Failed" : task.status}
            </span>
          </div>
        </div>

        {/* Stats bar */}
        <section className="grid gap-3 grid-cols-3 sm:grid-cols-6">
          {[
            { label: "Duration", value: totalDuration },
            { label: "Model calls", value: String(analysis.model_call_count) },
            { label: "Tool calls", value: String(analysis.tool_call_count) },
            { label: "Input tokens", value: analysis.total_input_tokens > 0 ? `${(analysis.total_input_tokens / 1000).toFixed(0)}k` : "—" },
            { label: "Retries", value: String(analysis.retry_count), warn: analysis.retry_count > 3 },
            { label: "Cost", value: `$${analysis.estimated_total_cost_dollars.toFixed(4)}` },
          ].map(({ label, value, warn }) => (
            <div key={label} className="rounded-xl border border-line bg-white p-3 text-center shadow-sm">
              <p className="text-xs text-slate-400 font-medium">{label}</p>
              <p className={`mt-1 text-xl font-bold ${warn ? "text-red-600" : "text-ink"}`}>{value}</p>
            </div>
          ))}
        </section>

        {/* Time split inline */}
        <section className="rounded-xl border border-line bg-white p-4 shadow-sm">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex-1 flex items-center gap-3 min-w-0">
              <div className="flex items-center gap-1.5 text-sm">
                <span className="h-3 w-3 rounded-sm bg-mint inline-block" />
                <span className="font-medium text-ink">Model {modelPct.toFixed(0)}%</span>
                <span className="text-slate-400">· {(analysis.model_time_ms / 1000).toFixed(1)}s</span>
              </div>
              <div className="flex items-center gap-1.5 text-sm">
                <span className="h-3 w-3 rounded-sm bg-amber-400 inline-block" />
                <span className={`font-medium ${toolPct >= 40 ? "text-amber-700" : "text-ink"}`}>
                  Tool wait {toolPct.toFixed(0)}%{toolPct >= 40 ? " ⚠" : ""}
                </span>
                <span className="text-slate-400">· {(analysis.tool_time_ms / 1000).toFixed(1)}s</span>
              </div>
              <div className="flex items-center gap-1.5 text-sm">
                <span className="h-3 w-3 rounded-sm bg-slate-200 inline-block" />
                <span className="text-slate-500">Idle {idlePct.toFixed(0)}%</span>
              </div>
            </div>
            {prefillHeavy && (
              <span className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
                Input-heavy: {inputOutputRatio}:1 in/out ratio
              </span>
            )}
          </div>
          <div className="mt-3 flex h-3 overflow-hidden rounded-full">
            <div className="bg-mint transition-all" style={{ width: `${modelPct}%` }} />
            <div className="bg-amber-400 transition-all" style={{ width: `${toolPct}%` }} />
            <div className="bg-slate-200 transition-all" style={{ width: `${idlePct}%` }} />
          </div>
        </section>

        {/* Waterfall + Context growth */}
        <div className="grid gap-4 lg:grid-cols-3">

          {/* Waterfall */}
          <div className="lg:col-span-2 rounded-xl border border-line bg-white p-5 shadow-sm">
            <h2 className="mb-1 font-semibold text-ink">Timeline waterfall</h2>
            <p className="mb-4 text-xs text-slate-400">Each bar = elapsed time from start. Tool wait gaps appear as whitespace.</p>
            {waterfall.length === 0 ? (
              <p className="text-sm text-slate-400">Not enough timing data to render waterfall. Capture traces with latency metadata.</p>
            ) : (
              <div className="space-y-2">
                {waterfall.map((span, i) => {
                  const { bar } = eventColor(span.type);
                  return (
                    <div key={i} className="flex items-center gap-2">
                      <div className="w-40 truncate text-right text-xs text-slate-500">{span.name}</div>
                      <div className="relative flex-1 h-6 bg-slate-50 rounded overflow-hidden">
                        <div
                          className={`absolute h-full ${bar} rounded flex items-center px-1.5`}
                          style={{ left: `${span.startPct}%`, width: `${Math.max(span.widthPct, 1.5)}%` }}
                        >
                          {span.tokens ? (
                            <span className="text-white text-xs truncate whitespace-nowrap">
                              {(span.tokens / 1000).toFixed(0)}k tok{span.deltaTokens ? ` +${(span.deltaTokens / 1000).toFixed(1)}k` : ""}
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            <div className="mt-3 flex items-center gap-4 text-xs text-slate-400">
              <span className="flex items-center gap-1"><span className="h-2 w-3 rounded-sm bg-mint inline-block" /> Model</span>
              <span className="flex items-center gap-1"><span className="h-2 w-3 rounded-sm bg-slate-300 inline-block" /> Tool/IO</span>
              <span className="flex items-center gap-1"><span className="h-2 w-3 rounded-sm bg-red-400 inline-block" /> Error</span>
            </div>
          </div>

          {/* Context growth */}
          <div className="rounded-xl border border-line bg-white p-5 shadow-sm">
            <h2 className="mb-1 font-semibold text-ink">Context growth</h2>
            <p className="mb-4 text-xs text-slate-400">Input tokens per model call</p>
            {contextGrowth.length === 0 ? (
              <p className="text-sm text-slate-400">No per-call token data captured.</p>
            ) : (
              <div className="space-y-3">
                {contextGrowth.map(({ call, tokens, delta }) => (
                  <div key={call}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-500">Call {call}</span>
                      <span className="font-semibold text-ink">
                        {(tokens / 1000).toFixed(1)}k
                        {delta > 0 && <span className="text-amber-600 ml-1">+{(delta / 1000).toFixed(1)}k</span>}
                      </span>
                    </div>
                    <div className="h-4 overflow-hidden rounded-full bg-slate-100">
                      <div className="h-full rounded-full bg-mint" style={{ width: maxTokens > 0 ? `${(tokens / maxTokens) * 100}%` : "0%" }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
            {analysis.repeated_context_percent > 15 && (
              <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
                {analysis.repeated_context_percent.toFixed(1)}% of tokens repeated
                <Link href="/context" className="ml-1 font-semibold hover:underline">Inspect →</Link>
              </div>
            )}
          </div>
        </div>

        {/* Recommendations for this run */}
        {optimizations && optimizations.recommendations.length > 0 && (
          <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-semibold text-ink">Optimization opportunities for this run</h2>
              <Link href="/recommendations" className="text-xs font-semibold text-mint hover:underline">See all recommendations →</Link>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {optimizations.recommendations.slice(0, 4).map((rec) => (
                <div key={rec.recommendation_id} className="rounded-lg border border-line bg-panel p-4">
                  <p className="text-xs font-semibold uppercase text-slate-400">{rec.category.replaceAll("_", " ")}</p>
                  <p className="mt-1 font-medium text-ink">{rec.title}</p>
                  <p className="mt-2 text-sm text-slate-600">{rec.evidence}</p>
                  <div className="mt-3 flex gap-2 text-xs text-slate-500">
                    <span className="rounded border border-line bg-white px-2 py-0.5">Save {(rec.estimated_time_savings_ms / 1000).toFixed(1)}s</span>
                    <span className="rounded border border-line bg-white px-2 py-0.5">Save ${rec.estimated_cost_savings_dollars.toFixed(5)}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Event feed */}
        <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
          <h2 className="mb-4 font-semibold text-ink">Event feed</h2>
          <div className="space-y-0.5 font-mono text-xs overflow-x-auto">
            {recentEvents.map((ev, i) => {
              const { text } = eventColor(ev.event_type);
              const attrs = (ev.attributes ?? {}) as Record<string, unknown>;
              const ts = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : "—";
              const detail = ev.event_type === "model_call_end"
                ? `${attrs.input_tokens ?? ""}tok in · ${attrs.output_tokens ?? ""}tok out · ${attrs.latency_ms ?? ""}ms · $${typeof attrs.cost_dollars === "number" ? (attrs.cost_dollars as number).toFixed(5) : "—"}`
                : ev.event_type === "tool_call_end"
                  ? `exit ${attrs.exit_code ?? "?"} · ${attrs.latency_ms ?? ""}ms`
                  : ev.name || "";
              return (
                <div key={i} className={`flex gap-3 rounded px-2 py-1 hover:bg-slate-50 ${ev.event_type === "error_event" ? "bg-red-50" : ev.event_type.includes("task_") ? "bg-teal-50" : ""}`}>
                  <span className="w-20 flex-shrink-0 text-slate-400">{ts}</span>
                  <span className={`w-36 flex-shrink-0 font-semibold ${text}`}>{ev.event_type}</span>
                  <span className="text-slate-600 truncate">{detail}</span>
                </div>
              );
            })}
            {events.length > 20 && (
              <p className="text-slate-400 px-2 py-1">… {events.length - 20} more events</p>
            )}
          </div>
        </section>

        {/* Cross-links */}
        <div className="flex flex-wrap gap-3">
          <Link href="/context" className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:border-mint hover:text-mint transition-colors">
            Inspect context across all runs <ArrowRight size={14} />
          </Link>
          <Link href="/cost" className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:border-mint hover:text-mint transition-colors">
            View cost breakdown <ArrowRight size={14} />
          </Link>
          <Link href="/recommendations" className="inline-flex items-center gap-2 rounded-lg border border-mint bg-teal-50 px-4 py-2 text-sm font-semibold text-mint hover:bg-teal-100 transition-colors">
            Get recommendations <ArrowRight size={14} />
          </Link>
        </div>

      </div>
    </Shell>
  );
}
