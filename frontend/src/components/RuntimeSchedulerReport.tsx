"use client";

import { useState } from "react";
import { browserBaseUrl } from "@/lib/api";
import type { SchedulerReport } from "@/lib/types";

function seconds(value: number) {
  return `${(value / 1000).toFixed(1)}s`;
}

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

export function RuntimeSchedulerReport({
  taskId,
  initialReport
}: {
  taskId: string;
  initialReport: SchedulerReport | null;
}) {
  const [report, setReport] = useState<SchedulerReport | null>(initialReport);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runScheduler() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${browserBaseUrl}/tasks/${taskId}/schedule`, { method: "POST" });
      if (!response.ok) {
        throw new Error(`Scheduler failed: ${response.status}`);
      }
      setReport(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Scheduler failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-line bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Runtime Scheduler</h2>
          <p className="mt-1 text-sm text-slate-600">Run a local deterministic scheduler simulation. It estimates scheduling decisions; it does not execute a production scheduler.</p>
        </div>
        <button
          type="button"
          onClick={runScheduler}
          disabled={loading}
          className="rounded border border-line bg-panel px-3 py-2 text-sm font-medium hover:bg-white disabled:opacity-60"
        >
          {loading ? "Scheduling..." : "Run Scheduler Tick"}
        </button>
      </div>
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      {report ? (
        <div className="mt-4 grid gap-4">
          <div className="grid gap-3 md:grid-cols-4">
            <div className="rounded-lg border border-line bg-panel p-3">
              <p className="text-xs font-medium uppercase text-slate-500">Duration</p>
              <p className="mt-2 text-lg font-semibold">{seconds(report.metrics.naive_duration_ms)} {"->"} {seconds(report.metrics.scheduled_estimated_duration_ms)}</p>
              <p className="mt-1 text-xs text-slate-600">{seconds(report.metrics.estimated_time_savings_ms)} estimated savings</p>
            </div>
            <div className="rounded-lg border border-line bg-panel p-3">
              <p className="text-xs font-medium uppercase text-slate-500">Idle Reduction</p>
              <p className="mt-2 text-lg font-semibold">{seconds(report.metrics.idle_reduction_ms)}</p>
              <p className="mt-1 text-xs text-slate-600">{seconds(report.metrics.idle_ms)} idle observed</p>
            </div>
            <div className="rounded-lg border border-line bg-panel p-3">
              <p className="text-xs font-medium uppercase text-slate-500">Throughput</p>
              <p className="mt-2 text-lg font-semibold">{report.metrics.naive_tasks_per_hour} {"->"} {report.metrics.scheduled_tasks_per_hour}/hr</p>
              <p className="mt-1 text-xs text-slate-600">simulated tasks per hour</p>
            </div>
            <div className="rounded-lg border border-line bg-panel p-3">
              <p className="text-xs font-medium uppercase text-slate-500">Guards</p>
              <p className="mt-2 text-lg font-semibold">{report.metrics.slo_status}</p>
              <p className="mt-1 text-xs text-slate-600">budget {report.metrics.budget_status}, priority {report.task_priority}</p>
            </div>
          </div>
          <div className="grid gap-3">
            {report.decisions.length === 0 ? (
              <p className="rounded-lg border border-line bg-panel p-3 text-sm text-slate-600">No scheduler action needed for this trace.</p>
            ) : null}
            {report.decisions.map((decision) => (
              <div key={decision.decision_id} className="rounded-lg border border-line bg-panel p-3">
                <div className="flex flex-wrap justify-between gap-2">
                  <div>
                    <p className="text-xs font-medium uppercase text-slate-500">{decision.category}</p>
                    <h3 className="mt-1 font-semibold">{decision.title}</h3>
                  </div>
                  <p className="text-xs font-semibold">Confidence {percent(decision.confidence)}</p>
                </div>
                <p className="mt-2 text-sm text-slate-600">{decision.rationale}</p>
                <p className="mt-2 text-sm">{decision.action}</p>
                <p className="mt-2 text-xs text-slate-600">Priority {decision.priority}, time {seconds(decision.estimated_time_savings_ms)}, idle {seconds(decision.estimated_idle_reduction_ms)}</p>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-600">{report.notes}</p>
        </div>
      ) : null}
    </section>
  );
}
