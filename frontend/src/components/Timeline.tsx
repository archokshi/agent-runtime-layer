import type { TraceEvent } from "@/lib/types";

function parseTime(value: string) {
  const time = new Date(value).getTime();
  return Number.isNaN(time) ? 0 : time;
}

function formatOffset(ms: number) {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function eventTone(type: string) {
  if (type.includes("model")) return "bg-teal-700";
  if (type.includes("tool") || type.includes("terminal")) return "bg-amber-600";
  if (type.includes("file")) return "bg-blue-700";
  if (type.includes("context") || type.includes("cache")) return "bg-purple-700";
  if (type.includes("error") || type.includes("failed")) return "bg-red-700";
  return "bg-slate-600";
}

function shortTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export function Timeline({ events }: { events: TraceEvent[] }) {
  const sorted = [...events].sort((a, b) => parseTime(a.timestamp) - parseTime(b.timestamp));
  const first = parseTime(sorted[0]?.timestamp ?? "");
  const last = parseTime(sorted[sorted.length - 1]?.timestamp ?? "");
  const duration = Math.max(last - first, 1);
  const rows = sorted.map((event) => {
    const offset = Math.max(parseTime(event.timestamp) - first, 0);
    return {
      event,
      offset,
      left: Math.min(96, Math.max(0, (offset / duration) * 100)),
    };
  });

  return (
    <section className="rounded-lg border border-line bg-white p-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Event Timeline</h2>
          <p className="mt-1 text-sm text-slate-600">Events plotted by timestamp from task start to task end.</p>
        </div>
        <div className="text-sm font-medium text-slate-600">{formatOffset(duration)} total</div>
      </div>
      <div className="mt-5 grid gap-3">
        {rows.map(({ event, offset, left }) => (
          <div key={event.event_id} className="grid gap-2 md:grid-cols-[8rem_1fr] md:items-center">
            <div className="text-xs text-slate-500">
              <div className="font-medium text-slate-700">{formatOffset(offset)}</div>
              <div>{shortTime(event.timestamp)}</div>
            </div>
            <div>
              <div className="relative h-7 rounded-md border border-line bg-panel">
                <div className="absolute inset-y-0 left-3 right-3">
                  <div className="absolute top-1/2 h-px w-full -translate-y-1/2 bg-line" />
                  <div
                    className={`absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full ${eventTone(event.event_type)}`}
                    style={{ left: `${left}%` }}
                    title={`${event.event_type}: ${event.name}`}
                  />
                </div>
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-sm">
                <span className="font-semibold">{event.name}</span>
                <span className="rounded-full border border-line bg-white px-2 py-0.5 text-xs text-slate-600">{event.event_type}</span>
                <span className="text-xs text-slate-500">{event.span_id}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
