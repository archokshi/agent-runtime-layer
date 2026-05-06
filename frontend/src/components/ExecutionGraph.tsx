"use client";

import { useMemo, useState } from "react";
import { Background, Controls, ReactFlow, type Edge, type Node } from "@xyflow/react";
import type { TraceEvent } from "@/lib/types";

const visibleTypes = new Set([
  "task_start",
  "model_call_start",
  "tool_call_start",
  "context_snapshot",
  "file_event",
  "terminal_event",
  "error_event",
  "cache_event",
]);

function labelFor(event: TraceEvent) {
  return `${event.event_type}\n${event.name}`;
}

function nodeClass(event: TraceEvent) {
  if (event.event_type.includes("model")) return "model";
  if (event.event_type.includes("tool") || event.event_type.includes("terminal")) return "tool";
  if (event.event_type.includes("context") || event.event_type.includes("cache")) return "context";
  if (event.event_type.includes("file")) return "file";
  return "default";
}

function buildDepth(spanId: string, parentBySpan: Map<string, string | null>, memo: Map<string, number>): number {
  if (memo.has(spanId)) return memo.get(spanId)!;
  const parent = parentBySpan.get(spanId);
  if (!parent || parent === spanId || !parentBySpan.has(parent)) {
    memo.set(spanId, 0);
    return 0;
  }
  const depth = buildDepth(parent, parentBySpan, memo) + 1;
  memo.set(spanId, depth);
  return depth;
}

export function ExecutionGraph({ events }: { events: TraceEvent[] }) {
  const [selected, setSelected] = useState<TraceEvent | null>(null);
  const graph = useMemo(() => {
    const visible = events.filter((event) => visibleTypes.has(event.event_type));
    const firstEventBySpan = new Map<string, TraceEvent>();
    const parentBySpan = new Map<string, string | null>();

    for (const event of visible) {
      if (!firstEventBySpan.has(event.span_id)) {
        firstEventBySpan.set(event.span_id, event);
        parentBySpan.set(event.span_id, event.parent_span_id ?? null);
      }
    }

    const depthMemo = new Map<string, number>();
    const depthCounts = new Map<number, number>();
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    for (const event of visible) {
      const depth = buildDepth(event.span_id, parentBySpan, depthMemo);
      const indexAtDepth = depthCounts.get(depth) ?? 0;
      depthCounts.set(depth, indexAtDepth + 1);
      nodes.push({
        id: event.event_id,
        position: { x: depth * 260, y: indexAtDepth * 115 },
        data: { label: labelFor(event) },
        className: nodeClass(event),
      });
    }

    const nodeBySpan = new Map<string, string>();
    for (const event of visible) {
      if (!nodeBySpan.has(event.span_id)) {
        nodeBySpan.set(event.span_id, event.event_id);
      }
    }

    for (const event of visible) {
      const parentId = event.parent_span_id ? nodeBySpan.get(event.parent_span_id) : null;
      if (parentId && parentId !== event.event_id) {
        edges.push({
          id: `parent-${parentId}-${event.event_id}`,
          source: parentId,
          target: event.event_id,
          label: "span",
        });
      }
    }

    const byTimestamp = [...visible].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
    for (let index = 1; index < byTimestamp.length; index += 1) {
      const previous = byTimestamp[index - 1];
      const current = byTimestamp[index];
      const edgeId = `time-${previous.event_id}-${current.event_id}`;
      const existing = edges.some((edge) => edge.source === previous.event_id && edge.target === current.event_id);
      if (!existing) {
        edges.push({
          id: edgeId,
          source: previous.event_id,
          target: current.event_id,
          type: "smoothstep",
          style: { strokeDasharray: "4 4", stroke: "#94a3b8" },
          label: "time",
        });
      }
    }

    return { nodes, edges };
  }, [events]);

  return (
    <section className="rounded-lg border border-line bg-white p-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Execution Graph</h2>
          <p className="mt-1 text-sm text-slate-600">Solid edges show parent span relationships. Dashed edges show event order.</p>
        </div>
        <div className="text-sm text-slate-600">{graph.nodes.length} nodes, {graph.edges.length} edges</div>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="h-[460px] rounded-lg border border-line">
          <ReactFlow nodes={graph.nodes} edges={graph.edges} fitView onNodeClick={(_, node) => setSelected(events.find((event) => event.event_id === node.id) ?? null)}>
            <Background />
            <Controls />
          </ReactFlow>
        </div>
        <div className="rounded-lg border border-line bg-panel p-3">
          <h3 className="text-sm font-semibold">Event Details</h3>
          {selected ? (
            <div className="mt-3 grid gap-3 text-sm">
              <div>
                <div className="text-xs font-semibold uppercase text-slate-500">Event</div>
                <div className="mt-1 font-semibold">{selected.name}</div>
                <div className="text-xs text-slate-600">{selected.event_type}</div>
              </div>
              <div>
                <div className="text-xs font-semibold uppercase text-slate-500">Span</div>
                <div className="mt-1 break-all text-xs">{selected.span_id}</div>
                {selected.parent_span_id ? <div className="mt-1 break-all text-xs text-slate-600">parent {selected.parent_span_id}</div> : null}
              </div>
              <pre className="max-h-[290px] overflow-auto whitespace-pre-wrap rounded-md border border-line bg-white p-2 text-xs">{JSON.stringify(selected, null, 2)}</pre>
            </div>
          ) : (
            <p className="mt-3 text-sm text-slate-600">Select a node to inspect its stored event.</p>
          )}
        </div>
      </div>
    </section>
  );
}
