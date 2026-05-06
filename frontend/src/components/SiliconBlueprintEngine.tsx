"use client";

import { useState } from "react";
import { Cpu, Download, FastForward, Layers, Network, Play, Route, ShieldAlert } from "lucide-react";
import { browserBaseUrl } from "@/lib/api";
import type { SiliconBlueprintReport, TraceReplayReport, TraceReplayScenarioId } from "@/lib/types";

const scenarioOptions: { id: TraceReplayScenarioId; label: string }[] = [
  { id: "persistent_prefix_cache", label: "Persistent prefix cache" },
  { id: "tool_wait_scheduler", label: "Tool-wait scheduler" },
  { id: "prefill_decode_split", label: "Prefill/decode split" },
  { id: "warm_context_tier", label: "Warm context tier" },
  { id: "kv_compression", label: "KV/context compression" },
];

function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
}

function MetricCard({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <div className="rounded-md border border-line bg-white p-4">
      <div className="text-xs font-medium uppercase text-muted">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
      {detail ? <div className="mt-1 text-sm text-muted">{detail}</div> : null}
    </div>
  );
}

function RecommendationCard({
  title,
  subtitle,
  confidence,
  body,
}: {
  title: string;
  subtitle: string;
  confidence?: number;
  body: string;
}) {
  return (
    <div className="rounded-md border border-line bg-panel p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xs font-medium uppercase text-muted">{subtitle}</div>
          <div className="mt-1 font-semibold">{title}</div>
        </div>
        {typeof confidence === "number" ? (
          <div className="shrink-0 text-xs font-semibold">Confidence {Math.round(confidence * 100)}%</div>
        ) : null}
      </div>
      <p className="mt-2 text-sm leading-6 text-muted">{body}</p>
    </div>
  );
}

