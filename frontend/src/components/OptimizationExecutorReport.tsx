"use client";

import { useState } from "react";
import { browserBaseUrl } from "@/lib/api";
import type { ContextOptimizationReport } from "@/lib/types";

function dollars(value: number) {
  if (value > 0 && value < 0.01) return `$${value.toFixed(5)}`;
  return `$${value.toFixed(3)}`;
}

function percent(value: number) {
  return `${value.toFixed(1)}%`;
}

export function OptimizationExecutorReport({
  taskId,
  initialReport
}: {
  taskId: string;
  initialReport: ContextOptimizationReport | null;
}) {
  const [report, setReport] = useState<ContextOptimizationReport | null>(initialReport);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runOptimizer() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${browserBaseUrl}/tasks/${taskId}/optimize-context`, {
        method: "POST"
      });
      if (!response.ok) {
        throw new Error(`Optimizer failed: ${response.status}`);
      }
      setReport(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Optimizer failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-line bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">Optimization Executor</h2>
          <p className="mt-1 text-sm text-slate-600">Generate a prefix-cache-ready context package from repeated trace context. Estimates only; no backend KV-cache hit is measured.</p>
        </div>
        <button
          type="button"
          onClick={runOptimizer}
          disabled={loading}
          className="rounded border border-line bg-panel px-3 py-2 text-sm font-medium hover:bg-white disabled:opacity-60"
        >
          {loading ? "Optimizing..." : "Run Optimize Context"}
        </button>
      </div>
      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
      {report ? (
        <div className="mt-4 grid gap-4">
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-lg border border-line bg-panel p-3">
              <p className="text-xs font-medium uppercase text-slate-500">Input Tokens</p>
              <p className="mt-2 text-lg font-semibold">{report.baseline.input_tokens.toLocaleString()} {"->"} {report.optimized.input_tokens.toLocaleString()}</p>
              <p className="mt-1 text-xs text-slate-600">{percent(report.savings.input_token_reduction_percent)} reduction</p>
            </div>
            <div className="rounded-lg border border-line bg-panel p-3">
              <p className="text-xs font-medium uppercase text-slate-500">Estimated Cost</p>
              <p className="mt-2 text-lg font-semibold">{dollars(report.baseline.estimated_cost)} {"->"} {dollars(report.optimized.estimated_cost)}</p>
              <p className="mt-1 text-xs text-slate-600">{percent(report.savings.estimated_cost_reduction_percent)} reduction</p>
            </div>
            <div className="rounded-lg border border-line bg-panel p-3">
              <p className="text-xs font-medium uppercase text-slate-500">Prefill Opportunity</p>
              <p className="mt-2 text-lg font-semibold">{percent(report.savings.estimated_prefill_reduction_percent)}</p>
              <p className="mt-1 text-xs text-slate-600">Prefix-cache-ready, not measured KV hits.</p>
            </div>
          </div>
          <div className="grid gap-3 lg:grid-cols-2">
            <div className="rounded-lg border border-line bg-panel p-3">
              <h3 className="font-semibold">Stable Context Blocks</h3>
              <div className="mt-3 grid gap-2">
                {report.stable_context_blocks.length === 0 ? <p className="text-sm text-slate-600">No stable blocks detected.</p> : null}
                {report.stable_context_blocks.map((block) => (
                  <div key={block.block_id} className="rounded border border-line bg-white p-2 text-sm">
                    <p className="font-medium">{block.block_id} - {block.type}</p>
                    <p className="text-xs text-slate-600">{block.tokens.toLocaleString()} tokens, {block.occurrences} occurrences, {block.action}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-lg border border-line bg-panel p-3">
              <h3 className="font-semibold">Dynamic Context Blocks</h3>
              <div className="mt-3 grid gap-2">
                {report.dynamic_context_blocks.map((block) => (
                  <div key={block.block_id} className="rounded border border-line bg-white p-2 text-sm">
                    <p className="font-medium">{block.block_id} - {block.type}</p>
                    <p className="text-xs text-slate-600">{block.tokens.toLocaleString()} tokens, {block.action}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="rounded-lg border border-line bg-panel p-3">
            <h3 className="font-semibold">Optimized Prompt Package</h3>
            <p className="mt-2 text-sm text-slate-600">{report.optimized_prompt_package.notes}</p>
            <div className="mt-3 grid gap-2 md:grid-cols-2">
              <p className="rounded border border-line bg-white p-2 text-sm">Stable refs: {report.optimized_prompt_package.stable_prefix_refs.join(", ") || "None"}</p>
              <p className="rounded border border-line bg-white p-2 text-sm">Dynamic refs: {report.optimized_prompt_package.dynamic_payload_refs.join(", ") || "None"}</p>
            </div>
            <p className="mt-3 text-xs text-slate-600">Validation: success preserved {report.validation.task_success_preserved === true ? "yes" : "unknown"}, confidence {report.validation.confidence}. {report.validation.next_validation_step}</p>
          </div>
        </div>
      ) : null}
    </section>
  );
}
