import type { AnalysisReport, Task, TraceEvent } from "@/lib/types";

function seconds(ms: number) {
  return `${(ms / 1000).toFixed(1)}s`;
}

function dollars(value: number) {
  if (value > 0 && value < 0.01) {
    return `$${value.toFixed(5)}`;
  }
  return `$${value.toFixed(3)}`;
}

export function TaskSummary({ task, events, analysis }: { task: Task; events: TraceEvent[]; analysis: AnalysisReport }) {
  const items = [
    ["Duration", seconds(analysis.total_task_duration_ms)],
    ["Events", String(events.length)],
    ["Model Calls", String(analysis.model_call_count)],
    ["Tool Calls", String(analysis.tool_call_count)],
    ["Cost", dollars(analysis.estimated_total_cost_dollars)],
    ["Bottleneck", analysis.bottleneck_category.replaceAll("_", " ")]
  ];

  return (
    <section>
      <div className="mb-4">
        <p className="text-sm text-slate-500">{task.task_id}</p>
        <h1 className="mt-1 text-3xl font-semibold tracking-normal">{task.goal}</h1>
        {task.summary ? <p className="mt-2 max-w-3xl text-sm text-slate-600">{task.summary}</p> : null}
      </div>
      <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        {items.map(([label, value]) => (
          <div key={label} className="rounded-lg border border-line bg-white p-4">
            <p className="text-xs font-medium uppercase text-slate-500">{label}</p>
            <p className="mt-2 text-xl font-semibold capitalize">{value}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