export function SiliconBlueprintEngine({
  initialReports,
  initialReplayReports,
}: {
  initialReports: SiliconBlueprintReport[];
  initialReplayReports: TraceReplayReport[];
}) {
  const [reports, setReports] = useState(initialReports);
  const [replayReports, setReplayReports] = useState(initialReplayReports);
  const [selectedScenarios, setSelectedScenarios] = useState<TraceReplayScenarioId[]>(scenarioOptions.map((scenario) => scenario.id));
  const [loading, setLoading] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const latest = reports[0] ?? null;
  const latestReplay = replayReports[0] ?? null;

  async function generateReport() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${browserBaseUrl}/blueprints/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "Local Agent Silicon Blueprint" }),
      });
      if (!response.ok) {
        throw new Error(`Generate failed: ${response.status}`);
      }
      const report = (await response.json()) as SiliconBlueprintReport;
      setReports([report, ...reports.filter((item) => item.blueprint_id !== report.blueprint_id)]);
      setReplayReports([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to generate blueprint");
    } finally {
      setLoading(false);
    }
  }

  async function runTraceReplay() {
    if (!latest) {
      return;
    }
    setSimulating(true);
    setError(null);
    try {
      const response = await fetch(`${browserBaseUrl}/blueprints/${latest.blueprint_id}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_ids: selectedScenarios }),
      });
      if (!response.ok) {
        throw new Error(`Trace replay failed: ${response.status}`);
      }
      const report = (await response.json()) as TraceReplayReport;
      setReplayReports([report, ...replayReports.filter((item) => item.replay_id !== report.replay_id)]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run trace replay");
    } finally {
      setSimulating(false);
    }
  }

  function toggleScenario(id: TraceReplayScenarioId) {
    setSelectedScenarios((current) => {
      if (current.includes(id)) {
        return current.length === 1 ? current : current.filter((item) => item !== id);
      }
      return [...current, id];
    });
  }

  return (
    <div className="grid gap-5">
      <section className="rounded-md border border-line bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-sm font-medium text-teal-700">v3.5 architecture report</div>
            <h1 className="mt-1 text-3xl font-semibold">Silicon Blueprint Engine</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
              Generates a rule-based architecture report from imported agent traces and hardware telemetry. This is a blueprint report, not ASIC design, RTL, FPGA work, or hardware simulation.
            </p>
          </div>
          <button
            type="button"
            onClick={generateReport}
            disabled={loading}
            className="inline-flex h-10 items-center gap-2 rounded-md border border-line px-4 text-sm font-medium hover:bg-panel disabled:opacity-60"
          >
            <Play size={16} aria-hidden />
            {loading ? "Generating..." : "Generate Blueprint"}
          </button>
        </div>
        {error ? <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</div> : null}
      </section>

      {latest ? (
        <>
          <section className="grid gap-3 md:grid-cols-4">
            <MetricCard label="Tasks" value={formatNumber(latest.workload_profile.task_count)} detail={`${latest.workload_profile.model_call_count} model calls`} />
            <MetricCard label="Input Tokens" value={formatNumber(latest.workload_profile.total_input_tokens)} detail={`${formatNumber(latest.workload_profile.total_output_tokens)} output`} />
            <MetricCard label="Repeated Context" value={`${latest.workload_profile.avg_repeated_context_percent.toFixed(1)}%`} detail={`${latest.workload_profile.avg_cache_reuse_opportunity_percent.toFixed(1)}% cache opportunity`} />
            <MetricCard label="Cost" value={`$${latest.workload_profile.total_cost_dollars.toFixed(5)}`} detail={latest.blueprint_version} />
          </section>

          <section className="rounded-md border border-line bg-white p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="font-semibold">Validation Coverage</div>
                <p className="mt-2 text-sm leading-6 text-muted">
                  Local corpus coverage is {latest.validation_summary.local_trace_count} of {latest.validation_summary.target_trace_count} target traces, with {latest.validation_summary.tasks_with_hardware_telemetry} task(s) carrying imported hardware telemetry. Status: {latest.validation_summary.real_world_validation_status.replaceAll("_", " ")}.
                </p>
              </div>
              <a
                href={`${browserBaseUrl}/blueprints/${latest.blueprint_id}/export.md`}
                className="inline-flex h-10 items-center gap-2 rounded-md border border-line px-4 text-sm font-medium hover:bg-panel"
              >
                <Download size={16} aria-hidden />
                Export Markdown
              </a>
            </div>
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-panel">
              <div
                className="h-full bg-teal-700"
                style={{ width: `${Math.min(100, latest.validation_summary.target_progress_percent)}%` }}
                aria-hidden
              />
            </div>
            <div className="mt-3 grid gap-2">
              {latest.validation_summary.remaining_validation_items.map((item) => (
                <div key={item} className="rounded-md border border-line bg-panel p-3 text-sm text-muted">{item}</div>
              ))}
            </div>
          </section>

          <section className="rounded-md border border-line bg-white p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 font-semibold">
                  <FastForward size={18} aria-hidden />
                  Trace Replay Simulator
                </div>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
                  v4.5 replays this blueprint's trace set through selected what-if scenarios. These are rule-based projections, not measured backend or hardware speedups.
                </p>
              </div>
              <button
                type="button"
                onClick={runTraceReplay}
                disabled={simulating}
                className="inline-flex h-10 items-center gap-2 rounded-md border border-line px-4 text-sm font-medium hover:bg-panel disabled:opacity-60"
              >
                <Play size={16} aria-hidden />
                {simulating ? "Simulating..." : "Run Replay"}
              </button>
            </div>
            <div className="mt-4 grid gap-2 md:grid-cols-5">
              {scenarioOptions.map((scenario) => (
                <label key={scenario.id} className="flex min-h-12 items-center gap-2 rounded-md border border-line bg-panel px-3 py-2 text-sm">
                  <input
                    type="checkbox"
                    checked={selectedScenarios.includes(scenario.id)}
                    onChange={() => toggleScenario(scenario.id)}
                    className="size-4"
                  />
                  <span>{scenario.label}</span>
                </label>
              ))}
            </div>
            {latestReplay ? (
              <div className="mt-4 grid gap-3">
                <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-muted">
                  <div>
                    Replay {latestReplay.replay_id} · {latestReplay.simulator_version} · best scenario {latestReplay.best_scenario_id?.replaceAll("_", " ") ?? "none"}
                  </div>
                  <a
                    href={`${browserBaseUrl}/replays/${latestReplay.replay_id}/export.md`}
                    className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-white"
                  >
                    <Download size={15} aria-hidden />
                    Export Replay
                  </a>
                </div>
                <div className="grid gap-3 md:grid-cols-3">
                  <MetricCard label="Best Duration" value={`${Number(latestReplay.comparison_summary.best_duration_reduction_percent ?? 0).toFixed(1)}%`} detail={String(latestReplay.comparison_summary.best_duration_scenario_id ?? "none").replaceAll("_", " ")} />
                  <MetricCard label="Best Cost" value={`${Number(latestReplay.comparison_summary.best_cost_reduction_percent ?? 0).toFixed(1)}%`} detail={String(latestReplay.comparison_summary.best_cost_scenario_id ?? "none").replaceAll("_", " ")} />
                  <MetricCard label="Best Prefill" value={`${Number(latestReplay.comparison_summary.best_prefill_reduction_percent ?? 0).toFixed(1)}%`} detail={String(latestReplay.comparison_summary.best_prefill_scenario_id ?? "none").replaceAll("_", " ")} />
                </div>
                <div className="grid gap-3 lg:grid-cols-3">
                  {latestReplay.scenario_results.map((scenario) => (
                    <div key={scenario.scenario_id} className="rounded-md border border-line bg-panel p-4">
                      <div className="text-xs font-medium uppercase text-muted">{scenario.scenario_id.replaceAll("_", " ")}</div>
                      <div className="mt-1 font-semibold">{scenario.name}</div>
                      <p className="mt-2 text-sm leading-6 text-muted">{scenario.description}</p>
                      <div className="mt-3 grid gap-2 text-sm">
                        <div>Duration reduction: <span className="font-semibold">{scenario.delta.duration_reduction_percent.toFixed(1)}%</span></div>
                        <div>Input token reduction: <span className="font-semibold">{scenario.delta.input_token_reduction_percent.toFixed(1)}%</span></div>
                        <div>Cost reduction: <span className="font-semibold">{scenario.delta.estimated_cost_reduction_percent.toFixed(1)}%</span></div>
                        <div>Prefill reduction: <span className="font-semibold">{scenario.delta.estimated_prefill_reduction_percent.toFixed(1)}%</span></div>
                        <div>Confidence: <span className="font-semibold">{Math.round(scenario.confidence * 100)}%</span></div>
                      </div>
                      <p className="mt-3 text-xs leading-5 text-muted">{scenario.projection_confidence_reason}</p>
                      <div className="mt-3 text-xs font-semibold">Validation evidence needed</div>
                      <ul className="mt-1 grid gap-1 text-xs leading-5 text-muted">
                        {scenario.validation_evidence_needed.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                      <p className="mt-3 text-xs leading-5 text-muted">{scenario.notes}</p>
                    </div>
                  ))}
                </div>
                <div className="grid gap-2">
                  {latestReplay.limitations.map((limit) => (
                    <div key={limit} className="rounded-md border border-line bg-panel p-3 text-sm text-muted">{limit}</div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="mt-4 rounded-md border border-line bg-panel p-3 text-sm text-muted">
                No replay report yet. Run Replay to project persistent prefix cache, tool-wait scheduler, and prefill/decode split scenarios.
              </div>
            )}
          </section>

          <section className="rounded-md border border-line bg-white p-5">
            <div className="mb-4 flex items-center gap-2 font-semibold">
              <Network size={18} aria-hidden />
              Bottleneck Map
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              {Object.entries(latest.bottleneck_map).map(([category, count]) => (
                <div key={category} className="rounded-md border border-line bg-panel p-3">
                  <div className="text-sm font-semibold">{category.replaceAll("_", " ")}</div>
                  <div className="mt-1 text-2xl font-semibold">{count}</div>
                </div>
              ))}
            </div>
          </section>

          <section className="grid gap-5 lg:grid-cols-2">
            <div className="rounded-md border border-line bg-white p-5">
              <div className="mb-4 flex items-center gap-2 font-semibold">
                <Layers size={18} aria-hidden />
                Memory Hierarchy
              </div>
              <div className="grid gap-3">
                {latest.memory_hierarchy_recommendations.map((rec) => (
                  <RecommendationCard key={rec.recommendation_id} title={rec.title} subtitle={rec.priority} confidence={rec.confidence} body={rec.rationale} />
                ))}
              </div>
            </div>

            <div className="rounded-md border border-line bg-white p-5">
              <div className="mb-4 flex items-center gap-2 font-semibold">
                <Cpu size={18} aria-hidden />
                Hardware Primitive Ranking
              </div>
              <div className="grid gap-3">
                {latest.hardware_primitive_rankings.map((primitive, index) => (
                  <div key={primitive.primitive} className="rounded-md border border-line bg-panel p-3">
                    <div className="flex items-center justify-between gap-4">
                      <div className="font-semibold">{index + 1}. {primitive.primitive.replaceAll("_", " ")}</div>
                      <div className="text-sm font-semibold">{primitive.score.toFixed(1)}</div>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-muted">{primitive.rationale}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="grid gap-5 lg:grid-cols-2">
            <div className="rounded-md border border-line bg-white p-5">
              <div className="mb-4 flex items-center gap-2 font-semibold">
                <Route size={18} aria-hidden />
                Backend And Runtime Recommendations
              </div>
              <div className="grid gap-3">
                {latest.backend_runtime_recommendations.map((rec) => (
                  <RecommendationCard key={rec.recommendation_id} title={rec.title} subtitle={rec.priority} confidence={rec.confidence} body={rec.rationale} />
                ))}
              </div>
            </div>

            <div className="rounded-md border border-line bg-white p-5">
              <div className="mb-4 flex items-center gap-2 font-semibold">
                <ShieldAlert size={18} aria-hidden />
                Benchmark Proposals And Limits
              </div>
              <div className="grid gap-3">
                {latest.benchmark_proposals.map((rec) => (
                  <RecommendationCard key={rec.recommendation_id} title={rec.title} subtitle={rec.priority} confidence={rec.confidence} body={rec.rationale} />
                ))}
                {latest.limitations.map((limit) => (
                  <div key={limit} className="rounded-md border border-line bg-panel p-3 text-sm text-muted">{limit}</div>
                ))}
              </div>
            </div>
          </section>
        </>
      ) : (
        <section className="rounded-md border border-line bg-white p-5 text-sm text-muted">
          No Silicon Blueprint reports yet. Import traces, optionally import telemetry, then generate a report.
        </section>
      )}
    </div>
  );
}
