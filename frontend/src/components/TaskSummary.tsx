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

function titleize(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function captureSourceLabel(events: TraceEvent[]) {
  const source = events
    .map((event) => event.attributes?.capture_source)
    .find((value): value is string => typeof value === "string" && value.length > 0);
  if (!source) return null;
  if (source === "codex_session_jsonl") return "Codex session JSONL";
  if (source === "codex_hook") return "Codex hooks";
  return titleize(source);
}

export function TaskSummary({ task, events, analysis }: { task: Task; events: TraceEvent[]; analysis: AnalysisReport }) {
  const captureSource = captureSourceLabel(events);
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
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="rounded-full border border-line bg-white px-3 py-1 text-xs font-medium text-slate-600">
            Agent: {titleize(task.agent_type)}
          </span>
          {captureSource ? (
            <span className="rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-medium text-teal-800">
              Source: {captureSource}
            </span>
          ) : null}
        </div>
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
