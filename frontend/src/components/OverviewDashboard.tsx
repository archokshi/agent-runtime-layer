import Link from "next/link";
import { Activity, ArrowRight, FileText, Gauge, GitBranch, type LucideIcon } from "lucide-react";
import { StartDemoButton } from "@/components/StartDemoButton";
import type { BenchmarkSuiteSummary, Phase1ExitPackage, PlatformSummary, Task } from "@/lib/types";

type OverviewDashboardProps = {
  tasks: Task[];
  platform: PlatformSummary | null;
  benchmarks: BenchmarkSuiteSummary | null;
  workloadReports: Phase1ExitPackage[];
};

function getMetric(summary: PlatformSummary | null, label: string) {
  return summary?.metrics.find((metric) => metric.label === label)?.value ?? "0";
}

function getMetricDetail(summary: PlatformSummary | null, label: string) {
  return summary?.metrics.find((metric) => metric.label === label)?.detail ?? undefined;
}

function metricCard(label: string, value: string, detail?: string | null) {
  return { label, value, detail };
}

function statusLabel(status: string) {
  if (status === "completed") return "Succeeded";
  if (status === "failed") return "Failed";
  return status || "Unknown";
}

function statusClass(status: string) {
  if (status === "completed") return "bg-teal-50 text-teal-800 border-teal-200";
  if (status === "failed") return "bg-red-50 text-red-800 border-red-200";
  return "bg-amber-50 text-amber-800 border-amber-200";
}

