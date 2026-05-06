import type { AnalysisReport, BlueprintPreview } from "@/lib/types";

export function BottleneckReport({ analysis, blueprint }: { analysis: AnalysisReport; blueprint: BlueprintPreview | null }) {
  const parsedExternalModel = analysis.model_call_count > 0 && analysis.model_time_ms === 0 && analysis.tool_time_ms > 0;

  return (
    <section className="grid gap-4 lg:grid-cols-3">
      <div className="rounded-lg border border-line bg-white p-4">
        <h2 className="text-base font-semibold">Bottleneck</h2>
        <p className="mt-3 text-2xl font-semibold capitalize">{analysis.bottleneck_category.replaceAll("_", " ")}</p>
        <p className="mt-2 text-sm text-slate-600">Model {analysis.model_time_ms}ms, tool {analysis.tool_time_ms}ms, idle {analysis.orchestration_idle_ms}ms.</p>
        {parsedExternalModel ? <p className="mt-2 text-xs text-slate-500">Model usage was parsed from an external agent run, so its latency is included in tool time.</p> : null}
      </div>
      <div className="rounded-lg border border-line bg-white p-4">
        <h2 className="text-base font-semibold">Repeated Context</h2>
        <p className="mt-3 text-2xl font-semibold">{analysis.repeated_context_percent.toFixed(1)}%</p>
        <p className="mt-2 text-sm text-slate-600">{analysis.repeated_context_tokens_estimate.toLocaleString()} repeated tokens estimated.</p>
      </div>
      <div className="rounded-lg border border-line bg-white p-4">
        <h2 className="text-base font-semibold">Token Flow</h2>
        <p className="mt-3 text-2xl font-semibold">{analysis.total_input_tokens.toLocaleString()} in</p>
        <p className="mt-2 text-sm text-slate-600">{analysis.total_output_tokens.toLocaleString()} output tokens, {analysis.retry_count} retries.</p>
      </div>
      <div className="rounded-lg border border-line bg-white p-4 lg:col-span-3">
        <h2 className="text-base font-semibold">Silicon Blueprint Preview</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {!blueprint || blueprint.recommendations.length === 0 ? <p className="text-sm text-slate-600">No architecture recommendations triggered by this trace, or the preview is unavailable.</p> : null}
          {blueprint?.recommendations.map((rec) => (
            <div key={rec.recommendation_id} className="rounded-lg border border-line bg-panel p-3">
              <p className="text-xs font-medium uppercase text-slate-500">{rec.category}</p>
              <h3 className="mt-1 font-semibold">{rec.title}</h3>
              <p className="mt-2 text-sm text-slate-600">{rec.rationale}</p>
              <p className="mt-3 text-xs font-medium">Confidence {(rec.confidence * 100).toFixed(0)}%</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
