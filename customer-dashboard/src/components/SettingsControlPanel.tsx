"use client";

import { useState } from "react";
import { Zap, Shield, Brain, Lock, CheckCircle, AlertCircle, ChevronDown, ChevronUp } from "lucide-react";
import type { Settings } from "@/lib/types";

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

const PLAN_ORDER = ["free", "pro", "team", "enterprise"];

const PLAN_GATES: Record<string, string> = {
  optimizer_enabled: "pro",
  budget_enabled: "team",
  memory_enabled: "enterprise",
};

const TIER_LABELS: Record<string, string> = {
  free: "Free",
  pro: "Pro — $49/mo",
  team: "Team — $149/mo",
  enterprise: "Enterprise",
};

function canAccess(feature: string, plan: string): boolean {
  const required = PLAN_GATES[feature];
  return PLAN_ORDER.indexOf(plan) >= PLAN_ORDER.indexOf(required);
}

type Estimates = {
  optimizerSavingPerRun: number;
  totalRetries: number;
  retryWaste: number;
  highestRunCost: number;
  cacheSavingPerRun: number;
  repeatedCtxPct: number;
};

export function SettingsControlPanel({
  initial,
  estimates,
}: {
  initial: Settings;
  estimates: Estimates;
}) {
  const [settings, setSettings] = useState<Settings>(initial);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [showDev, setShowDev] = useState(false);

  // Local draft state
  const [draft, setDraft] = useState({
    optimizer_enabled: initial.optimizer_enabled,
    budget_enabled: initial.budget_enabled,
    memory_enabled: initial.memory_enabled,
    max_cost_per_run: initial.max_cost_per_run,
    max_retries: initial.max_retries,
    plan: initial.plan,
  });

  const isDirty =
    draft.optimizer_enabled !== settings.optimizer_enabled ||
    draft.budget_enabled !== settings.budget_enabled ||
    draft.memory_enabled !== settings.memory_enabled ||
    draft.max_cost_per_run !== settings.max_cost_per_run ||
    draft.max_retries !== settings.max_retries ||
    draft.plan !== settings.plan;

  async function handleSave() {
    setSaving(true);
    setSaved(false);
    setError("");
    try {
      const res = await fetch(`${apiBase}/settings`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(draft),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error ${res.status}`);
      }
      const updated: Settings = await res.json();
      setSettings(updated);
      setDraft({
        optimizer_enabled: updated.optimizer_enabled,
        budget_enabled: updated.budget_enabled,
        memory_enabled: updated.memory_enabled,
        max_cost_per_run: updated.max_cost_per_run,
        max_retries: updated.max_retries,
        plan: updated.plan,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setSaving(false);
    }
  }

  function Toggle({ feature, value, onChange }: { feature: string; value: boolean; onChange: (v: boolean) => void }) {
    const locked = !canAccess(feature, draft.plan);
    const required = PLAN_GATES[feature];
    return (
      <div className="flex items-center gap-3">
        {locked ? (
          <div className="flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-400">
            <Lock size={11} />
            <span>{TIER_LABELS[required]}</span>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => onChange(!value)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
              value ? "bg-mint" : "bg-slate-200"
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
                value ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
        )}
        <span className={`text-sm font-semibold ${locked ? "text-slate-400" : value ? "text-teal-700" : "text-slate-500"}`}>
          {locked ? "Locked" : value ? "ON" : "OFF"}
        </span>
      </div>
    );
  }

  return (
    <div className="grid gap-5">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-ink">Control Plane</h1>
        <p className="mt-1 text-sm text-slate-500">
          Enable optimizations — each applies automatically from your next agent run.
        </p>
      </div>

      {/* Saved / error banner */}
      {saved && (
        <div className="flex items-center gap-2 rounded-xl border border-teal-200 bg-teal-50 px-4 py-3 text-sm font-medium text-teal-800">
          <CheckCircle size={15} className="flex-shrink-0" />
          Settings saved — changes active from your next run.
        </div>
      )}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          <AlertCircle size={15} className="flex-shrink-0" />
          {error}
        </div>
      )}

      {/* Phase 1.7 — Context Optimizer */}
      <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-teal-50 border border-teal-200">
              <Zap size={16} className="text-mint" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-semibold text-ink">Context Optimizer</h2>
                <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs font-semibold text-slate-500">Phase 1.7</span>
              </div>
              <p className="text-sm text-slate-500 mt-0.5">
                Strip repeated context automatically on every run
              </p>
            </div>
          </div>
          <Toggle
            feature="optimizer_enabled"
            value={draft.optimizer_enabled}
            onChange={(v) => setDraft((d) => ({ ...d, optimizer_enabled: v }))}
          />
        </div>

        {/* Value estimate */}
        {estimates.optimizerSavingPerRun > 0 && (
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="rounded-lg border border-teal-100 bg-teal-50 p-3">
              <p className="text-xs text-teal-700 font-medium">Estimated saving</p>
              <p className="text-xl font-bold text-teal-700 mt-0.5">
                ~${estimates.optimizerSavingPerRun.toFixed(4)}<span className="text-sm font-normal">/run</span>
              </p>
            </div>
            <div className="rounded-lg border border-teal-100 bg-teal-50 p-3">
              <p className="text-xs text-teal-700 font-medium">Repeated tokens</p>
              <p className="text-xl font-bold text-teal-700 mt-0.5">
                {estimates.repeatedCtxPct.toFixed(0)}%<span className="text-sm font-normal"> of input</span>
              </p>
            </div>
          </div>
        )}

        {!canAccess("optimizer_enabled", draft.plan) && (
          <p className="mt-3 text-xs text-slate-400">
            Upgrade to <span className="font-semibold text-mint">Pro ($49/mo)</span> to enable automatic context optimization and see proof cards per run.
          </p>
        )}
      </section>

      {/* Phase 1.8 — Budget Governor */}
      <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-amber-50 border border-amber-200">
              <Shield size={16} className="text-amber-600" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-semibold text-ink">Budget Governor</h2>
                <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs font-semibold text-slate-500">Phase 1.8</span>
              </div>
              <p className="text-sm text-slate-500 mt-0.5">
                Stop runaway costs and retry spirals automatically
              </p>
            </div>
          </div>
          <Toggle
            feature="budget_enabled"
            value={draft.budget_enabled}
            onChange={(v) => setDraft((d) => ({ ...d, budget_enabled: v }))}
          />
        </div>

        {/* Value estimate */}
        {(estimates.totalRetries > 0 || estimates.highestRunCost > 0) && (
          <div className="mt-4 grid grid-cols-2 gap-3">
            {estimates.totalRetries > 0 && (
              <div className="rounded-lg border border-amber-100 bg-amber-50 p-3">
                <p className="text-xs text-amber-700 font-medium">Retries detected</p>
                <p className="text-xl font-bold text-amber-700 mt-0.5">
                  {estimates.totalRetries}<span className="text-sm font-normal"> total</span>
                </p>
                <p className="text-xs text-amber-600 mt-0.5">~${estimates.retryWaste.toFixed(4)} wasted</p>
              </div>
            )}
            {estimates.highestRunCost > 0 && (
              <div className="rounded-lg border border-amber-100 bg-amber-50 p-3">
                <p className="text-xs text-amber-700 font-medium">Highest run cost</p>
                <p className="text-xl font-bold text-amber-700 mt-0.5">
                  ${estimates.highestRunCost.toFixed(4)}
                </p>
                <p className="text-xs text-amber-600 mt-0.5">uncapped today</p>
              </div>
            )}
          </div>
        )}

        {/* Budget inputs — shown when toggle is accessible */}
        {canAccess("budget_enabled", draft.plan) && draft.budget_enabled && (
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Max cost / run ($)</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={draft.max_cost_per_run}
                onChange={(e) => setDraft((d) => ({ ...d, max_cost_per_run: parseFloat(e.target.value) || 0.10 }))}
                className="w-full rounded-lg border border-line bg-panel px-3 py-2 text-sm font-mono text-ink focus:border-mint focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Max retries / task</label>
              <input
                type="number"
                step="1"
                min="1"
                value={draft.max_retries}
                onChange={(e) => setDraft((d) => ({ ...d, max_retries: parseInt(e.target.value) || 3 }))}
                className="w-full rounded-lg border border-line bg-panel px-3 py-2 text-sm font-mono text-ink focus:border-mint focus:outline-none"
              />
            </div>
          </div>
        )}

        {!canAccess("budget_enabled", draft.plan) && (
          <p className="mt-3 text-xs text-slate-400">
            Upgrade to <span className="font-semibold text-mint">Team ($149/mo)</span> to enforce cost caps and retry limits across all your runs.
          </p>
        )}
      </section>

      {/* Phase 1.9 — Context Memory */}
      <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-blue-50 border border-blue-200">
              <Brain size={16} className="text-blue-600" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-semibold text-ink">Context Memory</h2>
                <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs font-semibold text-slate-500">Phase 1.9</span>
              </div>
              <p className="text-sm text-slate-500 mt-0.5">
                Cache stable context at $0.30/MTok instead of $3.00/MTok
              </p>
            </div>
          </div>
          <Toggle
            feature="memory_enabled"
            value={draft.memory_enabled}
            onChange={(v) => setDraft((d) => ({ ...d, memory_enabled: v }))}
          />
        </div>

        {/* Value estimate */}
        {estimates.cacheSavingPerRun > 0 && (
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="rounded-lg border border-blue-100 bg-blue-50 p-3">
              <p className="text-xs text-blue-700 font-medium">Estimated saving</p>
              <p className="text-xl font-bold text-blue-700 mt-0.5">
                ~${estimates.cacheSavingPerRun.toFixed(4)}<span className="text-sm font-normal">/run</span>
              </p>
            </div>
            <div className="rounded-lg border border-blue-100 bg-blue-50 p-3">
              <p className="text-xs text-blue-700 font-medium">Cache discount</p>
              <p className="text-xl font-bold text-blue-700 mt-0.5">
                10×<span className="text-sm font-normal"> cheaper</span>
              </p>
            </div>
          </div>
        )}

        {!canAccess("memory_enabled", draft.plan) && (
          <p className="mt-3 text-xs text-slate-400">
            <span className="font-semibold text-mint">Enterprise</span> feature — context memory compounds every run, creating your optimization history and moat.
          </p>
        )}
      </section>

      {/* Save button */}
      {isDirty && (
        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-lg bg-mint px-6 py-2.5 text-sm font-semibold text-white hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {saving ? "Saving…" : "Save changes"}
          </button>
          <button
            onClick={() => setDraft({
              optimizer_enabled: settings.optimizer_enabled,
              budget_enabled: settings.budget_enabled,
              memory_enabled: settings.memory_enabled,
              max_cost_per_run: settings.max_cost_per_run,
              max_retries: settings.max_retries,
              plan: settings.plan,
            })}
            className="text-sm text-slate-400 hover:text-ink transition-colors"
          >
            Cancel
          </button>
        </div>
      )}

      {/* Developer section — plan override for alpha testing */}
      <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50">
        <button
          type="button"
          onClick={() => setShowDev((v) => !v)}
          className="flex w-full items-center justify-between px-4 py-3 text-xs font-semibold text-slate-400 hover:text-slate-600 transition-colors"
        >
          <span>Developer — plan override (alpha testing)</span>
          {showDev ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
        {showDev && (
          <div className="border-t border-dashed border-slate-200 px-4 pb-4">
            <p className="mt-3 text-xs text-slate-400 mb-2">
              Set your plan to unlock features for local testing. In production this is set via billing.
            </p>
            <div className="flex flex-wrap gap-2">
              {(["free", "pro", "team", "enterprise"] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setDraft((d) => ({ ...d, plan: p }))}
                  className={`rounded-full border px-3 py-1 text-xs font-semibold transition-colors ${
                    draft.plan === p
                      ? "border-mint bg-teal-50 text-teal-700"
                      : "border-slate-200 bg-white text-slate-500 hover:border-mint hover:text-mint"
                  }`}
                >
                  {p === "free" ? "Free" : p === "pro" ? "Pro" : p === "team" ? "Team" : "Enterprise"}
                </button>
              ))}
            </div>
            <p className="mt-2 text-xs text-slate-400">
              Current plan: <span className="font-semibold text-ink">{draft.plan}</span>
            </p>
          </div>
        )}
      </div>

    </div>
  );
}
