import Link from "next/link";
import { Shell } from "@/components/Shell";
import { getPhase1ExitPackages, getTasks } from "@/lib/api";
import { ArrowLeft, ArrowRight } from "lucide-react";

function Badge({ q }: { q: string }) {
  const m: Record<string, string> = { verified: "bg-teal-50 text-teal-800 border-teal-200", estimated: "bg-amber-50 text-amber-800 border-amber-200", inferred: "bg-blue-50 text-blue-800 border-blue-200", nodata: "bg-slate-50 text-slate-500 border-slate-200" };
  const l: Record<string, string> = { verified: "✓ Verified", estimated: "~ Estimated", inferred: "≈ Inferred", nodata: "— No data" };
  return <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-semibold ${m[q] ?? m.nodata}`}>{l[q] ?? q}</span>;
}

const priorityBorder: Record<string, string> = { P0: "border-l-red-400", P1: "border-l-amber-400", P2: "border-l-slate-300", P3: "border-l-slate-200" };
const priorityBadge: Record<string, string> = { P0: "border-red-200 bg-red-50 text-red-700", P1: "border-amber-200 bg-amber-50 text-amber-700", P2: "border-slate-200 bg-slate-50 text-slate-600", P3: "border-slate-200 bg-slate-50 text-slate-500" };

function effortLabel(e: number) {
  if (e <= 30) return { label: "LOW", color: "text-teal-700" };
  if (e <= 60) return { label: "MED", color: "text-amber-700" };
  return { label: "HIGH", color: "text-red-600" };
}

function qualityFromRec(confidence: number): string {
  if (confidence >= 70) return "verified";
  if (confidence >= 50) return "estimated";
  return "inferred";
}

function relatedLink(title: string): { href: string; label: string } | null {
  const t = title.toLowerCase();
  if (t.includes("context") || t.includes("token") || t.includes("prefix") || t.includes("repeat")) return { href: "/context", label: "Context Inspector" };
  if (t.includes("retry") || t.includes("cost") || t.includes("budget")) return { href: "/cost", label: "Cost Explorer" };
  if (t.includes("tool") || t.includes("wait") || t.includes("bottleneck") || t.includes("latency")) return { href: "/bottlenecks", label: "Bottlenecks" };
  return null;
}

export default async function RecommendationsPage() {
  const [tasks, reports] = await Promise.all([
    getTasks().catch(() => []),
    getPhase1ExitPackages(),
  ]);
  const latestReport = reports?.[0] ?? null;
  const recs = latestReport?.workload_recommendation_package?.prioritized_recommendations ?? [];
  const summary = latestReport?.workload_recommendation_package?.executive_recommendation_summary ?? [];
  const actionPlan = latestReport?.workload_recommendation_package?.current_infrastructure_action_plan ?? [];
  const scorecard = latestReport?.metric_quality_scorecard ?? [];
  const measuredCount = scorecard.filter((m) => m.quality === "measured").length;
  const estimatedCount = scorecard.filter((m) => m.quality === "estimated").length;
  const inferredCount = scorecard.filter((m) => m.quality === "inferred").length;
  const missingCount = scorecard.filter((m) => m.quality === "missing").length;

  return (
    <Shell hasData>
      <div className="grid gap-5">
        <div>
          <Link href="/" className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-mint mb-2"><ArrowLeft size={12} /> Overview</Link>
          <h1 className="text-2xl font-bold text-ink">Recommendations</h1>
          <p className="mt-1 text-sm text-slate-500">Ranked by impact × confidence ÷ effort. Every recommendation shows its evidence source.</p>
        </div>

        {/* Data confidence strip */}
        {scorecard.length > 0 && (
          <section className="grid gap-3 sm:grid-cols-4">
            {[
              { label: "Verified", count: measuredCount, q: "verified" },
              { label: "Estimated", count: estimatedCount, q: "estimated" },
              { label: "Inferred", count: inferredCount, q: "inferred" },
              { label: "No data", count: missingCount, q: "nodata" },
            ].map(({ label, count, q }) => (
              <div key={label} className={`rounded-xl border p-4 text-center shadow-sm ${{ verified: "border-teal-200 bg-teal-50", estimated: "border-amber-200 bg-amber-50", inferred: "border-blue-200 bg-blue-50", nodata: "border-line bg-white" }[q]}`}>
                <Badge q={q} />
                <p className={`mt-2 text-2xl font-bold ${{ verified: "text-teal-700", estimated: "text-amber-700", inferred: "text-blue-700", nodata: "text-slate-400" }[q]}`}>{count}</p>
                <p className="text-xs text-slate-400 mt-0.5">metrics</p>
              </div>
            ))}
          </section>
        )}

        {/* Executive summary */}
        {summary.length > 0 && (
          <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
            <h2 className="mb-3 font-semibold text-ink">Summary</h2>
            <ul className="space-y-1.5">
              {summary.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                  <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-mint" />
                  {s}
                </li>
              ))}
            </ul>
          </section>
        )}

        {/* Recommendation cards */}
        {recs.length === 0 ? (
          <section className="rounded-xl border border-line bg-white p-6 shadow-sm">
            <h2 className="font-semibold text-ink">No recommendations yet</h2>
            <p className="mt-2 max-w-xl text-sm text-slate-500">
              Recommendations are generated from your trace data. Import traces and run the workload analyzer from the{" "}
              <a href="http://localhost:3000/workload-report" target="_blank" rel="noopener noreferrer" className="text-mint hover:underline">dev dashboard</a>{" "}
              to populate this screen.
            </p>
            <Link href="/runs" className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-mint hover:underline">
              View runs <ArrowRight size={14} />
            </Link>
          </section>
        ) : (
          <section className="grid gap-4">
            {recs.map((rec, i) => {
              const effort = effortLabel(rec.effort);
              const related = relatedLink(rec.title);
              return (
                <article key={i} className={`rounded-xl border border-l-4 border-line bg-white p-5 shadow-sm ${priorityBorder[rec.priority] ?? priorityBorder.P3}`}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className={`rounded border px-2.5 py-1 text-xs font-bold ${priorityBadge[rec.priority] ?? priorityBadge.P3}`}>
                        #{i + 1} · {rec.priority}
                      </span>
                      <h3 className="text-base font-semibold text-ink">{rec.title}</h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge q={qualityFromRec(rec.confidence)} />
                      <span className={`rounded-full border border-line bg-panel px-2 py-0.5 text-xs font-semibold ${rec.score >= 80 ? "text-teal-700" : rec.score >= 60 ? "text-amber-700" : "text-slate-500"}`}>
                        Score {rec.score}
                      </span>
                    </div>
                  </div>

                  <div className="mt-4 grid grid-cols-3 gap-3">
                    <div className="rounded-lg border border-line bg-panel p-2 text-center">
                      <p className="text-xs text-slate-400">Impact</p>
                      <p className={`mt-1 text-xl font-bold ${rec.impact >= 70 ? "text-teal-700" : rec.impact >= 50 ? "text-amber-700" : "text-slate-500"}`}>{rec.impact}</p>
                    </div>
                    <div className="rounded-lg border border-line bg-panel p-2 text-center">
                      <p className="text-xs text-slate-400">Confidence</p>
                      <p className={`mt-1 text-xl font-bold ${rec.confidence >= 70 ? "text-teal-700" : rec.confidence >= 50 ? "text-amber-700" : "text-slate-500"}`}>{rec.confidence}</p>
                    </div>
                    <div className="rounded-lg border border-line bg-panel p-2 text-center">
                      <p className="text-xs text-slate-400">Effort</p>
                      <p className={`mt-1 text-xl font-bold ${effort.color}`}>{effort.label}</p>
                    </div>
                  </div>

                  <div className="mt-4 space-y-2">
                    <p className="text-sm text-slate-600"><span className="font-semibold text-ink">Evidence: </span>{rec.evidence}</p>
                    <p className="text-sm text-slate-700"><span className="font-semibold text-ink">Action: </span>{rec.action}</p>
                  </div>

                  {related && (
                    <Link href={related.href} className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-mint hover:underline">
                      Open {related.label} <ArrowRight size={12} />
                    </Link>
                  )}
                </article>
              );
            })}
          </section>
        )}

        {/* Action plan */}
        {actionPlan.length > 0 && (
          <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
            <h2 className="mb-3 font-semibold text-ink">Action plan</h2>
            <ol className="space-y-2">
              {actionPlan.map((step, i) => (
                <li key={i} className="flex items-start gap-3 text-sm">
                  <span className="mt-0.5 grid h-5 w-5 flex-shrink-0 place-items-center rounded-full border border-line bg-teal-50 text-xs font-bold text-mint">{i + 1}</span>
                  <span className="text-slate-700">{step}</span>
                </li>
              ))}
            </ol>
          </section>
        )}

        <div className="flex flex-wrap gap-3">
          <Link href="/bottlenecks" className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:border-mint hover:text-mint transition-colors"><ArrowLeft size={14} /> Bottlenecks</Link>
          <Link href="/context" className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:border-mint hover:text-mint transition-colors">Context Inspector <ArrowRight size={14} /></Link>
          <Link href="/cost" className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:border-mint hover:text-mint transition-colors">Cost Explorer <ArrowRight size={14} /></Link>
        </div>
      </div>
    </Shell>
  );
}
