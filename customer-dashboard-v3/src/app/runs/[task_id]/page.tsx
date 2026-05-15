import Link from "next/link";
import { Shell } from "@/components/Shell";
import { ApplyOptimizationButton } from "@/components/ApplyOptimizationButton";
import { getAnalysis, getEvents, getOptimizedContext, getOptimizations, getTask } from "@/lib/api";
import type { TraceEvent } from "@/lib/types";

async function optional<T>(p: Promise<T>): Promise<T | null> {
  try { return await p; } catch { return null; }
}

function eventColor(type: string): string {
  if (type.startsWith("model_call")) return "var(--mint)";
  if (type === "error_event")        return "var(--red)";
  if (type.includes("task_"))        return "#4F46E5";
  return "var(--muted)";
}

function buildWaterfall(events: TraceEvent[], totalMs: number) {
  if (events.length < 2 || totalMs <= 0) return [];
  const sorted   = [...events].sort((a, b) => a.timestamp.localeCompare(b.timestamp));
  const startTime = new Date(sorted[0].timestamp).getTime();
  const endTime   = startTime + totalMs;
  return sorted
    .filter(ev => ["model_call_start","model_call_end","tool_call_start","tool_call_end","terminal_event","error_event","task_start","task_end"].includes(ev.event_type))
    .slice(0, 10)
    .map(ev => {
      const attrs   = (ev.attributes ?? {}) as Record<string, unknown>;
      const evStart = new Date(ev.timestamp).getTime();
      const startPct = Math.max(0, ((evStart - startTime) / (endTime - startTime)) * 100);
      const dur      = typeof attrs.latency_ms === "number" ? attrs.latency_ms as number : typeof attrs.duration_ms === "number" ? attrs.duration_ms as number : 800;
      const widthPct = Math.max(0.5, (dur / totalMs) * 100);
      const tokens   = typeof attrs.input_tokens === "number" ? attrs.input_tokens as number : undefined;
      return { name: ev.name || ev.event_type, type: ev.event_type, startPct, widthPct: Math.min(widthPct, 100 - startPct), tokens };
    });
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

  const totalMs   = analysis.total_task_duration_ms;
  const modelPct  = totalMs > 0 ? (analysis.model_time_ms / totalMs) * 100 : 0;
  const toolPct   = totalMs > 0 ? (analysis.tool_time_ms  / totalMs) * 100 : 0;
  const idlePct   = totalMs > 0 ? (analysis.orchestration_idle_ms / totalMs) * 100 : 0;

  const waterfall = buildWaterfall(events, totalMs);

  const modelEvents = events.filter(e => e.event_type === "model_call_end")
    .sort((a, b) => a.timestamp.localeCompare(b.timestamp));
  const contextGrowth = modelEvents.map((e, i) => {
    const attrs  = (e.attributes ?? {}) as Record<string, unknown>;
    const tokens = typeof attrs.input_tokens === "number" ? attrs.input_tokens as number : 0;
    const prev   = i > 0 ? (() => { const pa = (modelEvents[i-1].attributes ?? {}) as Record<string, unknown>; return typeof pa.input_tokens === "number" ? pa.input_tokens as number : 0; })() : 0;
    return { call: i + 1, tokens, delta: i > 0 ? tokens - prev : 0 };
  });
  const maxTokens = contextGrowth.length > 0 ? Math.max(...contextGrowth.map(c => c.tokens)) : 0;

  const recentEvents = events.sort((a, b) => a.timestamp.localeCompare(b.timestamp)).slice(0, 20);

  function barColor(type: string) {
    if (type.startsWith("model_call")) return "var(--mint)";
    if (type === "error_event")        return "var(--red)";
    if (type.includes("task_"))        return "#4F46E5";
    return "var(--surface)";
  }
  function barTextColor(type: string) {
    if (type.startsWith("model_call")) return "#fff";
    if (type === "error_event")        return "#fff";
    if (type.includes("task_"))        return "#fff";
    return "var(--muted)";
  }

  return (
    <Shell>
      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

        {/* Title */}
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
          <div>
            <div className="page-title">{task.goal}</div>
            <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 4, fontFamily: "var(--mono)" }}>{task.task_id}</div>
          </div>
          <span className={`badge ${task.status === "completed" ? "badge-green" : task.status === "failed" ? "badge-red" : "badge-amber"}`} style={{ fontSize: 13, padding: "5px 12px", flexShrink: 0 }}>
            {task.status === "completed" ? "✓ Success" : task.status === "failed" ? "✗ Failed" : task.status}
          </span>
        </div>

        {/* Stat chips */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(6,minmax(0,1fr))", gap: 8 }}>
          {[
            { label: "Duration",     val: totalMs > 0 ? `${(totalMs/1000).toFixed(1)}s` : "—" },
            { label: "Model calls",  val: String(analysis.model_call_count) },
            { label: "Tool calls",   val: String(analysis.tool_call_count) },
            { label: "Input tokens", val: analysis.total_input_tokens > 0 ? `${(analysis.total_input_tokens/1000).toFixed(0)}k` : "—" },
            { label: "Retries",      val: String(analysis.retry_count), warn: analysis.retry_count > 3 },
            { label: "Cost",         val: `$${analysis.estimated_total_cost_dollars.toFixed(4)}` },
          ].map(({ label, val, warn }) => (
            <div key={label} className="stat-chip">
              <div className="stat-chip-label">{label}</div>
              <div className="stat-chip-val" style={warn ? { color: "var(--amber)" } : {}}>{val}</div>
            </div>
          ))}
        </div>

        {/* Time split */}
        <div className="card card-sm">
          <div style={{ display: "flex", alignItems: "center", gap: 20, flexWrap: "wrap", marginBottom: 8 }}>
            {[
              { label: "Model", pct: modelPct, sec: (analysis.model_time_ms/1000).toFixed(1), color: "var(--mint)", warn: false },
              { label: "Tool wait", pct: toolPct, sec: (analysis.tool_time_ms/1000).toFixed(1), color: "var(--amber)", warn: toolPct >= 40 },
              { label: "Idle", pct: idlePct, sec: (analysis.orchestration_idle_ms/1000).toFixed(1), color: "var(--border2)", warn: false },
            ].map(({ label, pct, sec, color, warn }) => (
              <div key={label} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12 }}>
                <span style={{ width: 10, height: 10, borderRadius: 3, background: color, display: "inline-block" }} />
                <span style={{ fontWeight: 600, color: warn ? "var(--amber)" : "var(--ink)" }}>{label} {pct.toFixed(0)}%{warn ? " ⚠" : ""}</span>
                <span style={{ color: "var(--muted)", fontFamily: "var(--mono)" }}>· {sec}s</span>
              </div>
            ))}
          </div>
          <div style={{ display: "flex", height: 7, borderRadius: 99, overflow: "hidden", background: "var(--surface)" }}>
            <div style={{ width: `${modelPct}%`, background: "var(--mint)" }} />
            <div style={{ width: `${toolPct}%`,  background: "var(--amber)" }} />
            <div style={{ width: `${idlePct}%`,  background: "var(--border2)" }} />
          </div>
        </div>

        {/* Apply optimization */}
        {analysis.repeated_context_percent >= 15 && (
          <ApplyOptimizationButton taskId={task_id} />
        )}

        {/* Waterfall + right panel */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 270px", gap: 14 }}>
          {/* Waterfall */}
          <div className="card">
            <div className="card-title" style={{ marginBottom: 3 }}>Timeline waterfall</div>
            <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 14 }}>Elapsed time from task start</div>
            {waterfall.length === 0 ? (
              <p style={{ fontSize: 13, color: "var(--muted)" }}>Not enough timing data to render waterfall.</p>
            ) : waterfall.map((span, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                <div className="waterfall-label">{span.name}</div>
                <div className="waterfall-track">
                  <div className="waterfall-bar" style={{ left: `${span.startPct}%`, width: `${Math.max(span.widthPct, 1.5)}%`, background: barColor(span.type), color: barTextColor(span.type), border: span.type.includes("tool_") || span.type === "terminal_event" ? "1px solid var(--border)" : undefined }}>
                    {span.tokens ? `${(span.tokens/1000).toFixed(0)}k` : ""}
                  </div>
                </div>
              </div>
            ))}
            <div style={{ display: "flex", gap: 14, marginTop: 12 }}>
              {[{ color: "var(--mint)", label: "Model" }, { color: "var(--surface)", label: "Tool", border: "1px solid var(--border)" }, { color: "#4F46E5", label: "Task" }].map(({ color, label, border }) => (
                <span key={label} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11, color: "var(--muted)" }}>
                  <span style={{ width: 10, height: 4, background: color, borderRadius: 2, display: "inline-block", border }} />
                  {label}
                </span>
              ))}
            </div>
          </div>

          {/* Context growth + event feed */}
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div className="card">
              <div className="card-title" style={{ marginBottom: 12 }}>Context growth</div>
              {contextGrowth.length === 0 ? (
                <p style={{ fontSize: 12, color: "var(--muted)" }}>No per-call token data captured.</p>
              ) : contextGrowth.map(({ call, tokens, delta }) => (
                <div key={call} style={{ marginBottom: 10 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 5, fontFamily: "var(--mono)" }}>
                    <span style={{ color: "var(--muted)" }}>Call {call}</span>
                    <span style={{ fontWeight: 600 }}>
                      {(tokens/1000).toFixed(1)}k
                      {delta > 0 && <span style={{ color: "var(--amber)", marginLeft: 4 }}>+{(delta/1000).toFixed(1)}k</span>}
                    </span>
                  </div>
                  <div className="ctx-bar-track">
                    <div className="ctx-bar-fill" style={{ width: maxTokens > 0 ? `${(tokens/maxTokens)*100}%` : "0%" }} />
                  </div>
                </div>
              ))}
              {analysis.repeated_context_percent > 15 && (
                <div style={{ marginTop: 10, padding: "8px 10px", background: "var(--red-lt)", border: "1px solid #DC262618", borderRadius: 7, fontSize: 11, color: "var(--red)" }}>
                  {analysis.repeated_context_percent.toFixed(1)}% tokens repeated
                  <Link href="/context" style={{ marginLeft: 6, fontWeight: 600, color: "var(--mint)" }}>Inspect →</Link>
                </div>
              )}
            </div>

            <div className="card">
              <div className="card-title" style={{ marginBottom: 10 }}>Event feed</div>
              {recentEvents.map((ev, i) => {
                const attrs = (ev.attributes ?? {}) as Record<string, unknown>;
                const ts    = new Date(ev.timestamp).toLocaleTimeString();
                const detail = ev.event_type === "model_call_end"
                  ? `${attrs.input_tokens ?? ""}tok in · ${attrs.output_tokens ?? ""}tok out · $${typeof attrs.cost_dollars === "number" ? (attrs.cost_dollars as number).toFixed(5) : "—"}`
                  : ev.name || "";
                return (
                  <div key={i} className="event-row">
                    <span style={{ color: "var(--muted2)", width: 68, flexShrink: 0 }}>{ts}</span>
                    <span style={{ width: 150, flexShrink: 0, color: eventColor(ev.event_type) }}>{ev.event_type}</span>
                    <span style={{ color: "var(--muted)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{detail}</span>
                  </div>
                );
              })}
              {events.length > 20 && <p style={{ fontSize: 11, color: "var(--muted)", padding: "4px 0" }}>… {events.length - 20} more events</p>}
            </div>
          </div>
        </div>

        {/* Recommendations for this run */}
        {optimizations && optimizations.recommendations.length > 0 && (
          <div className="card">
            <div className="card-title" style={{ marginBottom: 14 }}>Optimization opportunities for this run</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(2,minmax(0,1fr))", gap: 10 }}>
              {optimizations.recommendations.slice(0, 4).map(rec => (
                <div key={rec.recommendation_id} style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 9, padding: 14 }}>
                  <div className="section-label">{rec.category.replaceAll("_", " ")}</div>
                  <div style={{ fontSize: 13, fontWeight: 600, marginTop: 5 }}>{rec.title}</div>
                  <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 5 }}>{rec.evidence}</div>
                  <div style={{ marginTop: 10, display: "flex", gap: 6, flexWrap: "wrap" }}>
                    <span className="badge badge-muted">Save {(rec.estimated_time_savings_ms/1000).toFixed(1)}s</span>
                    <span className="badge badge-muted">Save ${rec.estimated_cost_savings_dollars.toFixed(5)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Cross-links */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          <Link href="/context" className="btn btn-sm">Inspect context →</Link>
          <Link href="/cost" className="btn btn-sm">View cost breakdown →</Link>
          <Link href="/recommendations" className="btn btn-primary btn-sm">See recommendations →</Link>
        </div>

      </div>
    </Shell>
  );
}
