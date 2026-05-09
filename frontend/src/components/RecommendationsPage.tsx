import type { Phase1ExitPackage, Task } from "@/lib/types";

function Badge({ quality }: { quality: string }) {
  const map: Record<string, string> = {
    measured: "bg-teal-50 text-teal-800 border-teal-200",
    estimated: "bg-amber-50 text-amber-800 border-amber-200",
    inferred: "bg-blue-50 text-blue-800 border-blue-200",
    missing: "bg-slate-50 text-slate-600 border-slate-200",
  };
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${map[quality] ?? map.estimated}`}>
      {quality}
    </span>
  );
}

const priorityBorder: Record<string, string> = {
  P0: "border-l-red-400",
  P1: "border-l-amber-400",
  P2: "border-l-slate-300",
  P3: "border-l-slate-200",
};
const priorityBadge: Record<string, string> = {
  P0: "border-red-200 bg-red-50 text-red-700",
  P1: "border-amber-200 bg-amber-50 text-amber-700",
  P2: "border-slate-200 bg-slate-50 text-slate-600",
  P3: "border-slate-200 bg-slate-50 text-slate-500",
};

function effortLabel(effort: number) {
  if (effort <= 30) return { label: "LOW", color: "text-teal-700" };
  if (effort <= 60) return { label: "MED", color: "text-amber-700" };
  return { label: "HIGH", color: "text-red-600" };
}

function scoreColor(score: number) {
  if (score >= 80) return "text-teal-700";
  if (score >= 60) return "text-amber-700";
  return "text-slate-500";
}

function evidenceQuality(rec: { confidence: number; impact: number }): string {
  if (rec.confidence >= 70 && rec.impact >= 70) return "measured";
  if (rec.confidence >= 50) return "estimated";
  return "inferred";
}

export function RecommendationsPage({
  latestReport,
  tasks,
}: {
  latestReport: Phase1ExitPackage | null;
  tasks: Task[];
}) {
  const recs = latestReport?.workload_recommendation_package?.prioritized_recommendations ?? [];
  const summary = latestReport?.workload_recommendation_package?.executive_recommendation_summary ?? [];
  const actionPlan = latestReport?.workload_recommendation_package?.current_infrastructure_action_plan ?? [];
  const doNotDoYet = latestReport?.do_not_do_yet ?? [];
  const qualityScorecard = latestReport?.metric_quality_scorecard ?? [];
  const measuredCount = qualityScorecard.filter((m) => m.quality === "measured").length;
  const estimatedCount = qualityScorecard.filter((m) => m.quality === "estimated").length;
  const missingCount = qualityScorecard.filter((m) => m.quality === "missing").length;

  return (
    <div className="grid gap-5">
      <div>
        <p className="text-sm font-medium text-teal-700">Ranked action list · {tasks.length} runs</p>
        <h1 className="mt-1 text-3xl font-semibold">Recommendations</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Ranked by impact × confidence ÷ effort. Every claim shows its evidence source and quality. High-confidence, low-effort items are quick wins — start there.
        </p>
      </div>

      {/* Evidence quality strip */}
      {qualityScorecard.length > 0 && (
        <section className="grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-teal-200 bg-teal-50 p-3 text-center">
            <p className="text-xs font-semibold uppercase text-teal-700">Measured</p>
            <p className="mt-2 text-2xl font-bold text-teal-700">{measuredCount}</p>
          </div>
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-center">
            <p className="text-xs font-semibold uppercase text-amber-700">Estimated</p>
            <p className="mt-2 text-2xl font-bold text-amber-700">{estimatedCount}</p>
          </div>
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-3 text-center">
            <p className="text-xs font-semibold uppercase text-blue-700">Inferred</p>
            <p className="mt-2 text-2xl font-bold text-blue-700">{qualityScorecard.filter((m) => m.quality === "inferred").length}</p>
          </div>
          <div className="rounded-lg border border-line bg-panel p-3 text-center">
            <p className="text-xs font-semibold uppercase text-muted">Missing</p>
            <p className={`mt-2 text-2xl font-bold ${missingCount > 0 ? "text-red-500" : "text-slate-400"}`}>{missingCount}</p>
          </div>
        </section>
      )}

      {/* Executive summary */}
      {summary.length > 0 && (
        <section className="rounded-lg border border-line bg-white p-5">
          <h2 className="mb-3 text-base font-semibold">Executive summary</h2>
          <ul className="space-y-1">
            {summary.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-teal-600" />
                {s}
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Recommendation cards */}
      {recs.length === 0 ? (
        <section className="rounded-lg border border-line bg-white p-6">
          <h2 className="font-semibold">No recommendations yet</h2>
          <p className="mt-2 max-w-xl text-sm text-muted">
            Recommendations are generated from the Workload Report. Go to{" "}
            <a href="/workload-report" className="text-teal-700 underline">Workload Report</a>{" "}
            and generate a report from your traces to see ranked recommendations here.
          </p>
        </section>
      ) : (
        <section className="grid gap-4">
          {recs.map((rec, i) => {
            const effort = effortLabel(rec.effort);
            return (
              <article
                key={i}
                className={`rounded-lg border border-l-4 border-line bg-white p-5 ${priorityBorder[rec.priority] ?? priorityBorder.P3}`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <span className={`rounded border px-2.5 py-1 text-xs font-bold ${priorityBadge[rec.priority] ?? priorityBadge.P3}`}>
                      #{i + 1} · {rec.priority}
                    </span>
                    <h3 className="text-base font-semibold text-slate-900">{rec.title}</h3>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge quality={evidenceQuality(rec)} />
                    <span className={`rounded-full border border-line bg-panel px-2 py-0.5 text-xs font-semibold ${scoreColor(rec.score)}`}>
                      Score {rec.score}
                    </span>
                  </div>
                </div>

                {/* Score breakdown */}
                <div className="mt-4 grid grid-cols-3 gap-3">
                  <div className="rounded-lg border border-line bg-panel p-2 text-center">
                    <p className="text-xs text-muted">Impact</p>
                    <p className={`mt-1 text-xl font-bold ${rec.impact >= 70 ? "text-teal-700" : rec.impact >= 50 ? "text-amber-700" : "text-slate-500"}`}>
                      {rec.impact}
                    </p>
                  </div>
                  <div className="rounded-lg border border-line bg-panel p-2 text-center">
                    <p className="text-xs text-muted">Confidence</p>
                    <p className={`mt-1 text-xl font-bold ${rec.confidence >= 70 ? "text-teal-700" : rec.confidence >= 50 ? "text-amber-700" : "text-slate-500"}`}>
                      {rec.confidence}
                    </p>
                  </div>
                  <div className="rounded-lg border border-line bg-panel p-2 text-center">
                    <p className="text-xs text-muted">Effort</p>
                    <p className={`mt-1 text-xl font-bold ${effort.color}`}>{effort.label}</p>
                  </div>
                </div>

                {/* Evidence + Action */}
                <div className="mt-4 space-y-2">
                  <p className="text-sm text-slate-600">
                    <span className="font-semibold text-slate-800">Evidence: </span>{rec.evidence}
                  </p>
                  <p className="text-sm text-slate-700">
                    <span className="font-semibold text-slate-800">Action: </span>{rec.action}
                  </p>
                </div>

                {rec.confidence < 60 && (
                  <p className="mt-3 inline-block rounded border border-blue-100 bg-blue-50 px-2 py-1 text-xs text-blue-700">
                    → Confidence is {rec.confidence} — gather more traces or add telemetry to improve signal
                  </p>
                )}
              </article>
            );
          })}
        </section>
      )}

      {/* Action plan + Do not do yet */}
      <div className="grid gap-4 lg:grid-cols-2">
        {actionPlan.length > 0 && (
          <section className="rounded-lg border border-line bg-white p-5">
            <h2 className="mb-3 text-base font-semibold">Current infrastructure action plan</h2>
            <ol className="space-y-2">
              {actionPlan.map((step, i) => (
                <li key={i} className="flex items-start gap-3 text-sm">
                  <span className="mt-0.5 grid h-5 w-5 flex-shrink-0 place-items-center rounded-full border border-line bg-teal-50 text-xs font-bold text-teal-700">
                    {i + 1}
                  </span>
                  <span className="text-slate-700">{step}</span>
                </li>
              ))}
            </ol>
          </section>
        )}
        {doNotDoYet.length > 0 && (
          <section className="rounded-lg border border-line bg-white p-5">
            <h2 className="mb-3 text-base font-semibold">Do not build yet</h2>
            <p className="mb-3 text-xs text-muted">These are out of scope for Phase 1 — no overclaiming.</p>
            <ul className="space-y-1">
              {doNotDoYet.map((item, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                  <span className="mt-1 text-slate-400">✗</span>
                  {item}
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </div>
  );
}
