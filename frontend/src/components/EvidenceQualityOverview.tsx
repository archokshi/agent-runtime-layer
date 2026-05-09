import type { EvidenceQualityReport } from "@/lib/types";

function StatusBadge({ status }: { status: "ready" | "partial" | "missing" }) {
  return <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold capitalize text-muted">{status}</span>;
}

function QualityBadge({ quality }: { quality: "measured" | "estimated" | "inferred" | "missing" }) {
  return <span className="rounded-full border border-line px-2 py-1 text-xs font-semibold text-muted">{quality}</span>;
}

export function EvidenceQualityOverview({ report }: { report: EvidenceQualityReport }) {
  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-line bg-white p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-sm font-semibold text-accent">Evidence Quality</p>
            <h1 className="mt-2 text-3xl font-black tracking-normal">What can Phase 2 safely trust?</h1>
            <p className="mt-3 max-w-3xl text-base leading-7 text-muted">
              Every metric is labeled as measured, estimated, inferred, or missing so architecture work uses evidence honestly and avoids claiming real cache hits or hardware speedups without measurement.
            </p>
          </div>
          <div className="min-w-40 rounded-lg border border-line bg-panel p-4">
            <p className="text-xs font-semibold uppercase text-muted">Quality score</p>
            <p className="mt-2 text-3xl font-black">{report.overall_score}/100</p>
            <div className="mt-2"><StatusBadge status={report.overall_status} /></div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-4">
        {report.categories.map((category) => (
          <div key={category.category} className="rounded-lg border border-line bg-white p-5">
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs font-semibold uppercase text-muted">{category.category}</p>
              <StatusBadge status={category.status} />
            </div>
            <p className="mt-3 text-2xl font-black">{category.score}/100</p>
            <p className="mt-2 text-sm text-muted">
              {category.measured_count} measured, {category.estimated_count} estimated, {category.inferred_count} inferred, {category.missing_count} missing
            </p>
          </div>
        ))}
      </section>

      <section className="grid gap-5">
        {report.categories.map((category) => (
          <div key={category.category} className="rounded-lg border border-line bg-white p-6">
            <h2 className="text-xl font-black">{category.category}</h2>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full min-w-[980px] text-left text-sm">
                <thead>
                  <tr className="border-b border-line text-xs uppercase text-muted">
                    <th className="py-3">Metric</th>
                    <th className="py-3">Value</th>
                    <th className="py-3">Quality</th>
                    <th className="py-3">Source</th>
                    <th className="py-3">Risk</th>
                    <th className="py-3">Next validation</th>
                  </tr>
                </thead>
                <tbody>
                  {category.metrics.map((metric) => (
                    <tr key={metric.metric_id} className="border-b border-line align-top">
                      <td className="py-3">
                        <p className="font-semibold">{metric.label}</p>
                        <p className="mt-1 text-xs text-muted">{metric.phase2_use}</p>
                      </td>
                      <td className="py-3">{metric.value}</td>
                      <td className="py-3"><QualityBadge quality={metric.quality} /></td>
                      <td className="py-3 text-muted">{metric.source}</td>
                      <td className="py-3 text-muted">{metric.risk_if_overclaimed}</td>
                      <td className="py-3 text-muted">{metric.next_validation_step}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-line bg-white p-6">
          <h2 className="text-xl font-black">Missing Evidence</h2>
          <div className="mt-4 grid gap-2">
            {report.missing_evidence.length ? report.missing_evidence.map((item) => (
              <div key={item} className="rounded-md border border-line bg-panel px-3 py-2 text-sm">{item}</div>
            )) : <p className="text-sm text-muted">No missing evidence in the current local scoring model.</p>}
          </div>
        </div>
        <div className="rounded-lg border border-line bg-white p-6">
          <h2 className="text-xl font-black">Phase 2 Safety Rules</h2>
          <ul className="mt-4 space-y-2 text-sm leading-6 text-muted">
            {report.phase2_safety_rules.map((rule) => <li key={rule}>{rule}</li>)}
          </ul>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-line bg-white p-6">
          <h2 className="text-xl font-black">Next Steps</h2>
          <ul className="mt-4 space-y-2 text-sm leading-6 text-muted">
            {report.next_steps.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
        <div className="rounded-lg border border-line bg-white p-6">
          <h2 className="text-xl font-black">Boundaries</h2>
          <ul className="mt-4 space-y-2 text-sm leading-6 text-muted">
            {report.limitations.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      </section>
    </div>
  );
}
