import Link from "next/link";
import { Shell } from "@/components/Shell";
import { getAllAnalyses, getTasks } from "@/lib/api";

export default async function CostPage() {
  const tasks    = await getTasks().catch(() => []);
  const analyses = await getAllAnalyses(tasks);
  const n = analyses.length;

  const total    = analyses.reduce((s, a) => s + a.estimated_total_cost_dollars, 0);
  const success  = analyses.filter(a => tasks.find(t => t.task_id === a.task_id)?.status === "completed");
  const failed   = analyses.filter(a => tasks.find(t => t.task_id === a.task_id)?.status === "failed");
  const avgSucc  = success.length > 0 ? success.reduce((s, a) => s + a.estimated_total_cost_dollars, 0) / success.length : null;
  const costFail = failed.reduce((s, a) => s + a.estimated_total_cost_dollars, 0);
  const retryWaste = analyses.reduce((s, a) => {
    const f = a.model_call_count > 0 ? a.retry_count / a.model_call_count : 0;
    return s + a.estimated_total_cost_dollars * f;
  }, 0);

  return (
    <Shell runCount={tasks.length}>
      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
        <div>
          <div className="page-title">Cost Explorer</div>
          <div className="page-sub">Cost per task, per failure, and before/after comparison</div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,minmax(0,1fr))", gap: 12 }}>
          <div className="metric-card">
            <div className="section-label">Total cost ({n} runs)</div>
            <div className="metric-val" style={{ marginTop: 10 }}>${total.toFixed(4)}</div>
            <div className="metric-delta delta-neu">{n} total runs</div>
          </div>
          <div className="metric-card">
            <div className="section-label">Avg cost / success</div>
            <div className="metric-val" style={{ marginTop: 10 }}>{avgSucc !== null ? `$${avgSucc.toFixed(4)}` : "—"}</div>
            <div className="metric-delta delta-neu">{success.length} successful runs</div>
          </div>
          <div className="metric-card" style={{ borderTop: costFail > 0 ? "3px solid var(--red)" : undefined }}>
            <div className="section-label">Wasted on failures</div>
            <div className="metric-val" style={{ marginTop: 10, color: costFail > 0 ? "var(--red)" : "var(--ink)" }}>${costFail.toFixed(4)}</div>
            <div className={`metric-delta ${costFail > 0 ? "delta-bad" : "delta-neu"}`}>{failed.length} failed run{failed.length !== 1 ? "s" : ""}</div>
          </div>
        </div>

        {retryWaste > 0 && (
          <div style={{ background: "var(--amber-lt)", border: "1px solid #D9770620", borderRadius: 12, padding: "14px 18px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: "var(--amber)" }}>Retry waste detected</div>
              <div style={{ fontSize: 12, color: "var(--amber)", marginTop: 2 }}>
                ~${retryWaste.toFixed(4)} estimated cost from retry overhead
              </div>
            </div>
            <Link href="/settings" style={{ fontSize: 12, fontWeight: 600, color: "var(--amber)" }}>Enable Budget Governor →</Link>
          </div>
        )}

        <div className="card">
          <div className="card-title" style={{ marginBottom: 14 }}>Cost per run</div>
          {tasks.length === 0 ? (
            <p style={{ fontSize: 13, color: "var(--muted)" }}>No runs yet.</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {tasks.slice(0, 10).map(task => {
                const a = analyses.find(x => x.task_id === task.task_id);
                const isSuccess = task.status === "completed";
                const isFailed  = task.status === "failed";
                return (
                  <div key={task.task_id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "12px 14px", background: isFailed ? "var(--red-lt)" : "var(--bg)", border: `1px solid ${isFailed ? "#DC262618" : "var(--border)"}`, borderRadius: 9 }}>
                    <div style={{ flex: 1, fontSize: 13, fontWeight: 500 }}>{task.goal}</div>
                    {a && <span style={{ fontSize: 12, color: "var(--muted2)", fontFamily: "var(--mono)" }}>${a.estimated_total_cost_dollars.toFixed(4)}</span>}
                    {isFailed
                      ? <span style={{ fontSize: 13, fontWeight: 700, color: "var(--red)", fontFamily: "var(--mono)" }}>Failed</span>
                      : <span className={`badge ${isSuccess ? "badge-green" : "badge-muted"}`}>{isSuccess ? "✓" : task.status}</span>}
                    {isFailed && <span className="badge badge-red">wasted</span>}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div style={{ display: "flex", gap: 10 }}>
          <Link href="/recommendations" className="btn btn-primary btn-sm">See recommendations →</Link>
          <Link href="/settings" className="btn btn-sm">Enable Budget Governor →</Link>
        </div>
      </div>
    </Shell>
  );
}
