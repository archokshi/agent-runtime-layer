import Link from "next/link";

import type { TraceCorpusReport } from "@/lib/types";

function StatusBadge({ status }: { status: "ready" | "partial" | "missing" }) {
  const label = status === "ready" ? "Ready" : status === "partial" ? "Partial" : "Missing";
  return <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold capitalize text-muted">{label}</span>;
}

function QualityBadge({ quality }: { quality: "measured" | "estimated" | "inferred" | "missing" }) {
  return <span className="rounded-full border border-line px-2 py-1 text-xs font-semibold text-muted">{quality}</span>;
}

export function TraceCorpusOverview({ report }: { report: TraceCorpusReport }) {
  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-line bg-white p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-sm font-semibold text-accent">Trace Corpus Manager</p>
            <h1 className="mt-2 text-3xl font-black tracking-normal">Corpus readiness for the Agentic Inference System Blueprint.</h1>
            <p className="mt-3 max-w-3xl text-base leading-7 text-muted">
              This report checks whether the local Agent Runtime trace corpus is strong enough to feed agentic inference workload modeling:
              execution graphs, model/tool/I/O split, retries, context lifetime, and outcome distribution.
            </p>
          </div>
          <div className="min-w-40 rounded-lg border border-line bg-panel p-4">
            <p className="text-xs font-semibold uppercase text-muted">Readiness</p>
            <p className="mt-2 text-3xl font-black">{report.readiness_score}/100</p>
            <div className="mt-2"><StatusBadge status={report.readiness_status} /></div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {report.metrics.map((metric) => (
          <div key={metric.label} className="rounded-lg border border-line bg-white p-5">
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs font-semibold uppercase text-muted">{metric.label}</p>
              <QualityBadge quality={metric.quality} />
            </div>
            <p className="mt-3 text-2xl font-black">{metric.value}</p>
            {metric.detail ? <p className="mt-2 text-sm leading-6 text-muted">{metric.detail}</p> : null}
          </div>
        ))}
      </section>

      <section className="rounded-lg border border-line bg-white p-6">
        <h2 className="text-xl font-black">Phase 2 Evidence Needs</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {report.phase2_evidence_needs.map((need) => (
            <div key={need.need_id} className="rounded-lg border border-line bg-panel p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold">{need.label}</h3>
                  <p className="mt-2 text-sm leading-6 text-muted">{need.evidence}</p>
                </div>
                <StatusBadge status={need.status} />
              </div>
              <p className="mt-3 text-sm leading-6">{need.phase2_use}</p>
              <p className="mt-3 text-xs font-semibold uppercase text-muted">Next: {need.next_step}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-line bg-white p-6">
        <h2 className="text-xl font-black">Coverage</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[860px] text-left text-sm">
            <thead>
              <tr className="border-b border-line text-xs uppercase text-muted">
                <th className="py-3">Category</th>
                <th className="py-3">Coverage</th>
                <th className="py-3">Status</th>
                <th className="py-3">Phase 2 consumes</th>
                <th className="py-3">Next step</th>
              </tr>
            </thead>
            <tbody>
              {report.coverage.map((item) => (
                <tr key={item.category} className="border-b border-line align-top">
                  <td className="py-3 font-semibold">{item.category}</td>
                  <td className="py-3">
                    {item.count}
                    {item.target ? `/${item.target}` : ""} ({item.percent}%)
                  </td>
                  <td className="py-3"><StatusBadge status={item.status} /></td>
                  <td className="py-3 text-muted">{item.phase2_consumes}</td>
                  <td className="py-3 text-muted">{item.next_step}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-line bg-white p-6">
          <h2 className="text-xl font-black">Top Agents</h2>
          <div className="mt-4 space-y-2">
            {Object.entries(report.top_agents).length ? (
              Object.entries(report.top_agents).map(([agent, count]) => (
                <div key={agent} className="flex justify-between rounded-md border border-line bg-panel px-3 py-2 text-sm">
                  <span>{agent}</span>
                  <span className="font-semibold">{count}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted">No agent labels captured yet.</p>
            )}
          </div>
        </div>
        <div className="rounded-lg border border-line bg-white p-6">
          <h2 className="text-xl font-black">Top Repos</h2>
          <div className="mt-4 space-y-2">
            {Object.entries(report.top_repos).length ? (
              Object.entries(report.top_repos).map(([repo, count]) => (
                <div key={repo} className="flex justify-between rounded-md border border-line bg-panel px-3 py-2 text-sm">
                  <span>{repo}</span>
                  <span className="font-semibold">{count}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted">No repo metadata captured yet.</p>
            )}
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-line bg-white p-6">
        <h2 className="text-xl font-black">Trace Samples</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[960px] text-left text-sm">
            <thead>
              <tr className="border-b border-line text-xs uppercase text-muted">
                <th className="py-3">Run</th>
                <th className="py-3">Agent</th>
                <th className="py-3">Events</th>
                <th className="py-3">Coverage</th>
                <th className="py-3">Phase 2 value</th>
              </tr>
            </thead>
            <tbody>
              {report.task_summaries.map((task) => (
                <tr key={task.task_id} className="border-b border-line align-top">
                  <td className="py-3">
                    <Link href={`/tasks/${task.task_id}`} className="font-semibold text-accent hover:underline">{task.goal}</Link>
                    <p className="mt-1 text-xs text-muted">{task.task_id}</p>
                  </td>
                  <td className="py-3">{task.agent_name ?? task.agent_type}</td>
                  <td className="py-3">{task.event_count}</td>
                  <td className="py-3 text-muted">
                    {[
                      task.has_model_events ? "model" : null,
                      task.has_tool_events ? "tool" : null,
                      task.has_file_events ? "file" : null,
                      task.has_terminal_events ? "terminal" : null,
                      task.has_context_snapshots ? "context" : null,
                      task.has_outcome_metadata ? "outcome" : null,
                    ].filter(Boolean).join(", ") || "basic"}
                  </td>
                  <td className="py-3 text-muted">{task.phase2_value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-line bg-white p-6">
          <h2 className="text-xl font-black">Next Steps</h2>
          <ul className="mt-4 space-y-2 text-sm leading-6 text-muted">
            {report.next_steps.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
        <div className="rounded-lg border border-line bg-white p-6">
          <h2 className="text-xl font-black">Boundaries</h2>
          <ul className="mt-4 space-y-2 text-sm leading-6 text-muted">
            {report.limitations.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      </section>
    </div>
  );
}