function formatDate(value?: string | null) {
  if (!value) return "No timestamp";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function publicEvidenceQuality(value?: string) {
  if (!value) return "estimated";
  if (value.includes("measured") || value.includes("validation")) return "measured";
  if (value.includes("telemetry") || value.includes("benchmark")) return "measured";
  return "estimated";
}

function EvidenceBadge({ quality }: { quality: string }) {
  const classes: Record<string, string> = {
    measured: "bg-teal-50 text-teal-800 border-teal-200",
    estimated: "bg-amber-50 text-amber-800 border-amber-200",
    inferred: "bg-blue-50 text-blue-800 border-blue-200",
    missing: "bg-panel text-muted border-line",
  };
  return (
    <span className={`inline-flex h-7 items-center rounded-full border px-2 text-xs font-semibold ${classes[quality] ?? classes.estimated}`}>
      {quality}
    </span>
  );
}

function MetricCard({ label, value, detail }: { label: string; value: string; detail?: string | null }) {
  return (
    <div className="min-h-28 rounded-md border border-line bg-white p-4">
      <div className="text-xs font-semibold uppercase text-muted">{label}</div>
      <div className="mt-2 break-words text-2xl font-semibold">{value}</div>
      {detail ? <div className="mt-2 text-sm leading-5 text-muted">{detail}</div> : null}
    </div>
  );
}

function FindingCard({
  rank,
  title,
  body,
  badge,
  stats,
}: {
  rank: number;
  title: string;
  body: string;
  badge: string;
  stats: string[];
}) {
  return (
    <div className="rounded-md border border-line bg-panel p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="grid size-8 place-items-center rounded-md border border-line bg-white text-sm font-bold text-teal-700">{rank}</span>
          <div className="font-semibold">{title}</div>
        </div>
        <span className="rounded-full border border-line bg-white px-2 py-1 text-xs font-semibold text-muted">{badge}</span>
      </div>
      <p className="mt-3 text-sm leading-6 text-muted">{body}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {stats.map((stat) => (
          <span key={stat} className="rounded-md border border-line bg-white px-2 py-1 text-xs font-semibold">
            {stat}
          </span>
        ))}
      </div>
    </div>
  );
}

export function OverviewDashboard({ tasks, platform, benchmarks, workloadReports }: OverviewDashboardProps) {
  const latestTask = tasks[0];
  const latestReport = workloadReports[0];
  const measuredExperiment = platform?.measured_validation?.[0];
  const benchmarkTaskCount = benchmarks?.task_count ?? platform?.benchmark_suite?.task_count ?? 0;
  const benchmarkRuns = benchmarks?.run_count ?? platform?.benchmark_suite?.run_count ?? 0;
  const reportScore = latestReport?.architecture_readiness_score;
  const recommendations = latestReport?.workload_recommendation_package.prioritized_recommendations ?? [];
  const topRecommendations = recommendations.slice(0, 3);
  const modelCompute = latestReport?.workload_evaluation_package.model_compute_profile ?? {};
  const contextProfile = latestReport?.workload_evaluation_package.context_kv_reuse_profile ?? {};
  const totalEstimatedCost = typeof modelCompute.estimated_cost_dollars === "number" ? modelCompute.estimated_cost_dollars : null;
  const repeatedContextPercent = typeof contextProfile.avg_repeated_context_percent === "number" ? contextProfile.avg_repeated_context_percent : null;
  const repeatedCostOpportunity = totalEstimatedCost !== null && repeatedContextPercent !== null
    ? totalEstimatedCost * (repeatedContextPercent / 100)
    : null;
  const metricQuality = latestReport?.metric_quality_scorecard ?? [];
  const evidenceCounts = {
    measured: metricQuality.filter((item) => item.quality === "measured").length,
    estimated: metricQuality.filter((item) => item.quality === "estimated").length,
    inferred: metricQuality.filter((item) => item.quality === "inferred").length,
    missing: metricQuality.filter((item) => item.quality === "missing").length,
  };
  const topIssue = getMetricDetail(platform, "Model Calls")?.includes("tool") ? "Tool wait" : "Context waste";
  const cards = [
    metricCard("Agent runs", String(tasks.length || getMetric(platform, "Tasks")), "traced in this workspace"),
    metricCard("Success rate", benchmarks?.task_success_rate_percent == null ? "Unknown" : `${benchmarks.task_success_rate_percent}%`, "known benchmark outcomes"),
    metricCard("Trace coverage", getMetric(platform, "Trace Coverage"), getMetricDetail(platform, "Trace Coverage")),
    metricCard("Model cost", totalEstimatedCost === null ? "$0" : `$${totalEstimatedCost.toFixed(4)}`, "estimated local workload"),
    metricCard("Repeated context", measuredExperiment?.measured_input_token_reduction_percent ? `${measuredExperiment.measured_input_token_reduction_percent}%` : "Estimate", "measured/estimated opportunity"),
    metricCard("Benchmarks", String(benchmarkRuns), `${benchmarkTaskCount} task result(s)`),
  ];
  const advancedCards: { title: string; body: string; href: string; icon: LucideIcon }[] = [
    {
      title: "Backend-aware hints",
      body: "Prefix overlap, cache locality, queue-depth hints, and prefill/decode classification.",
      href: "/platform",
      icon: Gauge,
    },
    {
      title: "Hardware telemetry",
      body: "Imported GPU, memory, queue, cache, prefill, and decode symptoms correlated with agent spans.",
      href: "/platform",
      icon: Activity,
    },
    {
      title: "Silicon Blueprint",
      body: "Workload profile, bottleneck map, memory hierarchy recommendations, and primitive ranking.",
      href: "/blueprints",
      icon: GitBranch,
    },
    {
      title: "Workload Report",
      body: "Evaluation, recommendations, evidence quality, and backend test plan generated from your agent traces.",
      href: "/workload-report",
      icon: FileText,
    },
  ];

  return (
    <div className="grid gap-5">
      <section className="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="rounded-md border border-line bg-white p-8">
          <div className="text-sm font-semibold text-teal-700">Developer Preview - Self-hosted profiler for coding agents</div>
          <h1 className="mt-2 max-w-4xl text-4xl font-extrabold leading-tight tracking-normal md:text-5xl">
            See why your coding agent is slow, expensive, or stuck.
          </h1>
          <p className="mt-4 max-w-3xl text-base leading-7 text-muted">
            Trace coding-agent runs, diagnose latency, cost, context waste, retries, and tool wait, then validate optimizations with evidence developers can trust.
          </p>
          <div className="mt-5 flex flex-wrap gap-2">
            {["Laptop", "Dev server", "CI runner", "On-prem", "Private cloud", "SQLite by default"].map((item) => (
              <span key={item} className="rounded-full border border-line bg-panel px-3 py-1 text-sm font-semibold text-muted">{item}</span>
            ))}
          </div>
          <div className="mt-7 flex flex-wrap gap-3">
            <StartDemoButton />
            <Link href="/import" className="inline-flex h-11 items-center rounded-md border border-line px-4 text-sm font-semibold hover:bg-panel">
              Import trace
            </Link>
            <Link href={latestTask ? `/tasks/${latestTask.task_id}` : "/runs"} className="inline-flex h-11 items-center rounded-md border border-line px-4 text-sm font-semibold hover:bg-panel">
              View latest run
            </Link>
          </div>
        </div>

        <div className="rounded-md border border-line bg-white p-6">
          <div className="font-semibold">Agent Quality Loop</div>
          <p className="mt-2 text-sm leading-6 text-muted">
            The dashboard is organized as the loop developers already need: observe, diagnose, recommend, validate, and report.
          </p>
          <div className="mt-4 grid gap-2">
            {[
              ["1", "Observe", "Capture traces, model calls, tools, files, and terminal events.", "traces"],
              ["2", "Diagnose", "Find bottlenecks, repeated context, retries, cost, and latency.", "analysis"],
              ["3", "Recommend", "Show the next best action with impact and confidence.", "actions"],
              ["4", "Validate", "Compare baseline vs optimized and track benchmark evidence.", "evidence"],
              ["5", "Report", "Create the Workload Report with recommendations and backend test plan.", "workload"],
            ].map(([num, title, body, tag]) => (
              <div key={num} className="grid grid-cols-[2.25rem_1fr_auto] items-center gap-3 rounded-md border border-line bg-panel p-3">
                <span className="grid size-8 place-items-center rounded-md border border-line bg-white font-bold text-teal-700">{num}</span>
                <div>
                  <div className="font-semibold">{title}</div>
                  <div className="text-sm leading-5 text-muted">{body}</div>
                </div>
                <span className="rounded-full bg-white px-2 py-1 text-xs font-semibold text-muted">{tag}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section>
        <div className="mb-3 flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">Project Workload Health</h2>
            <p className="mt-1 text-sm text-muted">Cumulative summary across traced runs in this workspace.</p>
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
          {cards.map((card) => (
            <MetricCard key={card.label} {...card} />
          ))}
        </div>
      </section>

      {tasks.length === 0 ? (
        <section className="rounded-md border border-line bg-white p-6">
          <div className="font-semibold">No traces yet</div>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
            Import a sample trace or capture a local command to populate the overview with real agent-run data.
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <Link href="/import" className="inline-flex h-10 items-center rounded-md bg-teal-700 px-4 text-sm font-semibold text-white">
              Import sample trace
            </Link>
            <Link href="/runs" className="inline-flex h-10 items-center rounded-md border border-line px-4 text-sm font-semibold">
              View runs
            </Link>
          </div>
        </section>
      ) : null}

      <section className="grid gap-5 lg:grid-cols-2">
        <div className="rounded-md border border-line bg-white p-5">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">What is slowing agents down?</h2>
              <p className="mt-1 text-sm leading-6 text-muted">Ranked from the current local evidence.</p>
            </div>
            <EvidenceBadge quality="estimated" />
          </div>
          <div className="grid gap-3">
            <FindingCard
              rank={1}
              title="Tool wait blocks progress"
              body="Tests, terminal commands, and file operations consume elapsed time while the model may be idle."
              badge="P1"
              stats={[`${getMetric(platform, "Model Calls")} model/tool signal`, "scheduler candidate"]}
            />
            <FindingCard
              rank={2}
              title="Context is repeated across calls"
              body="Stable instructions, repo summaries, and tool schemas can be separated from dynamic task payloads."
              badge="P0"
              stats={[measuredExperiment ? `${measuredExperiment.measured_input_token_reduction_percent}% measured token drop` : "optimization available", "context candidate"]}
            />
            <FindingCard
              rank={3}
              title="Benchmark evidence is still developing"
              body="Benchmark records are tracked, but official benchmark performance should only be claimed after verified runs."
              badge="P2"
              stats={[`${benchmarkTaskCount} benchmark task(s)`, "no overclaiming"]}
            />
          </div>
        </div>

        <div className="rounded-md border border-line bg-white p-5">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">What should developers do next?</h2>
              <p className="mt-1 text-sm leading-6 text-muted">A short action list with evidence and confidence.</p>
            </div>
            <EvidenceBadge quality={topRecommendations.length ? "measured" : "estimated"} />
          </div>
          <div className="grid gap-3">
            {(topRecommendations.length ? topRecommendations : [
              {
                priority: "P0" as const,
                title: "Import or capture your first agent trace",
                evidence: "No workload report exists yet.",
                action: "Use the import page or CLI trace command to create the first run.",
                impact: 80,
                confidence: 80,
                effort: 20,
                risk: 5,
                score: 90,
              },
            ]).map((rec) => (
              <div key={`${rec.priority}-${rec.title}`} className="rounded-md border border-line bg-panel p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="font-semibold">{rec.title}</div>
                  <span className="rounded-full border border-line bg-white px-2 py-1 text-xs font-semibold text-muted">{rec.priority}</span>
                </div>
                <p className="mt-2 text-sm leading-6 text-muted">{rec.evidence}</p>
                <p className="mt-2 text-sm leading-6">{rec.action}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="rounded-md border border-line bg-white px-2 py-1 text-xs font-semibold">Impact {rec.impact}</span>
                  <span className="rounded-md border border-line bg-white px-2 py-1 text-xs font-semibold">Confidence {rec.confidence}</span>
                  <span className="rounded-md border border-line bg-white px-2 py-1 text-xs font-semibold">Score {rec.score}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="rounded-md border border-line bg-white p-5">
        <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">Cost & Savings</h2>
            <p className="mt-1 text-sm leading-6 text-muted">
              Shows model cost, repeated-context cost opportunity, and measured before/after savings when available.
            </p>
          </div>
          <EvidenceBadge quality={measuredExperiment ? "measured" : "estimated"} />
        </div>
        <div className="grid gap-3 md:grid-cols-4">
          <MetricCard
            label="Total Model Cost"
            value={totalEstimatedCost === null ? "Unknown" : `$${totalEstimatedCost.toFixed(6)}`}
            detail="estimated from local traces"
          />
          <MetricCard
            label="Repeated Cost Opportunity"
            value={repeatedCostOpportunity === null ? "Unknown" : `$${repeatedCostOpportunity.toFixed(6)}`}
            detail="proportional estimate"
          />
          <MetricCard
            label="Measured Cost Reduction"
            value={measuredExperiment?.measured_cost_reduction_percent == null ? "No measurement" : `${measuredExperiment.measured_cost_reduction_percent}%`}
            detail="before/after validation"
          />
          <MetricCard
            label="Projected Token Reduction"
            value={measuredExperiment?.projected_input_token_reduction_percent == null ? "Unknown" : `${measuredExperiment.projected_input_token_reduction_percent}%`}
            detail="optimizer estimate"
          />
        </div>
      </section>

      <section className="rounded-md border border-line bg-white p-5">
        <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">Measured result developers can understand</h2>
            <p className="mt-1 text-sm leading-6 text-muted">
              The cleanest current credibility demo: fewer real model input tokens while preserving task success.
            </p>
          </div>
          <EvidenceBadge quality={measuredExperiment ? "measured" : "missing"} />
        </div>
        {measuredExperiment ? (
          <>
            <div className="grid items-stretch gap-4 md:grid-cols-[1fr_auto_1fr]">
              <div className="rounded-md border border-line bg-panel p-5">
                <div className="text-xs font-semibold uppercase text-muted">Projected input reduction</div>
                <div className="mt-2 text-4xl font-semibold">{measuredExperiment.projected_input_token_reduction_percent ?? 0}%</div>
              </div>
              <div className="grid size-12 place-items-center self-center justify-self-center rounded-full bg-teal-700 text-xl font-bold text-white">
                <ArrowRight size={22} aria-hidden />
              </div>
              <div className="rounded-md border border-line bg-panel p-5">
                <div className="text-xs font-semibold uppercase text-muted">Measured input reduction</div>
                <div className="mt-2 text-4xl font-semibold">{measuredExperiment.measured_input_token_reduction_percent ?? 0}%</div>
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="rounded-md border border-line bg-panel px-2 py-1 text-xs font-semibold">Cost reduction {measuredExperiment.measured_cost_reduction_percent ?? 0}%</span>
              <span className="rounded-md border border-line bg-panel px-2 py-1 text-xs font-semibold">Success preserved: {measuredExperiment.success_preserved ? "yes" : "unknown"}</span>
              <span className="rounded-md border border-line bg-panel px-2 py-1 text-xs font-semibold">No real KV-cache control claim</span>
            </div>
          </>
        ) : (
          <div className="rounded-md border border-line bg-panel p-4 text-sm leading-6 text-muted">
            No measured validation experiment is stored yet. Add one through the validation API after a before/after run.
          </div>
        )}
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <div className="rounded-md border border-line bg-white p-5">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">Evidence quality</h2>
              <p className="mt-1 text-sm leading-6 text-muted">Every claim should show whether it is measured, estimated, inferred, or missing.</p>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-4">
            {[
              ["measured", evidenceCounts.measured],
              ["estimated", evidenceCounts.estimated],
              ["inferred", evidenceCounts.inferred],
              ["missing", evidenceCounts.missing],
            ].map(([quality, count]) => (
              <div key={quality} className="rounded-md border border-line bg-panel p-4">
                <EvidenceBadge quality={String(quality)} />
                <div className="mt-3 text-2xl font-semibold">{String(count)}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-md border border-line bg-white p-5">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">Validation level</h2>
              <p className="mt-1 text-sm leading-6 text-muted">Keeps the developer preview honest.</p>
            </div>
            <EvidenceBadge quality="estimated" />
          </div>
          <div className="grid gap-3">
            <div className="rounded-md border border-line bg-panel p-4">
              <div className="font-semibold">What is proven</div>
              <p className="mt-2 text-sm leading-6 text-muted">
                Trace import, SDK/CLI capture, Aider-style traces, dashboard, recommendations, optimization packages, benchmark records, and Workload Reports.
              </p>
            </div>
            <div className="rounded-md border border-line bg-panel p-4">
              <div className="font-semibold">What is not claimed</div>
              <p className="mt-2 text-sm leading-6 text-muted">
                No official SWE-bench score, no real KV-cache control, no vLLM/SGLang/Dynamo integration, no hardware speedup, and no chip simulation.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-md border border-line bg-white p-5">
        <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">Recent agent runs</h2>
            <p className="mt-1 text-sm leading-6 text-muted">Click a run to inspect spans, graph, events, recommendations, and raw evidence.</p>
          </div>
          <Link href="/runs" className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-semibold hover:bg-panel">
            View all runs
          </Link>
        </div>
        {tasks.length ? (
          <div className="grid gap-2">
            {tasks.slice(0, 5).map((task) => (
              <Link key={task.task_id} href={`/tasks/${task.task_id}`} className="grid gap-3 rounded-md border border-line bg-panel p-3 hover:border-teal-600 md:grid-cols-[1.4fr_0.45fr_0.7fr_1fr] md:items-center">
                <div>
                  <div className="font-semibold">{task.goal}</div>
                  <div className="mt-1 text-xs text-muted">{task.task_id}</div>
                </div>
                <div>
                  <span className={`inline-flex rounded-full border px-2 py-1 text-xs font-semibold ${statusClass(task.status)}`}>
                    {statusLabel(task.status)}
                  </span>
                </div>
                <div className="text-sm text-muted">{formatDate(task.ended_at ?? task.started_at)}</div>
                <div className="text-sm text-muted">{task.summary ?? "Open run for details"}</div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="rounded-md border border-line bg-panel p-4 text-sm text-muted">No recent runs yet.</div>
        )}
      </section>

      <section className="rounded-md border border-line bg-white p-5">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold">Advanced evidence for backend and hardware decisions</h2>
            <p className="mt-1 text-sm leading-6 text-muted">
              Keep this below the developer workflow. It is powerful, but it should not be the first thing a new user must understand.
            </p>
          </div>
          <EvidenceBadge quality="inferred" />
        </div>
        <div className="grid gap-3 md:grid-cols-4">
          {advancedCards.map(({ title, body, href, icon: Icon }) => {
            return (
              <Link key={title} href={href} className="min-h-40 rounded-md border border-line bg-panel p-4 hover:border-teal-600">
                <Icon size={20} aria-hidden className="text-teal-700" />
                <div className="mt-3 font-semibold">{title}</div>
                <p className="mt-2 text-sm leading-6 text-muted">{body}</p>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
