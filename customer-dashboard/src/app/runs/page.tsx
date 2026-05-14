import Link from "next/link";
import { Shell } from "@/components/Shell";
import { getAllAnalyses, getTasks } from "@/lib/api";
import { ArrowLeft, ArrowUpDown } from "lucide-react";

function statusStyle(s: string) {
  if (s === "completed") return "border-teal-200 bg-teal-50 text-teal-700";
  if (s === "failed") return "border-red-200 bg-red-50 text-red-700";
  return "border-amber-200 bg-amber-50 text-amber-700";
}
function statusLabel(s: string) {
  if (s === "completed") return "Success";
  if (s === "failed") return "Failed";
  return s;
}

export default async function RunsPage() {
  const tasks = await getTasks().catch(() => []);
  const analyses = await getAllAnalyses(tasks);

  const successCount = tasks.filter((t) => t.status === "completed").length;
  const failedCount = tasks.filter((t) => t.status === "failed").length;

  return (
    <Shell hasData>
      <div className="grid gap-5">

        {/* Breadcrumb + header */}
        <div>
          <Link href="/" className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-mint mb-2">
            <ArrowLeft size={12} /> Overview
          </Link>
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold text-ink">Runs</h1>
              <p className="mt-1 text-sm text-slate-500">
                {tasks.length} traced runs · {successCount} succeeded · {failedCount} failed
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <ArrowUpDown size={12} /> Click a run to inspect its waterfall timeline
            </div>
          </div>
        </div>

        {/* Summary cards */}
        <div className="grid gap-3 sm:grid-cols-4">
          {[
            { label: "Total runs", value: String(tasks.length), color: "text-ink" },
            { label: "Successful", value: String(successCount), color: "text-teal-700" },
            { label: "Failed", value: String(failedCount), color: "text-red-600" },
            {
              label: "Avg cost",
              value: analyses.length > 0
                ? `$${(analyses.reduce((s, a) => s + a.estimated_total_cost_dollars, 0) / analyses.length).toFixed(4)}`
                : "—",
              color: "text-ink"
            },
          ].map(({ label, value, color }) => (
            <div key={label} className="rounded-xl border border-line bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase text-slate-400">{label}</p>
              <p className={`mt-2 text-2xl font-bold ${color}`}>{value}</p>
            </div>
          ))}
        </div>

        {/* Table */}
        <div className="rounded-xl border border-line bg-white shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <th className="px-5 py-3 text-left">Task goal</th>
                <th className="px-5 py-3 text-left">Status</th>
                <th className="px-5 py-3 text-left">Duration</th>
                <th className="px-5 py-3 text-left">Cost</th>
                <th className="px-5 py-3 text-left">Retries</th>
                <th className="px-5 py-3 text-left">Repeated CTX%</th>
                <th className="px-5 py-3 text-left">Model calls</th>
                <th className="px-5 py-3 text-left">Optimize</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {tasks.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-5 py-8 text-center text-sm text-slate-400">
                    No runs yet.{" "}
                    <Link href="/import" className="text-mint hover:underline">Import a trace</Link> to get started.
                  </td>
                </tr>
              ) : (
                tasks.map((task) => {
                  const a = analyses.find((x) => x.task_id === task.task_id);
                  const ctxPct = a?.repeated_context_percent ?? 0;
                  const isHighCtx = ctxPct >= 55;
                  return (
                    <tr key={task.task_id} className="hover:bg-teal-50 transition-colors cursor-pointer group">
                      <td className="px-5 py-3">
                        <Link href={`/runs/${task.task_id}`} className="block">
                          <span className="font-medium text-ink group-hover:text-mint transition-colors">{task.goal}</span>
                          <span className="block text-xs text-slate-400 mt-0.5">{task.task_id.slice(0, 16)}…</span>
                        </Link>
                      </td>
                      <td className="px-5 py-3">
                        <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${statusStyle(task.status)}`}>
                          {statusLabel(task.status)}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-slate-600">{a ? `${(a.total_task_duration_ms / 1000).toFixed(1)}s` : "—"}</td>
                      <td className="px-5 py-3 text-slate-600">{a ? `$${a.estimated_total_cost_dollars.toFixed(4)}` : "—"}</td>
                      <td className={`px-5 py-3 font-medium ${a && a.retry_count > 3 ? "text-red-600" : "text-slate-600"}`}>
                        {a ? a.retry_count : "—"}
                      </td>
                      <td className={`px-5 py-3 font-semibold ${isHighCtx ? "text-red-600" : ctxPct > 30 ? "text-amber-700" : "text-teal-700"}`}>
                        {a ? `${ctxPct.toFixed(1)}%${isHighCtx ? " ⚠" : ""}` : "—"}
                      </td>
                      <td className="px-5 py-3 text-slate-600">{a ? a.model_call_count : "—"}</td>
                      <td className="px-5 py-3">
                        {a && a.repeated_context_percent >= 20 ? (
                          <Link href={`/runs/${task.task_id}`} className="inline-flex items-center gap-1 rounded-full border border-teal-200 bg-teal-50 px-2 py-0.5 text-xs font-semibold text-teal-700 hover:bg-teal-100 transition-colors">
                            ⚡ Fix it
                          </Link>
                        ) : (
                          <span className="text-xs text-slate-300">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
          <div className="border-t border-line bg-slate-50 px-5 py-2 text-xs text-slate-400">
            ⚠ = repeated context above 55% — highest optimization priority · Click any row to inspect the waterfall
          </div>
        </div>

        {/* Cross-links */}
        <div className="flex flex-wrap gap-3">
          <Link href="/context" className="rounded-lg border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:border-mint hover:text-mint transition-colors">
            Inspect repeated context across all runs →
          </Link>
          <Link href="/cost" className="rounded-lg border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:border-mint hover:text-mint transition-colors">
            Explore cost breakdown →
          </Link>
        </div>

      </div>
    </Shell>
  );
}
