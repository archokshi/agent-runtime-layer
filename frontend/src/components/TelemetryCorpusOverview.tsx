import Link from "next/link";

import type { TelemetryCorpusReport } from "@/lib/types";

function StatusBadge({ status }: { status: "ready" | "partial" | "missing" }) {
  return <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold capitalize text-muted">{status}</span>;
}

function FieldLabel({ field }: { field: string }) {
  const labels: Record<string, string> = {
    gpu_utilization_percent: "GPU utilization",
    cpu_utilization_percent: "CPU utilization",
    gpu_memory_used_percent: "Memory pressure",
    queue_depth: "Queue depth",
    prefill_ms: "Prefill time",
    decode_ms: "Decode time",
    kv_cache_hit_rate: "KV/cache hit rate",
  };
  return <>{labels[field] ?? field}</>;
}

export function TelemetryCorpusOverview({ report }: { report: TelemetryCorpusReport }) {
  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-line bg-white p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-sm font-semibold text-accent">Backend/System Telemetry Evidence</p>
            <h1 className="mt-2 text-3xl font-black tracking-normal">Can the workload explain backend and hardware symptoms?</h1>
            <p className="mt-3 max-w-3xl text-base leading-7 text-muted">
              This summarizes imported telemetry coverage for GPU utilization, CPU orchestration, memory pressure, queue depth, prefill/decode timing, and cache hit behavior. It is evidence readiness, not live cluster monitoring.
            </p>
          </div>
          <div className="min-w-40 rounded-lg border border-line bg-panel p-4">
            <p className="text-xs font-semibold uppercase text-muted">Readiness</p>
            <p className="mt-2 text-3xl font-black">{report.readiness_score}/100</p>
            <div className="mt-2"><StatusBadge status={report.readiness_status} /></div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        <div className="rounded-lg border border-line bg-white p-5">
          <p className="text-xs font-semibold uppercase text-muted">Telemetry Tasks</p>
          <p className="mt-3 text-2xl font-black">{report.telemetry_task_count}/{report.task_count}</p>
          <p className="mt-2 text-sm text-muted">{report.telemetry_task_coverage_percent}% coverage</p>
        </div>
        <div className="rounded-lg border border-line bg-white p-5">
          <p className="text-xs font-semibold uppercase text-muted">Samples</p>
          <p className="mt-3 text-2xl font-black">{report.sample_count}</p>
          <p className="mt-2 text-sm text-muted">imported telemetry points</p>
        </div>
        <div className="rounded-lg border border-line bg-white p-5">
          <p className="text-xs font-semibold uppercase text-muted">Backends</p>
          <p className="mt-3 text-2xl font-black">{report.backend_count}</p>
          <p className="mt-2 text-sm text-muted">backend IDs observed</p>
        </div>
        <div className="rounded-lg border border-line bg-white p-5">
          <p className="text-xs font-semibold uppercase text-muted">Bottlenecks</p>
          <p className="mt-3 text-2xl font-black">{Object.keys(report.bottleneck_counts).length}</p>
          <p className="mt-2 text-sm text-muted">classifier categories</p>
        </div>
      </section>

      <section className="rounded-lg border border-line bg-white p-6">
        <h2 className="text-xl font-black">Telemetry Field Coverage</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {report.field_coverage.map((field) => (
            <div key={field.field} className="rounded-lg border border-line bg-panel p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold"><FieldLabel field={field.field} /></h3>
                  <p className="mt-1 text-sm text-muted">
                    {field.task_count} task(s), {field.sample_count} sample(s), {field.percent_of_telemetry_tasks}% telemetry-task coverage
                  </p>
                </div>
                <StatusBadge status={field.status} />
              </div>
              <p className="mt-3 text-sm leading-6">{field.phase2_use}</p>
              <p className="mt-3 text-xs font-semibold uppercase text-muted">Next: {field.next_step}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-line bg-white p-6">
        <h2 className="text-xl font-black">Phase 2 Evidence Value</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {report.phase2_evidence_value.map((need) => (
            <div key={need.need_id} className="rounded-lg border border-line bg-panel p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold">{need.label}</h3>
                  <p className="mt-2 text-sm leading-6 text-muted">{need.evidence}</p>
                </div>
                <StatusBadge status={need.status} />
              </div>
              <p className="mt-3 text-sm leading-6">{need.phase2_use}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-line bg-white p-6">
          <h2 className="text-xl font-black">Detected Bottleneck Counts</h2>
          <div className="mt-4 grid gap-2">
            {Object.entries(report.bottleneck_counts).length ? Object.entries(report.bottleneck_counts).map(([category, count]) => (
              <div key={category} className="flex justify-between rounded-md border border-line bg-panel px-3 py-2 text-sm">
                <span>{category}</span>
                <span className="font-semibold">{count}</span>
              </div>
            )) : <p className="text-sm text-muted">No telemetry bottlenecks detected yet.</p>}
          </div>
        </div>
        <div className="rounded-lg border border-line bg-white p-6">
          <h2 className="text-xl font-black">Next Steps</h2>
          <ul className="mt-4 space-y-2 text-sm leading-6 text-muted">
            {report.next_steps.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      </section>

      <section className="rounded-lg border border-line bg-white p-6">
        <h2 className="text-xl font-black">Telemetry Task Samples</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[860px] text-left text-sm">
            <thead>
              <tr className="border-b border-line text-xs uppercase text-muted">
                <th className="py-3">Task</th>
                <th className="py-3">Samples</th>
                <th className="py-3">Backends</th>
                <th className="py-3">Measured fields</th>
                <th className="py-3">Bottlenecks</th>
              </tr>
            </thead>
            <tbody>
              {report.task_summaries.map((task) => (
                <tr key={task.task_id} className="border-b border-line align-top">
                  <td className="py-3">
                    <Link href={`/tasks/${task.task_id}`} className="font-semibold text-accent hover:underline">{task.goal}</Link>
                    <p className="mt-1 text-xs text-muted">{task.task_id}</p>
                  </td>
                  <td className="py-3">{task.sample_count}</td>
                  <td className="py-3">{task.backend_ids.join(", ") || "n/a"}</td>
                  <td className="py-3 text-muted">
                    {[
                      task.has_gpu_utilization ? "gpu" : null,
                      task.has_cpu_utilization ? "cpu" : null,
                      task.has_memory_pressure ? "memory" : null,
                      task.has_queue_depth ? "queue" : null,
                      task.has_prefill_decode ? "prefill/decode" : null,
                      task.has_cache_hit_rate ? "cache" : null,
                    ].filter(Boolean).join(", ") || "none"}
                  </td>
                  <td className="py-3 text-muted">{task.detected_bottlenecks.join(", ") || "none"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-lg border border-line bg-white p-6">
        <h2 className="text-xl font-black">Boundaries</h2>
        <ul className="mt-4 space-y-2 text-sm leading-6 text-muted">
          {report.limitations.map((item) => <li key={item}>{item}</li>)}
        </ul>
      </section>
    </div>
  );
}
