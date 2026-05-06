import type { ValidationReport as ValidationReportType } from "@/lib/types";

function value(text: string | number | boolean | null | undefined) {
  if (text === true) return "Yes";
  if (text === false) return "No";
  if (text === null || text === undefined || text === "") return "Not set";
  return String(text);
}

function percent(text: number | null | undefined) {
  if (text === null || text === undefined) return "N/A";
  return `${text.toFixed(1)}%`;
}

export function ValidationReport({ validation }: { validation: ValidationReportType | null }) {
  if (!validation) {
    return null;
  }
  const metadata = validation.metadata;
  const hasMetadata = Object.values(metadata).some((item) => item !== null && item !== undefined && item !== "");
  if (!hasMetadata && !validation.comparison) {
    return null;
  }

  return (
    <section className="rounded-lg border border-line bg-white p-4">
      <h2 className="text-base font-semibold">Validation</h2>
      <div className="mt-4 grid gap-3 md:grid-cols-4">
        <div className="rounded-lg border border-line bg-panel p-3">
          <p className="text-xs font-medium uppercase text-slate-500">Benchmark</p>
          <p className="mt-2 font-semibold">{value(metadata.benchmark_name)}</p>
          <p className="mt-1 text-xs text-slate-600">{value(metadata.benchmark_task_id)}</p>
        </div>
        <div className="rounded-lg border border-line bg-panel p-3">
          <p className="text-xs font-medium uppercase text-slate-500">Agent</p>
          <p className="mt-2 font-semibold">{value(metadata.agent_name)}</p>
          <p className="mt-1 text-xs text-slate-600">{value(metadata.baseline_or_optimized)}</p>
        </div>
        <div className="rounded-lg border border-line bg-panel p-3">
          <p className="text-xs font-medium uppercase text-slate-500">Outcome</p>
          <p className="mt-2 font-semibold">{metadata.task_success ? "Succeeded" : "Not passed"}</p>
          <p className="mt-1 text-xs text-slate-600">Tests {value(metadata.tests_passed)} passed / {value(metadata.tests_failed)} failed</p>
        </div>
        <div className="rounded-lg border border-line bg-panel p-3">
          <p className="text-xs font-medium uppercase text-slate-500">Patch</p>
          <p className="mt-2 font-semibold">{value(metadata.patch_generated)}</p>
          <p className="mt-1 text-xs text-slate-600">{value(metadata.files_changed_count)} files changed</p>
        </div>
      </div>
      {validation.comparison ? (
        <div className="mt-4 rounded-lg border border-line bg-panel p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="text-xs font-medium uppercase text-slate-500">Before/After Pair</p>
              <p className="mt-1 font-semibold">{validation.comparison.before_after_pair_id}</p>
            </div>
            <p className="text-sm font-medium">Success preserved: {value(validation.comparison.success_preserved)}</p>
          </div>
          <div className="mt-3 grid gap-2 md:grid-cols-3">
            <div className="rounded border border-line bg-white px-3 py-2">
              <p className="text-xs text-slate-500">Repeated input reduction</p>
              <p className="mt-1 font-semibold">{percent(validation.comparison.repeated_input_token_reduction_percent)}</p>
            </div>
            <div className="rounded border border-line bg-white px-3 py-2">
              <p className="text-xs text-slate-500">Estimated cost reduction</p>
              <p className="mt-1 font-semibold">{percent(validation.comparison.estimated_cost_reduction_percent)}</p>
            </div>
            <div className="rounded border border-line bg-white px-3 py-2">
              <p className="text-xs text-slate-500">Latency change</p>
              <p className="mt-1 font-semibold">{percent(validation.comparison.latency_change_percent)}</p>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
