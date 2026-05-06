"use client";

import { useState } from "react";
import { Download, FileText, Play } from "lucide-react";
import { browserBaseUrl } from "@/lib/api";
import type { Phase1ExitPackage } from "@/lib/types";

function MetricCard({ label, value, detail }: { label: string; value: string; detail?: string | null }) {
  return (
    <div className="rounded-md border border-line bg-white p-4">
      <div className="text-xs font-medium uppercase text-muted">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
      {detail ? <div className="mt-1 text-sm text-muted">{detail}</div> : null}
    </div>
  );
}

function valueToString(value: unknown) {
  if (value === null || value === undefined) {
    return "unknown";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

export function Phase1ExitDashboard({ initialPackages }: { initialPackages: Phase1ExitPackage[] }) {
  const [packages, setPackages] = useState(initialPackages);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const latest = packages[0] ?? null;
  const recommendations = latest?.workload_recommendation_package.prioritized_recommendations ?? [];
  const modelCompute = latest?.workload_evaluation_package.model_compute_profile ?? {};
  const contextProfile = latest?.workload_evaluation_package.context_kv_reuse_profile ?? {};
  const totalEstimatedCost = typeof modelCompute.estimated_cost_dollars === "number" ? modelCompute.estimated_cost_dollars : null;
  const totalInputTokens = typeof modelCompute.input_tokens === "number" ? modelCompute.input_tokens : null;
  const repeatedContextPercent = typeof contextProfile.avg_repeated_context_percent === "number" ? contextProfile.avg_repeated_context_percent : null;
  const estimatedRepeatedCost = totalEstimatedCost !== null && repeatedContextPercent !== null
    ? totalEstimatedCost * (repeatedContextPercent / 100)
    : null;
  const topCostRecommendation = recommendations.find((rec) =>
    `${rec.title} ${rec.evidence} ${rec.action}`.toLowerCase().includes("cost")
    || `${rec.title} ${rec.evidence} ${rec.action}`.toLowerCase().includes("context")
    || `${rec.title} ${rec.evidence} ${rec.action}`.toLowerCase().includes("token")
  ) ?? recommendations[0];

  async function generatePackage() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${browserBaseUrl}/phase-1-exit/generate`, { method: "POST" });
      if (!response.ok) {
        throw new Error(`Generate failed: ${response.status}`);
      }
      const report = (await response.json()) as Phase1ExitPackage;
      setPackages([report, ...packages.filter((item) => item.package_id !== report.package_id)]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to generate Workload Report");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid gap-5">
      <section className="rounded-md border border-line bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="text-sm font-medium text-teal-700">Workload Report</div>
            <h1 className="mt-1 text-3xl font-semibold">Workload Evaluation + Recommendation Report</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
              Summarizes local runtime evidence, prioritized recommendations, metric quality, backend test planning, and architecture signals. It is not hardware simulation, live backend control, or a silicon design.
            </p>
          </div>
          <button
            type="button"
            onClick={generatePackage}
            disabled={loading}
            className="inline-flex h-10 items-center gap-2 rounded-md border border-line px-4 text-sm font-medium hover:bg-panel disabled:opacity-60"
          >
            <Play size={16} aria-hidden />
            {loading ? "Generating..." : "Generate Report"}
          </button>
        </div>
        {error ? <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</div> : null}
      </section>

      {latest ? (
        <>
          <section className="grid gap-3 md:grid-cols-4">
            <MetricCard label="Readiness" value={`${latest.architecture_readiness_score}/100`} detail={latest.architecture_readiness_rationale} />
            <MetricCard label="Metrics" value={`${latest.metric_quality_scorecard.length}`} detail="quality scorecard" />
            <MetricCard label="Recommendations" value={`${recommendations.length}`} detail="prioritized actions" />
            <MetricCard label="Backend Tests" value={`${latest.phase_1_5_hardware_test_plan.length}`} detail="validation plan" />
          </section>

          <section className="rounded-md border border-line bg-white p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
              <div className="font-semibold">Latest Workload Report</div>
                <p className="mt-2 text-sm leading-6 text-muted">
                  {latest.package_id} · {latest.package_version} · {new Date(latest.generated_at).toLocaleString()}
                </p>
              </div>
              <a
                href={`${browserBaseUrl}/phase-1-exit/${latest.package_id}/export.md`}
                className="inline-flex h-10 items-center gap-2 rounded-md border border-line px-4 text-sm font-medium hover:bg-panel"
              >
                <Download size={16} aria-hidden />
                Export Markdown
              </a>
            </div>
          </section>

          <section className="rounded-md border border-line bg-white p-5">
            <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="font-semibold">Cost & Savings</div>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
                  Cost numbers are evidence-aware: model cost is estimated from trace metadata unless a measured validation record is imported.
                </p>
              </div>
              <div className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-800">
                estimated unless measured
              </div>
            </div>
            <div className="grid gap-3 md:grid-cols-4">
              <MetricCard
                label="Total Model Cost"
                value={totalEstimatedCost === null ? "Unknown" : `$${totalEstimatedCost.toFixed(6)}`}
                detail="local workload estimate"
              />
              <MetricCard
                label="Input Tokens"
                value={totalInputTokens === null ? "Unknown" : new Intl.NumberFormat("en-US").format(totalInputTokens)}
                detail="prompt/prefill driver"
              />
              <MetricCard
                label="Repeated Context"
                value={repeatedContextPercent === null ? "Unknown" : `${repeatedContextPercent.toFixed(2)}%`}
                detail="cost reduction opportunity"
              />
              <MetricCard
                label="Repeated Cost Opportunity"
                value={estimatedRepeatedCost === null ? "Unknown" : `$${estimatedRepeatedCost.toFixed(6)}`}
                detail="rough proportional estimate"
              />
            </div>
            {topCostRecommendation ? (
              <div className="mt-4 rounded-md border border-line bg-panel p-4">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <div className="text-xs font-medium uppercase text-muted">Top cost-saving action</div>
                    <div className="mt-1 font-semibold">{topCostRecommendation.title}</div>
                  </div>
                  <div className="text-sm font-semibold">Score {topCostRecommendation.score}</div>
                </div>
                <p className="mt-2 text-sm leading-6 text-muted">{topCostRecommendation.evidence}</p>
                <p className="mt-2 text-sm leading-6">{topCostRecommendation.action}</p>
              </div>
            ) : null}
          </section>

          <section className="rounded-md border border-line bg-white p-5">
            <div className="mb-4 font-semibold">Workload Evaluation</div>
            <div className="grid gap-3 lg:grid-cols-2">
              {Object.entries(latest.workload_evaluation_package).map(([section, values]) => (
                <div key={section} className="rounded-md border border-line bg-panel p-4">
                  <div className="font-semibold">{section.replaceAll("_", " ")}</div>
                  <div className="mt-3 grid gap-2 text-sm text-muted">
                    {Object.entries(values ?? {}).map(([key, value]) => (
                      <div key={key} className="flex justify-between gap-4 border-b border-line pb-1">
                        <span>{key.replaceAll("_", " ")}</span>
                        <span className="text-right font-medium text-ink">{valueToString(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-md border border-line bg-white p-5">
            <div className="mb-4 font-semibold">Metric Quality Scorecard</div>
            <div className="grid gap-3 md:grid-cols-2">
              {latest.metric_quality_scorecard.map((metric) => (
                <div key={metric.name} className="rounded-md border border-line bg-panel p-4">
                  <div className="flex justify-between gap-4">
                    <div className="font-semibold">{metric.name}</div>
                    <div className="text-xs font-medium uppercase text-muted">{metric.quality}</div>
                  </div>
                  <div className="mt-2 text-lg font-semibold">{metric.value}</div>
                  <p className="mt-2 text-sm leading-6 text-muted">{metric.evidence}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-md border border-line bg-white p-5">
            <div className="mb-4 font-semibold">Recommendations</div>
            <div className="grid gap-3">
              {recommendations.map((rec) => (
                <div key={`${rec.priority}-${rec.title}`} className="rounded-md border border-line bg-panel p-4">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <div className="text-xs font-medium uppercase text-muted">{rec.priority} · score {rec.score}</div>
                      <div className="mt-1 font-semibold">{rec.title}</div>
                    </div>
                    <div className="text-sm text-muted">Impact {rec.impact} · Confidence {rec.confidence}</div>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-muted">{rec.evidence}</p>
                  <p className="mt-2 text-sm leading-6">{rec.action}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="grid gap-5 lg:grid-cols-2">
            <div className="rounded-md border border-line bg-white p-5">
              <div className="mb-4 font-semibold">Backend Test Plan</div>
              <div className="grid gap-3">
                {latest.phase_1_5_hardware_test_plan.map((item) => (
                  <div key={item.platform} className="rounded-md border border-line bg-panel p-4">
                    <div className="font-semibold">{item.platform}</div>
                    <p className="mt-2 text-sm leading-6 text-muted">{item.test}</p>
                    <p className="mt-2 text-sm leading-6">{item.success_criteria}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-md border border-line bg-white p-5">
              <div className="mb-4 font-semibold">Architecture Signals</div>
              <div className="grid gap-3">
                {latest.phase_2_architecture_signals.map((item) => (
                  <div key={item.signal} className="rounded-md border border-line bg-panel p-4">
                    <div className="flex justify-between gap-4">
                      <div className="font-semibold">{item.signal}</div>
                      <div className="text-xs font-medium uppercase text-muted">{item.strength}</div>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-muted">{item.evidence}</p>
                    <p className="mt-2 text-sm leading-6">{item.implication}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="rounded-md border border-line bg-white p-5">
            <div className="mb-4 flex items-center gap-2 font-semibold">
              <FileText size={18} aria-hidden />
              Do Not Do Yet
            </div>
            <div className="grid gap-2">
              {latest.do_not_do_yet.map((item) => (
                <div key={item} className="rounded-md border border-line bg-panel p-3 text-sm text-muted">{item}</div>
              ))}
            </div>
          </section>
        </>
      ) : (
        <section className="rounded-md border border-line bg-white p-5 text-sm text-muted">
          No Workload Report yet. Generate one from the current local evidence corpus.
        </section>
      )}
    </div>
  );
}
