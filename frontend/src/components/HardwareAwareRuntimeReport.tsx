import type { HardwareAnalysisReport } from "@/lib/types";

function maybePercent(value?: number | null) {
  return value === null || value === undefined ? "n/a" : `${value.toFixed(1)}%`;
}

function maybeMs(value?: number | null) {
  return value === null || value === undefined ? "n/a" : `${value.toFixed(0)}ms`;
}

function confidence(value: number) {
  return `${Math.round(value * 100)}%`;
}

export function HardwareAwareRuntimeReport({ report }: { report: HardwareAnalysisReport | null }) {
  if (!report) {
    return (
      <section className="rounded-lg border border-line bg-white p-4">
        <h2 className="text-base font-semibold">Hardware-Aware Runtime</h2>
        <p className="mt-1 text-sm text-slate-600">Import telemetry JSON with `POST /api/tasks/&lt;task_id&gt;/telemetry/import` to generate a hardware-aware bottleneck map. v3.0 uses imported samples only, not live GPU polling.</p>
      </section>
    );
  }

  return (
    <section className="rounded-lg border border-line bg-white p-4">
      <div>
        <h2 className="text-base font-semibold">Hardware-Aware Runtime</h2>
        <p className="mt-1 text-sm text-slate-600">Imported telemetry correlation. No live GPU metrics or full cluster monitoring.</p>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-4">
        <div className="rounded-lg border border-line bg-panel p-3">
          <p className="text-xs font-medium uppercase text-slate-500">Samples</p>
          <p className="mt-2 text-lg font-semibold">{report.summary.sample_count}</p>
          <p className="mt-1 text-xs text-slate-600">imported telemetry points</p>
        </div>
        <div className="rounded-lg border border-line bg-panel p-3">
          <p className="text-xs font-medium uppercase text-slate-500">GPU</p>
          <p className="mt-2 text-lg font-semibold">{maybePercent(report.summary.avg_gpu_utilization_percent)}</p>
          <p className="mt-1 text-xs text-slate-600">memory {maybePercent(report.summary.avg_gpu_memory_used_percent)}</p>
        </div>
        <div className="rounded-lg border border-line bg-panel p-3">
          <p className="text-xs font-medium uppercase text-slate-500">Queue</p>
          <p className="mt-2 text-lg font-semibold">{report.summary.max_queue_depth ?? "n/a"}</p>
          <p className="mt-1 text-xs text-slate-600">max backend queue depth</p>
        </div>
        <div className="rounded-lg border border-line bg-panel p-3">
          <p className="text-xs font-medium uppercase text-slate-500">Prefill/Decode</p>
          <p className="mt-2 text-lg font-semibold">{maybeMs(report.summary.avg_prefill_ms)} / {maybeMs(report.summary.avg_decode_ms)}</p>
          <p className="mt-1 text-xs text-slate-600">cache hit {report.summary.avg_kv_cache_hit_rate === null || report.summary.avg_kv_cache_hit_rate === undefined ? "n/a" : report.summary.avg_kv_cache_hit_rate.toFixed(2)}</p>
        </div>
      </div>
      <div className="mt-4 grid gap-3">
        {report.bottlenecks.map((bottleneck) => (
          <div key={bottleneck.bottleneck_id} className="rounded-lg border border-line bg-panel p-3">
            <div className="flex flex-wrap justify-between gap-2">
              <div>
                <p className="text-xs font-medium uppercase text-slate-500">{bottleneck.category}</p>
                <h3 className="mt-1 font-semibold">{bottleneck.title}</h3>
              </div>
              <p className="text-xs font-semibold">Confidence {confidence(bottleneck.confidence)}</p>
            </div>
            <p className="mt-2 text-sm text-slate-600">{bottleneck.evidence}</p>
            <p className="mt-2 text-sm">{bottleneck.recommendation}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 rounded-lg border border-line bg-panel p-3">
        <h3 className="font-semibold">Correlated Windows</h3>
        <div className="mt-3 grid gap-2">
          {report.correlated_windows.map((window) => (
            <div key={window.span_id} className="rounded border border-line bg-white p-2 text-sm">
              <p className="font-medium">{window.event_name} - {window.event_type}</p>
              <p className="text-xs text-slate-600">samples {window.sample_count}, GPU {maybePercent(window.avg_gpu_utilization_percent)}, queue {window.avg_queue_depth ?? "n/a"}, prefill {maybeMs(window.avg_prefill_ms)}, decode {maybeMs(window.avg_decode_ms)}</p>
            </div>
          ))}
        </div>
      </div>
      <p className="mt-3 text-xs text-slate-600">{report.notes}</p>
    </section>
  );
}
