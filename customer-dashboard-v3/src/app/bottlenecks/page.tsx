import Link from "next/link";
import { Shell } from "@/components/Shell";
import { getAllAnalyses, getTasks } from "@/lib/api";

export default async function BottlenecksPage() {
  const tasks    = await getTasks().catch(() => []);
  const analyses = await getAllAnalyses(tasks);
  const n = analyses.length;

  const totalModelMs = analyses.reduce((s, a) => s + a.model_time_ms, 0);
  const totalToolMs  = analyses.reduce((s, a) => s + a.tool_time_ms, 0);
  const totalIdleMs  = analyses.reduce((s, a) => s + a.orchestration_idle_ms, 0);
  const totalMs = totalModelMs + totalToolMs + totalIdleMs;
  const modelPct = totalMs > 0 ? (totalModelMs / totalMs) * 100 : 0;
  const toolPct  = totalMs > 0 ? (totalToolMs  / totalMs) * 100 : 0;
  const idlePct  = totalMs > 0 ? (totalIdleMs  / totalMs) * 100 : 0;
  const avgModelSec = n > 0 ? (totalModelMs / n / 1000).toFixed(1) : "0";
  const avgToolSec  = n > 0 ? (totalToolMs  / n / 1000).toFixed(1) : "0";
  const avgIdleSec  = n > 0 ? (totalIdleMs  / n / 1000).toFixed(1) : "0";

  return (
    <Shell runCount={tasks.length}>
      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        <div>
          <div className="page-title">Bottlenecks</div>
          <div className="page-sub">Where is your agent&apos;s time going?</div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,minmax(0,1fr))", gap: 12 }}>
          {[
            { label: "Model inference", pct: modelPct, avg: `${avgModelSec}s avg`, warn: false },
            { label: "Tool wait",       pct: toolPct,  avg: `${avgToolSec}s avg`, warn: toolPct >= 40 },
            { label: "Idle / CPU",      pct: idlePct,  avg: `${avgIdleSec}s avg`, warn: false },
          ].map(({ label, pct, avg, warn }) => (
            <div key={label} className="metric-card" style={warn ? { borderTop: "3px solid var(--amber)" } : {}}>
              <div className="section-label" style={warn ? { color: "var(--amber)" } : {}}>{label}{warn ? " ⚠" : ""}</div>
              <div className="metric-val" style={{ marginTop: 10, color: warn ? "var(--amber)" : "var(--ink)" }}>
                {pct.toFixed(0)}<span style={{ fontSize: 18, opacity: .6, fontFamily: "inherit" }}>%</span>
              </div>
              <div className={`metric-delta ${warn ? "delta-bad" : "delta-neu"}`}>{avg}</div>
            </div>
          ))}
        </div>

        {n > 0 && (
          <div className="card">
            <div className="card-title" style={{ marginBottom: 16 }}>Time split across {n} runs</div>
            {[
              { label: "Model inference", pct: modelPct, avg: `${avgModelSec}s`, color: "var(--mint)", warn: false },
              { label: "Tool wait",       pct: toolPct,  avg: `${avgToolSec}s`, color: "var(--amber)", warn: toolPct >= 40 },
              { label: "Idle / CPU",      pct: idlePct,  avg: `${avgIdleSec}s`, color: "var(--border2)", warn: false },
            ].map(({ label, pct, avg, color, warn }) => (
              <div key={label} style={{ marginBottom: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 5 }}>
                  <span style={{ color: warn ? "var(--amber)" : "var(--muted)", fontWeight: warn ? 600 : 400 }}>{label}{warn ? " ⚠" : ""}</span>
                  <span style={{ fontWeight: 600, fontFamily: "var(--mono)", color: warn ? "var(--amber)" : "var(--ink)" }}>{pct.toFixed(0)}% · {avg}</span>
                </div>
                <div className="split-bar">
                  <div style={{ width: `${Math.max(pct, 0)}%`, background: color, height: "100%", borderRadius: "99px" }} />
                </div>
              </div>
            ))}
            {toolPct >= 40 && (
              <div style={{ marginTop: 14, padding: "10px 12px", background: "var(--amber-lt)", border: "1px solid #D9770620", borderRadius: 8, fontSize: 12, color: "var(--amber)" }}>
                ⚠ Tool wait is the #1 bottleneck. Parallelising tool calls could save ~{(totalToolMs / 1000 / Math.max(n, 1)).toFixed(1)}s per run.
              </div>
            )}
          </div>
        )}

        <div style={{ display: "flex", gap: 10 }}>
          <Link href="/recommendations" className="btn btn-primary btn-sm">See recommendations →</Link>
          <Link href="/context" className="btn btn-sm">Inspect context →</Link>
        </div>
      </div>
    </Shell>
  );
}
