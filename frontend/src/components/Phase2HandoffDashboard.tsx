"use client";

import { useState } from "react";

import { browserBaseUrl } from "@/lib/api";
import type { Phase2HandoffPackage, Phase2HandoffSection } from "@/lib/types";

function StatusBadge({ status }: { status: "ready" | "partial" | "missing" }) {
  return <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold capitalize text-muted">{status}</span>;
}

function SectionCard({ section }: { section: Phase2HandoffSection }) {
  return (
    <div className="rounded-lg border border-line bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-black">{section.title}</h3>
          <p className="mt-2 text-sm leading-6 text-muted">{section.summary}</p>
        </div>
        <StatusBadge status={section.status} />
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-3">
        <div>
          <p className="text-xs font-semibold uppercase text-muted">Consumes</p>
          <ul className="mt-2 space-y-1 text-sm text-muted">
            {section.phase2_consumes.slice(0, 6).map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase text-muted">Missing</p>
          <ul className="mt-2 space-y-1 text-sm text-muted">
            {section.missing_items.length ? section.missing_items.slice(0, 6).map((item) => <li key={item}>{item}</li>) : <li>None listed</li>}
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase text-muted">Next</p>
          <ul className="mt-2 space-y-1 text-sm text-muted">
            {section.next_steps.slice(0, 6).map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      </div>
    </div>
  );
}

export function Phase2HandoffDashboard({ initialPackages }: { initialPackages: Phase2HandoffPackage[] }) {
  const [packages, setPackages] = useState(initialPackages);
  const [isGenerating, setIsGenerating] = useState(false);
  const latest = packages[0] ?? null;

  async function generate() {
    setIsGenerating(true);
    try {
      const response = await fetch(`${browserBaseUrl}/phase-2-handoff/generate`, { method: "POST" });
      if (!response.ok) {
        throw new Error(`Generate failed: ${response.status}`);
      }
      const report = await response.json() as Phase2HandoffPackage;
      setPackages([report, ...packages.filter((item) => item.handoff_id !== report.handoff_id)]);
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-line bg-white p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-sm font-semibold text-accent">Phase 2 Handoff</p>
            <h1 className="mt-2 text-3xl font-black tracking-normal">Package Agent Runtime evidence for the Agentic Inference System Blueprint.</h1>
            <p className="mt-3 max-w-3xl text-base leading-7 text-muted">
              This is the final Phase 1 artifact: what Phase 2 may use, what backend/system/hardware evidence is missing, what to test next, and what must not be claimed.
            </p>
          </div>
          <button
            type="button"
            onClick={generate}
            disabled={isGenerating}
            className="inline-flex h-10 items-center justify-center rounded-md bg-accent px-4 text-sm font-semibold text-white disabled:opacity-60"
          >
            {isGenerating ? "Generating..." : "Generate Handoff"}
          </button>
        </div>
      </section>

      {latest ? (
        <>
          <section className="rounded-lg border border-line bg-white p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase text-muted">{latest.handoff_id}</p>
                <h2 className="mt-2 text-2xl font-black">Entry score {latest.phase2_entry_criteria_score}/100</h2>
                <p className="mt-3 max-w-4xl text-sm leading-6 text-muted">{latest.executive_summary}</p>
              </div>
              <div className="flex flex-col items-start gap-3">
                <StatusBadge status={latest.phase2_entry_criteria_status} />
                {latest.handoff_id ? (
                  <a className="rounded-md border border-line px-3 py-2 text-sm font-semibold hover:bg-panel" href={`${browserBaseUrl}/phase-2-handoff/${latest.handoff_id}/export.md`}>
                    Export Markdown
                  </a>
                ) : null}
              </div>
            </div>
          </section>

          <section className="grid gap-4">
            <SectionCard section={latest.workload_model_input} />
            <SectionCard section={latest.backend_gap_analysis_input} />
            <SectionCard section={latest.runtime_hardware_interface_input} />
            <SectionCard section={latest.memory_context_architecture_input} />
            <SectionCard section={latest.compiler_execution_graph_input} />
            <SectionCard section={latest.evidence_quality_gate} />
          </section>

          <section className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-line bg-white p-6">
              <h2 className="text-xl font-black">Phase 2 Test Plan</h2>
              <div className="mt-4 space-y-3">
                {latest.phase2_test_plan.map((item) => (
                  <div key={`${item.platform}-${item.test}`} className="rounded-md border border-line bg-panel p-3 text-sm">
                    <p className="font-semibold">{item.platform}</p>
                    <p className="mt-1 text-muted">{item.test}</p>
                    <p className="mt-2 text-xs font-semibold uppercase text-muted">Success: {item.success_criteria}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="rounded-lg border border-line bg-white p-6">
              <h2 className="text-xl font-black">Do Not Claim</h2>
              <ul className="mt-4 space-y-2 text-sm leading-6 text-muted">
                {latest.phase2_do_not_claim.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
          </section>
        </>
      ) : (
        <section className="rounded-lg border border-line bg-white p-6 text-sm text-muted">
          No Phase 2 handoff package generated yet.
        </section>
      )}
    </div>
  );
}
