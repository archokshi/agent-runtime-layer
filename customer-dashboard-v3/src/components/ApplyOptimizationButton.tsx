"use client";

import { useState } from "react";
import { Zap, CheckCircle, Loader } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

type ProofResult = {
  proof_id: string; token_reduction_percent: number;
  cost_reduction_percent: number; evidence_quality: string; message: string;
};

export function ApplyOptimizationButton({ taskId }: { taskId: string }) {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [proof, setProof] = useState<ProofResult | null>(null);
  const [error, setError] = useState("");

  async function apply() {
    setState("loading"); setError("");
    try {
      const res = await fetch(`${API}/tasks/${taskId}/apply-optimization`, { method: "POST" });
      if (!res.ok) { const b = await res.json().catch(() => ({})); throw new Error(b.detail || `Error ${res.status}`); }
      setProof(await res.json());
      setState("done");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setState("error");
    }
  }

  if (state === "done" && proof) {
    return (
      <div className="proof-card">
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
          <CheckCircle size={15} color="var(--mint)" />
          <span style={{ fontSize: 14, fontWeight: 600 }}>Optimization Applied — Proof Card</span>
          <span className={`badge ${proof.evidence_quality === "measured" ? "badge-mint" : "badge-amber"}`} style={{ marginLeft: "auto" }}>
            {proof.evidence_quality === "measured" ? "✓ Verified" : "~ Estimated"}
          </span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <div style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 9, padding: "14px", textAlign: "center" }}>
            <div className="section-label">Token reduction</div>
            <div className="proof-val">−{proof.token_reduction_percent.toFixed(1)}%</div>
          </div>
          <div style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 9, padding: "14px", textAlign: "center" }}>
            <div className="section-label">Cost reduction</div>
            <div className="proof-val">−{proof.cost_reduction_percent.toFixed(1)}%</div>
          </div>
        </div>
        <p style={{ fontSize: 12, color: "var(--muted)", marginTop: 12, lineHeight: 1.6 }}>{proof.message}</p>
        <p style={{ fontSize: 11, color: "var(--muted2)", marginTop: 4, fontFamily: "var(--mono)" }}>Proof ID: {proof.proof_id}</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
        <Zap size={16} color="var(--mint)" />
        <span style={{ fontWeight: 600, fontSize: 14 }}>Apply Optimization</span>
        <span className="badge badge-muted" style={{ marginLeft: "auto" }}>Phase 1.7</span>
      </div>
      <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 14, lineHeight: 1.6 }}>
        Strip stable context (system prompt, tool definitions, repo summary) from the per-call payload.
        Agentium stores a verified before/after proof record.
      </p>
      {state === "error" && (
        <p style={{ fontSize: 13, color: "var(--red)", marginBottom: 12 }}>Error: {error}</p>
      )}
      <button className="btn btn-primary" onClick={apply} disabled={state === "loading"}>
        {state === "loading"
          ? <><Loader size={14} className="animate-spin" /> Applying…</>
          : <><Zap size={14} /> Apply optimization</>}
      </button>
    </div>
  );
}
