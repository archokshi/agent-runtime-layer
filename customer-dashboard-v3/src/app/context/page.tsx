import Link from "next/link";
import { Shell } from "@/components/Shell";
import { getAllAnalyses, getOptimizedContext, getTasks } from "@/lib/api";

export default async function ContextPage() {
  const tasks    = await getTasks().catch(() => []);
  const analyses = await getAllAnalyses(tasks);
  const n = analyses.length;

  const avgRepeatedPct    = n > 0 ? analyses.reduce((s, a) => s + a.repeated_context_percent, 0) / n : 0;
  const avgInputTokens    = n > 0 ? analyses.reduce((s, a) => s + a.total_input_tokens, 0) / n : 0;
  const avgRepeatedTokens = avgInputTokens * (avgRepeatedPct / 100);

  const highCtxTasks = tasks.filter((_, i) => (analyses[i]?.repeated_context_percent ?? 0) >= 30)
    .slice(0, 1);
  const ctxReport = highCtxTasks.length > 0
    ? await getOptimizedContext(highCtxTasks[0].task_id)
    : null;

  return (
    <Shell runCount={tasks.length}>
      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        <div>
          <div className="page-title">Context Inspector</div>
          <div className="page-sub">Which tokens are you re-sending on every call?</div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(2,minmax(0,1fr))", gap: 12 }}>
          <div className="metric-card" style={{ borderTop: avgRepeatedPct >= 30 ? "3px solid var(--red)" : undefined }}>
            <div className="section-label">Repeated tokens</div>
            <div className="metric-val" style={{ marginTop: 10, color: avgRepeatedPct >= 30 ? "var(--red)" : "var(--ink)" }}>
              {avgRepeatedPct.toFixed(1)}<span style={{ fontSize: 18, opacity: .6, fontFamily: "inherit" }}>%</span>
            </div>
            <div className={`metric-delta ${avgRepeatedPct >= 30 ? "delta-bad" : "delta-neu"}`}>
              ~{(avgRepeatedTokens / 1000).toFixed(1)}k of {(avgInputTokens / 1000).toFixed(1)}k tokens wasted/call
            </div>
          </div>
          <div className="metric-card">
            <div className="section-label">Cache opportunity</div>
            <div className="metric-val" style={{ marginTop: 10 }}>
              ${(avgRepeatedTokens * 2.70 / 1_000_000).toFixed(4)}
            </div>
            <div className="metric-delta delta-good">est. saving per run at cache rates</div>
          </div>
        </div>

        {ctxReport && ctxReport.stable_context_blocks.length > 0 ? (
          <div className="card">
            <div className="card-title" style={{ marginBottom: 14 }}>Stable context blocks — re-sent every call</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {ctxReport.stable_context_blocks.slice(0, 5).map((b, i) => (
                <div key={b.block_id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 14px", background: i === 0 ? "var(--red-lt)" : i === 1 ? "var(--amber-lt)" : "var(--bg)", border: `1px solid ${i === 0 ? "#DC262618" : i === 1 ? "#D9770618" : "var(--border)"}`, borderRadius: 9 }}>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>{b.type.replace(/_/g, " ")}</div>
                    <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2, fontFamily: "var(--mono)" }}>
                      {b.fingerprint.slice(0, 20)}… · seen {b.occurrences}× · action: {b.action}
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 20, fontWeight: 700, fontFamily: "var(--mono)", color: i === 0 ? "var(--red)" : i === 1 ? "var(--amber)" : "var(--muted)" }}>{(b.tokens / 1000).toFixed(1)}k</div>
                    <div className="section-label">tokens/call</div>
                  </div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 12, padding: "10px 12px", background: "var(--mint-lt)", border: "1px solid var(--mint-md)", borderRadius: 8, fontSize: 12, color: "var(--mint)" }}>
              ⚡ Enable Context Optimizer in Settings to strip these blocks — est. −{ctxReport.savings.input_token_reduction_percent.toFixed(0)}% tokens per run.
            </div>
          </div>
        ) : (
          <div className="card">
            <div className="card-title" style={{ marginBottom: 8 }}>Stable context blocks</div>
            <p style={{ fontSize: 13, color: "var(--muted)" }}>
              {n === 0 ? "No traces yet. Run your agent to see context analysis." : "Run the context optimizer on a high-repeated-context run to see stable blocks."}
            </p>
            {n > 0 && <Link href="/runs" className="btn btn-sm" style={{ marginTop: 12, display: "inline-flex" }}>Go to Runs →</Link>}
          </div>
        )}

        <div style={{ display: "flex", gap: 10 }}>
          <Link href="/settings" className="btn btn-primary btn-sm">Enable Context Optimizer →</Link>
          <Link href="/recommendations" className="btn btn-sm">See recommendations →</Link>
        </div>
      </div>
    </Shell>
  );
}
