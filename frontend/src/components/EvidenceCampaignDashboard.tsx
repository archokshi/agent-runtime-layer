"use client";

import { useState } from "react";

import { browserBaseUrl } from "@/lib/api";
import type { EvidenceCampaignReport, EvidenceCampaignTarget, EvidenceCampaignTrack } from "@/lib/types";

function StatusBadge({ status }: { status: "ready" | "partial" | "missing" }) {
  return <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold capitalize text-muted">{status}</span>;
}

function TargetRow({ target }: { target: EvidenceCampaignTarget }) {
  return (
    <div className="rounded-md border border-line bg-panel p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold">{target.label}</p>
          <p className="mt-1 text-xs leading-5 text-muted">{target.phase2_use}</p>
        </div>
        <StatusBadge status={target.status} />
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-white">
        <div className="h-full bg-accent" style={{ width: `${Math.min(100, target.percent)}%` }} />
      </div>
      <p className="mt-2 text-xs font-semibold text-muted">
        {target.current} / {target.target} · {target.percent.toFixed(1)}%
      </p>
    </div>
  );
}

function TrackCard({ track }: { track: EvidenceCampaignTrack }) {
  return (
    <section className="rounded-lg border border-line bg-white p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase text-muted">{track.track_id.replaceAll("_", " ")}</p>
          <h2 className="mt-1 text-xl font-black">{track.name}</h2>
          <p className="mt-2 text-sm leading-6 text-muted">{track.summary}</p>
        </div>
        <StatusBadge status={track.status} />
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {track.targets.map((target) => <TargetRow key={target.target_id} target={target} />)}
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase text-muted">Phase 2 consumes</p>
          <ul className="mt-2 space-y-1 text-sm text-muted">
            {track.phase2_consumes.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase text-muted">Next</p>
          <ul className="mt-2 space-y-1 text-sm text-muted">
            {(track.missing_items.length ? track.missing_items : track.next_steps).slice(0, 5).map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      </div>
    </section>
  );
}

export function EvidenceCampaignDashboard({ initialReports }: { initialReports: EvidenceCampaignReport[] }) {
  const [reports, setReports] = useState(initialReports);
  const [isGenerating, setIsGenerating] = useState(false);
  const latest = reports[0] ?? null;

  async function generate() {
    setIsGenerating(true);
    try {
      const response = await fetch(`${browserBaseUrl}/evidence-campaign/generate`, { method: "POST" });
      if (!response.ok) {
        throw new Error(`Generate failed: ${response.status}`);
      }
      const report = await response.json() as EvidenceCampaignReport;
      setReports([report, ...reports.filter((item) => item.campaign_id !== report.campaign_id)]);
    } finally {
      setIsGenerating(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-line bg-white p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-sm font-semibold text-accent">Phase 1.6 Evidence Campaign</p>
            <h1 className="mt-2 text-3xl font-black tracking-normal">Run the evidence campaign before Phase 2.</h1>
            <p className="mt-3 max-w-3xl text-base leading-7 text-muted">
              This report checks whether Agent Runtime Layer has enough real traces, benchmark-style runs, before/after pairs, and backend/system telemetry imports to feed Agentic Inference System Blueprint Validation.
            </p>
          </div>
          <button
            type="button"
            onClick={generate}
            disabled={isGenerating}
            className="inline-flex h-10 items-center justify-center rounded-md bg-accent px-4 text-sm font-semibold text-white disabled:opacity-60"
          >
            {isGenerating ? "Generating..." : "Generate Campaign Report"}
          </button>
        </div>
      </section>

      {latest ? (
        <>
          <section className="rounded-lg border border-line bg-white p-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase text-muted">{latest.campaign_id}</p>
                <h2 className="mt-2 text-2xl font-black">Campaign score {latest.campaign_score}/100</h2>
                <p className="mt-3 max-w-4xl text-sm leading-6 text-muted">{latest.executive_summary}</p>
              </div>
              <div className="flex flex-col items-start gap-3">
                <StatusBadge status={latest.campaign_status} />
                {latest.campaign_id ? (
                  <a className="rounded-md border border-line px-3 py-2 text-sm font-semibold hover:bg-panel" href={`${browserBaseUrl}/evidence-campaign/${latest.campaign_id}/export.md`}>
                    Export Markdown
                  </a>
                ) : null}
              </div>
            </div>
            <div className="mt-5 grid gap-3 md:grid-cols-3">
              <div className="rounded-md border border-line bg-panel p-4">
                <p className="text-xs font-semibold uppercase text-muted">Workload Model Ready</p>
                <p className="mt-2 text-xl font-black">{latest.ready_for_phase2_workload_model ? "Yes" : "No"}</p>
              </div>
              <div className="rounded-md border border-line bg-panel p-4">
                <p className="text-xs font-semibold uppercase text-muted">Backend Validation Ready</p>
                <p className="mt-2 text-xl font-black">{latest.ready_for_phase2_backend_validation ? "Yes" : "No"}</p>
              </div>
              <div className="rounded-md border border-line bg-panel p-4">
                <p className="text-xs font-semibold uppercase text-muted">Regenerated System Handoff</p>
                <p className="mt-2 break-all text-sm font-semibold">{latest.regenerated_phase2_handoff_id ?? "Not generated"}</p>
              </div>
            </div>
          </section>

          <div className="grid gap-4">
            {latest.tracks.map((track) => <TrackCard key={track.track_id} track={track} />)}
          </div>

          <section className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-line bg-white p-6">
              <h2 className="text-xl font-black">Required Trace Fields</h2>
              <ul className="mt-4 grid gap-2 text-sm text-muted md:grid-cols-2">
                {latest.required_trace_fields.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
            <div className="rounded-lg border border-line bg-white p-6">
              <h2 className="text-xl font-black">No Claims</h2>
              <ul className="mt-4 space-y-2 text-sm leading-6 text-muted">
                {latest.no_claims.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
          </section>
        </>
      ) : (
        <section className="rounded-lg border border-line bg-white p-6 text-sm text-muted">
          No evidence campaign report generated yet.
        </section>
      )}
    </div>
  );
}
