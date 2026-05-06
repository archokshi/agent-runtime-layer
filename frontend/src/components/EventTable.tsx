"use client";

import { useMemo, useState } from "react";
import type { TraceEvent } from "@/lib/types";

function stringify(value: unknown) {
  if (value === null || value === undefined) return "";
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

function preview(event: TraceEvent) {
  const attrs = event.attributes ?? {};
  const payload = event.payload ?? {};
  const pieces = [
    attrs.tool_name,
    attrs.command,
    attrs.model,
    attrs.role,
    attrs.context_kind,
    attrs.status,
    payload.summary,
    payload.stderr_preview,
    payload.stdout_preview,
    payload.preview,
  ].filter(Boolean);
  return pieces.length ? pieces.map(String).join(" | ") : "No preview";
}

function pretty(value: unknown) {
  return JSON.stringify(value ?? {}, null, 2);
}

export function EventTable({ events }: { events: TraceEvent[] }) {
  const [query, setQuery] = useState("");
  const [type, setType] = useState("all");
  const [expanded, setExpanded] = useState<string | null>(null);
  const types = useMemo(() => Array.from(new Set(events.map((event) => event.event_type))).sort(), [events]);
  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return events.filter((event) => {
      if (type !== "all" && event.event_type !== type) return false;
      if (!normalized) return true;
      const haystack = [
        event.timestamp,
        event.event_type,
        event.name,
        event.span_id,
        event.parent_span_id,
        stringify(event.attributes),
        stringify(event.payload),
      ].join(" ").toLowerCase();
      return haystack.includes(normalized);
    });
  }, [events, query, type]);

  return (
    <section className="rounded-lg border border-line bg-white p-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Event Inspector</h2>
          <p className="mt-1 text-sm text-slate-600">Search, filter, and expand trace events to inspect attributes and payload.</p>
        </div>
        <div className="text-sm text-slate-600">{filtered.length} of {events.length} events</div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-[1fr_220px]">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search event name, span, command, model, payload..."
          className="h-10 rounded-md border border-line px-3 text-sm outline-none focus:border-teal-700"
        />
        <select
          value={type}
          onChange={(event) => setType(event.target.value)}
          className="h-10 rounded-md border border-line px-3 text-sm outline-none focus:border-teal-700"
        >
          <option value="all">All event types</option>
          {types.map((item) => (
            <option key={item} value={item}>{item}</option>
          ))}
        </select>
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[980px] text-left text-sm">
          <thead className="border-b border-line text-xs uppercase text-slate-500">
            <tr>
              <th className="py-2 pr-4">Time</th>
              <th className="py-2 pr-4">Type</th>
              <th className="py-2 pr-4">Name</th>
              <th className="py-2 pr-4">Span</th>
              <th className="py-2 pr-4">Preview</th>
              <th className="py-2 pr-4">Details</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((event) => {
              const isExpanded = expanded === event.event_id;
              return (
                <tr key={event.event_id} className="border-b border-line align-top last:border-0">
                  <td className="py-3 pr-4 text-xs text-slate-500">{event.timestamp}</td>
                  <td className="py-3 pr-4">
                    <span className="rounded-full border border-line bg-panel px-2 py-1 text-xs font-medium">{event.event_type}</span>
                  </td>
                  <td className="py-3 pr-4 font-medium">{event.name}</td>
                  <td className="py-3 pr-4 text-xs text-slate-500">
                    <div>{event.span_id}</div>
                    {event.parent_span_id ? <div className="mt-1">parent {event.parent_span_id}</div> : null}
                  </td>
                  <td className="max-w-[360px] py-3 pr-4 text-sm text-slate-600">{preview(event)}</td>
                  <td className="py-3 pr-4">
                    <button
                      type="button"
                      onClick={() => setExpanded(isExpanded ? null : event.event_id)}
                      className="rounded-md border border-line bg-white px-2 py-1 text-xs font-semibold hover:bg-panel"
                    >
                      {isExpanded ? "Hide" : "Inspect"}
                    </button>
                    {isExpanded ? (
                      <div className="mt-3 grid gap-2">
                        <div>
                          <div className="text-xs font-semibold uppercase text-slate-500">Attributes</div>
                          <pre className="mt-1 max-h-48 overflow-auto rounded-md border border-line bg-panel p-2 text-xs">{pretty(event.attributes)}</pre>
                        </div>
                        <div>
                          <div className="text-xs font-semibold uppercase text-slate-500">Payload</div>
                          <pre className="mt-1 max-h-48 overflow-auto rounded-md border border-line bg-panel p-2 text-xs">{pretty(event.payload)}</pre>
                        </div>
                      </div>
                    ) : null}
                  </td>
                </tr>
              );
            })}
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-6 text-center text-sm text-slate-600">No events match the current filter.</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
