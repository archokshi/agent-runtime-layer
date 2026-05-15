import Link from "next/link";
import { Shell } from "@/components/Shell";
import { getAllAnalyses, getPhase1ExitPackages, getTasks } from "@/lib/api";

export default async function RecommendationsPage() {
  const tasks    = await getTasks().catch(() => []);
  const analyses = await getAllAnalyses(tasks);
  const reports  = await getPhase1ExitPackages();
  const n = analyses.length;

  const avgRepeatedPct  = n > 0 ? analyses.reduce((s, a) => s + a.repeated_context_percent, 0) / n : 0;
  const totalRetries    = analyses.reduce((s, a) => s + a.retry_count, 0);
  const totalModelMs    = analyses.reduce((s, a) => s + a.model_time_ms, 0);
  const totalToolMs     = analyses.reduce((s, a) => s + a.tool_time_ms, 0);
  const totalMs         = totalModelMs + totalToolMs + analyses.reduce((s, a) => s + a.orchestration_idle_ms, 0);
  const toolPct         = totalMs > 0 ? (totalToolMs / totalMs) * 100 : 0;
  const avgToolSec      = n > 0 ? (totalToolMs / n / 1000).toFixed(1) : "0";
  const avgInputTokens  = n > 0 ? analyses.reduce((s, a) => s + a.total_input_tokens, 0) / n : 0;
  const estSaving       = avgInputTokens * (avgRepeatedPct / 100) * (2.70 / 1_000_000);
  const retryWaste      = analyses.reduce((s, a) => {
    const f = a.model_call_count > 0 ? a.retry_count / a.model_call_count : 0;
    return s + a.estimated_total_cost_dollars * f;
  }, 0);

  const topRecs = reports?.[0]?.workload_recommendation_package?.prioritized_recommendations ?? [];

  type Rec = { priority: string; color: string; label: string; title: string; desc: string; impact: string; linkHref: string; linkLabel: string; };

  const builtInRecs: Rec[] = [
    avgRepeatedPct >= 20 ? {
      priority: "P0", color: "var(--red)", label: "context_optimization",
      title: "Strip stable context from every model call",
      desc: `${avgRepeatedPct.toFixed(1)}% of input tokens are identical across runs. System prompt, tool definitions, and repo summary re-sent every call.`,
      impact: `−${avgRepeatedPct.toFixed(0)}% tokens`, linkHref: "/settings", linkLabel: "Enable in Settings",
    } : null,
    toolPct >= 30 ? {
      priority: "P1", color: "var(--amber)", label: "tool_wait",
      title: "Parallelise independent tool calls",
      desc: `Tool wait accounts for ${toolPct.toFixed(0)}% of elapsed time (${avgToolSec}s avg). Sequential tool calls could run in parallel.`,
      impact: `−${avgToolSec}s/run`, linkHref: "/bottlenecks", linkLabel: "See bottlenecks",
    } : null,
    totalRetries > 0 ? {
      priority: "P2", color: "var(--mint)", label: "retry_reduction",
      title: "Set retry limits to stop cost spirals",
      desc: `${totalRetries} total retries detected. ~$${retryWaste.toFixed(4)} estimated waste. Budget Governor can cap this automatically.`,
      impact: `−$${retryWaste.toFixed(4)}/wasted`, linkHref: "/settings", linkLabel: "Enable Budget Governor",
    } : null,
  ].filter((r): r is Rec => r !== null);

  const allRecs = builtInRecs.length > 0 ? builtInRecs : topRecs.slice(0, 5).map(r => ({
    priority: r.priority, color: r.priority === "P0" ? "var(--red)" : r.priority === "P1" ? "var(--amber)" : "var(--mint)",
    label: "optimization", title: r.title, desc: r.evidence,
    impact: `Score: ${r.score.toFixed(1)}`, linkHref: "/settings", linkLabel: "View settings",
  }));

  return (
    <Shell runCount={tasks.length}>
      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        <div>
          <div className="page-title">Recommendations</div>
          <div className="page-sub">Ranked by impact — highest ROI first</div>
        </div>

        {allRecs.length === 0 ? (
          <div className="card">
            <p style={{ fontSize: 13, color: "var(--muted)" }}>
              {n === 0 ? "No traces yet. Run your agent to generate recommendations." : "No recommendations detected — your agent looks healthy."}
            </p>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {allRecs.map((rec, i) => (
              <div key={i} className="card" style={{ borderLeft: `4px solid ${rec.color}` }}>
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 7 }}>
                      <span className={`badge ${rec.priority === "P0" ? "badge-red" : rec.priority === "P1" ? "badge-amber" : "badge-mint"}`}>
                        {rec.priority} · {rec.priority === "P0" ? "High" : rec.priority === "P1" ? "Medium" : "Low"}
                      </span>
                      <span className="badge badge-muted">{rec.label}</span>
                    </div>
                    <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 5 }}>{rec.title}</div>
                    <div style={{ fontSize: 13, color: "var(--muted)" }}>{rec.desc}</div>
                  </div>
                  <div style={{ textAlign: "right", flexShrink: 0 }}>
                    <div style={{ fontSize: 22, fontWeight: 700, fontFamily: "var(--mono)", color: rec.color }}>{rec.impact}</div>
                    <div style={{ fontSize: 11, color: "var(--muted)" }}>estimated</div>
                  </div>
                </div>
                <div style={{ marginTop: 12 }}>
                  <Link href={rec.linkHref} className="btn btn-primary btn-sm">{rec.linkLabel}</Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Shell>
  );
}
