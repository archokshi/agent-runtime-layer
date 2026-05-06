import type { PlatformSummary } from "@/lib/types";

function statusClass(status: string) {
  if (status === "complete" || status === "ready") {
    return "border-teal-200 bg-teal-50 text-teal-900";
  }
  if (status === "partial") {
    return "border-amber-200 bg-amber-50 text-amber-900";
  }
  return "border-line bg-panel text-muted";
}

function MetricCard({ label, value, detail }: { label: string; value: string; detail?: string | null }) {
  return (
    <div className="rounded-md border border-line bg-white p-4">
      <div className="text-xs font-medium uppercase text-muted">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
      {detail ? <div className="mt-1 truncate text-sm text-muted">{detail}</div> : null}
    </div>
  );
}

export function PlatformOverview({ summary }: { summary: PlatformSummary }) {
  return (
    <div className="grid gap-5">
      <section className="rounded-md border border-line bg-white p-5">
        <div className="text-sm font-medium text-teal-700">{summary.platform_version} local platform</div>
        <h1 className="mt-1 text-3xl font-semibold">Agentic Inference Platform</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
          One local overview for traces, optimization, scheduler decisions, backend hints, hardware telemetry, Silicon Blueprints, and replay projections.
        </p>
      </section>

      <section className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        {summary.metrics.map((metric) => (
          <MetricCard key={metric.label} label={metric.label} value={metric.value} detail={metric.detail} />
        ))}
      </section>

      <section className="rounded-md border border-line bg-white p-5">
        <div className="mb-4 font-semibold">End-to-End Runbook</div>
        <div className="grid gap-3 lg:grid-cols-4">
          {summary.runbook.map((step) => (
            <div key={step.step_id} className={`rounded-md border p-4 ${statusClass(step.status)}`}>
              <div className="text-xs font-semibold uppercase">{step.status}</div>
              <div className="mt-1 font-semibold">{step.label}</div>
              <p className="mt-2 text-sm leading-6">{step.evidence}</p>
              <p className="mt-2 text-xs leading-5">{step.next_step}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <div className="rounded-md border border-line bg-white p-5">
          <div className="mb-4 font-semibold">Readiness Scores</div>
          <div className="grid gap-3">
            {summary.readiness.map((item) => (
              <div key={item.category} className="rounded-md border border-line bg-panel p-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <div className="font-semibold">{item.category}</div>
                    <div className="mt-1 text-xs font-medium uppercase text-muted">{item.status}</div>
                  </div>
                  <div className="text-2xl font-semibold">{item.score}</div>
                </div>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-white">
                  <div className="h-full bg-teal-700" style={{ width: `${Math.min(100, item.score)}%` }} aria-hidden />
                </div>
                <p className="mt-3 text-sm leading-6 text-muted">{item.rationale}</p>
                <p className="mt-2 text-xs leading-5 text-muted">{item.next_step}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-md border border-line bg-white p-5">
          <div className="mb-4 font-semibold">Module Coverage</div>
          <div className="grid gap-3">
            {summary.module_coverage.map((item) => (
              <div key={item.module} className="rounded-md border border-line bg-panel p-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <div className="font-semibold">{item.module}</div>
                    <p className="mt-1 text-sm leading-6 text-muted">{item.description}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-semibold">{item.count}</div>
                    <div className="text-xs font-medium uppercase text-muted">{item.status}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="rounded-md border border-line bg-white p-5">
        <div className="font-semibold">Measured Validation</div>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
          Compares replay or optimization projections against measured before/after runs. These records are local evidence, not broad benchmark generalization.
        </p>
        {summary.measured_validation.length ? (
          <div className="mt-4 grid gap-3">
            {summary.measured_validation.map((experiment) => (
              <div key={experiment.experiment_id ?? experiment.scenario_id} className="rounded-md border border-line bg-panel p-4">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="text-xs font-medium uppercase text-muted">{experiment.scenario_id}</div>
                    <div className="mt-1 font-semibold">{experiment.scenario_name}</div>
                  </div>
                  <div className="text-sm font-semibold">
                    Success preserved: {experiment.success_preserved === true ? "Yes" : experiment.success_preserved === false ? "No" : "Unknown"}
                  </div>
                </div>
                <div className="mt-3 grid gap-3 md:grid-cols-4">
                  <MetricCard label="Projected Tokens" value={`${experiment.projected_input_token_reduction_percent ?? 0}%`} />
                  <MetricCard label="Measured Tokens" value={`${experiment.measured_input_token_reduction_percent ?? 0}%`} />
                  <MetricCard label="Measured Cost" value={`${experiment.measured_cost_reduction_percent ?? 0}%`} />
                  <MetricCard label="Projection Error" value={`${experiment.projection_error_percent ?? 0}%`} />
                </div>
                <p className="mt-3 text-sm leading-6 text-muted">{experiment.evidence}</p>
                <p className="mt-2 text-xs leading-5 text-muted">{experiment.notes}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="mt-4 rounded-md border border-line bg-panel p-3 text-sm text-muted">
            No measured validation experiments yet. Add a projected-vs-measured before/after record through the validation API.
          </div>
        )}
      </section>

      <section className="rounded-md border border-line bg-white p-5">
        <div className="font-semibold">Benchmark Suite</div>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
          v0.5 benchmark records for SWE-bench, Aider, OpenHands, and custom coding-agent validation. Imported records are evidence tracking, not automatic benchmark execution.
        </p>
        {summary.benchmark_suite ? (
          <div className="mt-4 grid gap-3 md:grid-cols-4">
            <MetricCard label="Runs" value={`${summary.benchmark_suite.run_count}`} />
            <MetricCard label="Tasks" value={`${summary.benchmark_suite.task_count}`} />
            <MetricCard label="Trace Completion" value={`${summary.benchmark_suite.trace_completion_rate_percent}%`} />
            <MetricCard
              label="Task Success"
              value={summary.benchmark_suite.task_success_rate_percent == null ? "Unknown" : `${summary.benchmark_suite.task_success_rate_percent}%`}
            />
          </div>
        ) : (
          <div className="mt-4 rounded-md border border-line bg-panel p-3 text-sm text-muted">
            No benchmark suite summary is available.
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
