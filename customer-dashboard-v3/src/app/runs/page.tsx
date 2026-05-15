import Link from "next/link";
import { Shell } from "@/components/Shell";
import { getAllAnalyses, getTasks } from "@/lib/api";

function statusBadge(s: string) {
  if (s === "completed") return <span className="badge badge-green">✓ Success</span>;
  if (s === "failed")    return <span className="badge badge-red">✗ Failed</span>;
  return <span className="badge badge-amber">{s}</span>;
}

export default async function RunsPage() {
  const tasks    = await getTasks().catch(() => []);
  const analyses = await getAllAnalyses(tasks);

  const success = tasks.filter(t => t.status === "completed").length;
  const failed  = tasks.filter(t => t.status === "failed").length;
  const avgCost = analyses.length > 0
    ? analyses.reduce((s, a) => s + a.estimated_total_cost_dollars, 0) / analyses.length : null;

  return (
    <Shell runCount={tasks.length}>
      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

        <div>
          <div className="page-title">Runs</div>
          <div className="page-sub">{tasks.length} traced runs · {success} succeeded · {failed} failed</div>
        </div>

        {/* Summary chips */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,minmax(0,1fr))", gap: 10 }}>
          <div className="stat-chip"><div className="stat-chip-label">Total</div><div className="stat-chip-val">{tasks.length}</div></div>
          <div className="stat-chip"><div className="stat-chip-label">Succeeded</div><div className="stat-chip-val" style={{ color: "var(--green)" }}>{success}</div></div>
          <div className="stat-chip"><div className="stat-chip-label">Failed</div><div className="stat-chip-val" style={{ color: "var(--red)" }}>{failed}</div></div>
          <div className="stat-chip"><div className="stat-chip-label">Avg cost</div><div className="stat-chip-val">{avgCost !== null ? `$${avgCost.toFixed(4)}` : "—"}</div></div>
        </div>

        {/* Table */}
        <div className="data-table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Task goal</th>
                <th>Status</th>
                <th>Duration</th>
                <th>Cost</th>
                <th>Retries</th>
                <th>Repeated ctx%</th>
                <th>Model calls</th>
                <th>Optimize</th>
              </tr>
            </thead>
            <tbody>
              {tasks.length === 0 ? (
                <tr><td colSpan={8} style={{ textAlign: "center", padding: "32px 16px", color: "var(--muted)" }}>No runs yet. Install the SDK and run your agent.</td></tr>
              ) : tasks.map(task => {
                const a = analyses.find(x => x.task_id === task.task_id);
                const ctx = a?.repeated_context_percent ?? 0;
                return (
                  <tr key={task.task_id}>
                    <td>
                      <Link href={`/runs/${task.task_id}`} style={{ display: "block" }}>
                        <div style={{ fontWeight: 500 }}>{task.goal}</div>
                        <div className="td-id">{task.task_id.slice(0, 16)}…</div>
                      </Link>
                    </td>
                    <td>{statusBadge(task.status)}</td>
                    <td className="td-mono">{a ? `${(a.total_task_duration_ms / 1000).toFixed(1)}s` : "—"}</td>
                    <td className="td-mono">{a ? `$${a.estimated_total_cost_dollars.toFixed(4)}` : "—"}</td>
                    <td className="td-mono" style={{ color: a && a.retry_count > 3 ? "var(--red)" : "inherit" }}>{a ? a.retry_count : "—"}</td>
                    <td className="td-mono" style={{ color: ctx >= 55 ? "var(--amber)" : ctx > 0 ? "var(--green)" : "inherit", fontWeight: ctx >= 30 ? 600 : 400 }}>
                      {a ? `${ctx.toFixed(1)}%${ctx >= 55 ? " ⚠" : ""}` : "—"}
                    </td>
                    <td className="td-mono">{a ? a.model_call_count : "—"}</td>
                    <td>
                      {a && ctx >= 20
                        ? <Link href={`/runs/${task.task_id}`}><span className="fix-btn">⚡ Fix it</span></Link>
                        : <span style={{ color: "var(--muted2)", fontSize: 12 }}>—</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <div className="table-footer">⚠ = repeated context ≥55% — highest optimization priority · Click any row to inspect</div>
        </div>

      </div>
    </Shell>
  );
}
