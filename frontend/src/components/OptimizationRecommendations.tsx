import type { OptimizationReport } from "@/lib/types";

function seconds(ms: number) {
  return `${(ms / 1000).toFixed(1)}s`;
}

export function OptimizationRecommendations({ optimizations }: { optimizations: OptimizationReport | null }) {
  if (!optimizations) {
    return (
      <section className="rounded-lg border border-line bg-white p-4">
        <h2 className="text-base font-semibold">Top Optimization Recommendations</h2>
        <p className="mt-3 text-sm text-slate-600">Optimization recommendations are unavailable for this trace. The rest of the task evidence is still inspectable.</p>
      </section>
    );
  }
  return (
    <section className="rounded-lg border border-line bg-white p-4">
      <h2 className="text-base font-semibold">Top Optimization Recommendations</h2>
      <div className="mt-4 grid gap-3">
        {optimizations.recommendations.length === 0 ? (
          <p className="text-sm text-slate-600">No optimization recommendations triggered by this trace.</p>
        ) : null}
        {optimizations.recommendations.map((rec) => (
          <article key={rec.recommendation_id} className="rounded-lg border border-line bg-panel p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs font-medium uppercase text-slate-500">{rec.category.replaceAll("_", " ")}</p>
                <h3 className="mt-1 font-semibold">{rec.title}</h3>
              </div>
              <p className="text-xs font-medium">Confidence {(rec.confidence * 100).toFixed(0)}%</p>
            </div>
            <p className="mt-3 text-sm text-slate-700">{rec.evidence}</p>
            <p className="mt-2 text-sm text-slate-600">{rec.action}</p>
            <div className="mt-3 flex flex-wrap gap-2 text-xs font-medium text-slate-700">
              <span className="rounded border border-line bg-white px-2 py-1">Time {seconds(rec.estimated_time_savings_ms)}</span>
              <span className="rounded border border-line bg-white px-2 py-1">Cost ${rec.estimated_cost_savings_dollars.toFixed(6)}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
