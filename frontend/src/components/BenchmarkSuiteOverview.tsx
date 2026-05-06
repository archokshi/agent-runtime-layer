import type { BenchmarkSuiteSummary } from "@/lib/types";

function MetricCard({ label, value, detail }: { label: string; value: string; detail?: string | null }) {
  return (
    <div className="rounded-md border border-line bg-white p-4">
      <div className="text-xs font-medium uppercase text-muted">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
      {detail ? <div className="mt-1 text-sm text-muted">{detail}</div> : null}
    </div>
  );
}

export function BenchmarkSuiteOverview({ summary }: { summary: BenchmarkSuiteSummary }) {
  return (
    <div className="grid gap-5">
      <section className="rounded-md border border-line bg-white p-5">
        <div className="text-sm font-medium text-teal-700">v0.5 benchmark validation</div>
        <h1 className="mt-1 text-3xl font-semibold">Benchmark Suite Integration</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
          First-class records for SWE-bench, Aider, OpenHands, and custom coding-agent validation runs. This records benchmark evidence; it does not run external harnesses automatically.
        </p>
      </section>

      <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <MetricCard label="Runs" value={`${summary.run_count}`} />
        <MetricCard label="Task Results" value={`${summary.task_count}`} />
        <MetricCard label="Trace Completion" value={`${summary.trace_completion_rate_percent}%`} />
        <MetricCard label="Task Success" value={summary.task_success_rate_percent == null ? "Unknown" : `${summary.task_success_rate_percent}%`} />
        <MetricCard label="Actionable Recs" value={summary.actionable_recommendation_rate_percent == null ? "Unknown" : `${summary.actionable_recommendation_rate_percent}%`} />
        <MetricCard label="Suites" value={`${Object.keys(summary.suite_counts).length}`} />
      </section>

      <section className="rounded-md border border-line bg-white p-5">
        <div className="font-semibold">Suite Coverage</div>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          {Object.entries(summary.suite_counts).length ? (
            Object.entries(summary.suite_counts).map(([suite, count]) => (
              <div key={suite} className="rounded-md border border-line bg-panel p-4">
                <div className="text-xs font-medium uppercase text-muted">{suite}</div>
                <div className="mt-2 text-2xl font-semibold">{count}</div>
              </div>
            ))
          ) : (
            <div className="rounded-md border border-line bg-panel p-4 text-sm text-muted">
              No benchmark suite runs recorded yet.
            </div>
          )}
        </div>
      </section>

      <section className="rounded-md border border-line bg-white p-5">
        <div className="font-semibold">Latest Benchmark Runs</div>
        {summary.latest_runs.length ? (
          <div className="mt-4 grid gap-3">
            {summary.latest_runs.map((run) => (
              <div key={run.benchmark_run_id ?? `${run.suite_name}-${run.created_at}`} className="rounded-md border border-line bg-panel p-4">
                <div className="flex flex-wrap justify-between gap-4">
                  <div>
                    <div className="text-xs font-medium uppercase text-muted">{run.suite_name} / {run.run_mode}</div>
                    <div className="mt-1 font-semibold">{run.agent_name}</div>
                  </div>
                  <div className="text-sm text-muted">{run.metrics.task_count} task(s)</div>
                </div>
                <div className="mt-3 grid gap-3 md:grid-cols-4">
                  <MetricCard label="Trace Complete" value={`${run.metrics.trace_completion_rate_percent}%`} />
                  <MetricCard label="Success" value={run.metrics.task_success_rate_percent == null ? "Unknown" : `${run.metrics.task_success_rate_percent}%`} />
                  <MetricCard label="Recommendations" value={run.metrics.actionable_recommendation_rate_percent == null ? "Unknown" : `${run.metrics.actionable_recommendation_rate_percent}%`} />
                  <MetricCard label="Cost" value={`$${run.metrics.total_cost_dollars.toFixed(4)}`} />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-4 rounded-md border border-line bg-panel p-3 text-sm text-muted">
            Add imported benchmark records through `POST /api/benchmarks/runs`.
          </div>
        )}
      </section>

      <section className="rounded-md border border-line bg-white p-5">
        <div className="font-semibold">Limitations</div>
        <div className="mt-3 grid gap-2">
          {summary.limitations.map((limit) => (
            <div key={limit} className="rounded-md border border-line bg-panel p-3 text-sm text-muted">{limit}</div>
          ))}
        </div>
      </section>
    </div>
  );
}
