"use client";

import { useState } from "react";
import { browserBaseUrl } from "@/lib/api";
import type { BackendAwareReport } from "@/lib/types";

function percent(value: number) {
  return `${value.toFixed(1)}%`;
}

function confidence(value: number) {
  return `${Math.round(value * 100)}%`;
}

export function BackendAwareRuntimeReport({
  taskId,
  initialReport
}: {
  taskId: string;
  initialReport: BackendAwareReport | null;
}) {
  const [report, setReport] = useState<BackendAwareReport | null>(initialReport);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generateHints() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${browserBaseUrl}/tasks/${taskId}/backend-hints`, { method: "POST" });
      if (!response.ok) {
        throw new Error(`Backend hints failed: ${response.status}`);
      }
      setReport(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Backend hints failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-line bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Backend-Aware Runtime</h2>
          <p className="mt-1 text-sm text-slate-600">Generate backend-agnostic cache and routing hints. No real vLLM, SGLang, LMCache, Dynamo, or production load balancing is invoked.</p>
        </div>
        <button
          type="button"
          onClick={generateHints}
          disabled={loading}
          className="rounded border border-line bg-panel px-3 py-2 text-sm font-medium hover:bg-white disabled:opacity-60"
        >
          {loading ? "Generating..." : "Generate Backend Hints"}
        </button>
      </div>
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      {report ? (
        <div className="mt-4 grid gap-4">
          <div className="grid gap-3 md:grid-cols-4">
            <div className="rounded-lg border border-line bg-panel p-3">
              <p className="text-xs font-medium uppercase text-slate-500">Prefix Overlap</p>
              <p className="mt-2 text-lg font-semibold">{percent(report.metrics.prefix_overlap_estimate_percent)}</p>
              <p className="mt-1 text-xs text-slate-600">cache locality {report.metrics.cache_locality}</p>
            </div>
            <div className="rounded-lg border border-line bg-panel p-3">
              <p className="text-xs font-medium uppercase text-slate-500">Prefill/Decode</p>
              <p className="mt-2 text-lg font-semibold">{report.metrics.prefill_decode_classification}</p>
              <p className="mt-1 text-xs text-slate-600">{report.metrics.total_input_tokens.toLocaleString()} in, {report.metrics.total_output_tokens.toLocaleString()} out</p>
            </div>
            <div className="rounded-lg border border-line bg-panel p-3">
              <p className="text-xs font-medium uppercase text-slate-500">Model Calls</p>
              <p className="mt-2 text-lg font-semibold">{report.metrics.model_call_count}</p>
              <p className="mt-1 text-xs text-slate-600">queue depth {report.metrics.queue_depth_observed}</p>
            </div>
            <div className="rounded-lg border border-line bg-panel p-3">
              <p className="text-xs font-medium uppercase text-slate-500">Backends</p>
              <p className="mt-2 text-lg font-semibold">{report.backend_registry.length}</p>
              <p className="mt-1 text-xs text-slate-600">hint targets only</p>
            </div>
          </div>
          <div className="grid gap-3">
            {report.routing_hints.map((hint) => (
              <div key={hint.hint_id} className="rounded-lg border border-line bg-panel p-3">
                <div className="flex flex-wrap justify-between gap-2">
                  <div>
                    <p className="text-xs font-medium uppercase text-slate-500">{hint.category}</p>
                    <h3 className="mt-1 font-semibold">{hint.title}</h3>
                  </div>
                  <p className="text-xs font-semibold">Confidence {confidence(hint.confidence)}</p>
                </div>
                <p className="mt-2 text-sm text-slate-600">{hint.rationale}</p>
                <p className="mt-2 text-sm">{hint.action}</p>
                <p className="mt-2 text-xs text-slate-600">Target {hint.target_backend_id ?? "none"}</p>
              </div>
            ))}
          </div>
          <div className="rounded-lg border border-line bg-panel p-3">
            <h3 className="font-semibold">Model Call Profiles</h3>
            <div className="mt-3 grid gap-2">
              {report.model_call_profiles.map((profile) => (
                <div key={profile.span_id} className="rounded border border-line bg-white p-2 text-sm">
                  <p className="font-medium">{profile.role || "model"} - {profile.prefill_decode_classification}</p>
                  <p className="text-xs text-slate-600">{profile.input_tokens.toLocaleString()} in, {profile.output_tokens.toLocaleString()} out, prefix overlap {percent(profile.prefix_overlap_percent)}, locality {profile.cache_locality}</p>
                </div>
              ))}
            </div>
          </div>
          <p className="text-xs text-slate-600">{report.notes}</p>
        </div>
      ) : null}
    </section>
  );
}
