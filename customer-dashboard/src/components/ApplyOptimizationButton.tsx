"use client";

import { useState } from "react";
import { browserBaseUrl } from "@/lib/api";
import { Zap, CheckCircle, Loader } from "lucide-react";

type ProofResult = {
  proof_id: string;
  token_reduction_percent: number;
  cost_reduction_percent: number;
  evidence_quality: string;
  message: string;
};

export function ApplyOptimizationButton({ taskId }: { taskId: string }) {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [proof, setProof] = useState<ProofResult | null>(null);
  const [error, setError] = useState("");

  async function handleApply() {
    setState("loading");
    setError("");
    try {
      const base = browserBaseUrl ?? "http://localhost:8000/api";
      const res = await fetch(`${base}/tasks/${taskId}/apply-optimization`, {
        method: "POST",
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error ${res.status}`);
      }
      const data: ProofResult = await res.json();
      setProof(data);
      setState("done");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setState("error");
    }
  }

  if (state === "done" && proof) {
    return (
      <div className="rounded-xl border-2 border-teal-300 bg-teal-50 p-5">
        <div className="flex items-center gap-2 mb-3">
          <CheckCircle size={18} className="text-mint flex-shrink-0" />
          <span className="font-semibold text-teal-800">Optimization applied</span>
          <span className={`ml-auto text-xs font-semibold px-2 py-0.5 rounded-full border ${
            proof.evidence_quality === "measured"
              ? "bg-teal-50 text-teal-800 border-teal-200"
              : "bg-amber-50 text-amber-800 border-amber-200"
          }`}>
            {proof.evidence_quality === "measured" ? "✓ Verified" : "~ Estimated"}
          </span>
        </div>
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div className="rounded-lg bg-white border border-teal-200 p-3 text-center">
            <p className="text-xs text-slate-400 font-medium">Token reduction</p>
            <p className="text-2xl font-bold text-teal-700 mt-1">
              −{proof.token_reduction_percent.toFixed(1)}%
            </p>
          </div>
          <div className="rounded-lg bg-white border border-teal-200 p-3 text-center">
            <p className="text-xs text-slate-400 font-medium">Cost reduction</p>
            <p className="text-2xl font-bold text-teal-700 mt-1">
              −{proof.cost_reduction_percent.toFixed(1)}%
            </p>
          </div>
        </div>
        <p className="text-xs text-teal-700 leading-relaxed">{proof.message}</p>
        <p className="text-xs text-slate-400 mt-2">Proof ID: {proof.proof_id}</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-line bg-white p-5">
      <div className="flex items-center gap-2 mb-2">
        <Zap size={16} className="text-mint" />
        <h3 className="font-semibold text-ink">Phase 1.7 — Apply optimization</h3>
      </div>
      <p className="text-sm text-slate-500 mb-4">
        Strip stable context (system prompt, tool definitions, repo summary) from the per-call
        payload. Agentium computes the expected token and cost reduction and stores a proof record.
      </p>
      {state === "error" && (
        <p className="text-sm text-red-600 mb-3">Error: {error}</p>
      )}
      <button
        onClick={handleApply}
        disabled={state === "loading"}
        className="inline-flex items-center gap-2 rounded-lg bg-mint px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90 transition-opacity disabled:opacity-50"
      >
        {state === "loading" ? (
          <><Loader size={14} className="animate-spin" /> Applying…</>
        ) : (
          <><Zap size={14} /> Apply optimization</>
        )}
      </button>
    </div>
  );
}
