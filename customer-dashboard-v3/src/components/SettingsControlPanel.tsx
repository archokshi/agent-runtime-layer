"use client";

import { useState } from "react";
import { Zap, Shield, Brain, CheckCircle, AlertCircle, ChevronDown, ChevronUp, Lock } from "lucide-react";
import type { Settings } from "@/lib/types";

const API = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

const PLAN_ORDER = ["free", "pro", "team", "enterprise"] as const;
const GATES: Record<string, string> = {
  optimizer_enabled: "pro",
  budget_enabled:    "team",
  memory_enabled:    "enterprise",
};
const TIER_LABEL: Record<string, string> = {
  pro: "Pro — $49/mo", team: "Team — $149/mo", enterprise: "Enterprise",
};

function canAccess(feature: string, plan: string) {
  return PLAN_ORDER.indexOf(plan as never) >= PLAN_ORDER.indexOf(GATES[feature] as never);
}

type Estimates = {
  optimizerSaving: number; totalRetries: number; retryWaste: number;
  highestCost: number; cacheSaving: number; repeatedPct: number;
};

function Toggle({ on, onChange }: { on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!on)}
      className={`toggle-switch ${on ? "on" : ""}`}
    />
  );
}

function LockedPill({ tier }: { tier: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 5, padding: "5px 10px", borderRadius: 7, background: "var(--surface)", border: "1px solid var(--border)", fontSize: 12, color: "var(--muted)" }}>
      <Lock size={11} /> {TIER_LABEL[tier] ?? tier}
    </div>
  );
}

export function SettingsControlPanel({ initial, estimates }: { initial: Settings; estimates: Estimates }) {
  const [saved, setSaved] = useState<Settings>(initial);
  const [draft, setDraft] = useState({
    optimizer_enabled: initial.optimizer_enabled,
    budget_enabled:    initial.budget_enabled,
    memory_enabled:    initial.memory_enabled,
    max_cost_per_run:  initial.max_cost_per_run,
    max_retries:       initial.max_retries,
    plan:              initial.plan,
  });
  const [saving,  setSaving]  = useState(false);
  const [success, setSuccess] = useState(false);
  const [error,   setError]   = useState("");
  const [devOpen, setDevOpen] = useState(false);

  const dirty =
    draft.optimizer_enabled !== saved.optimizer_enabled ||
    draft.budget_enabled    !== saved.budget_enabled    ||
    draft.memory_enabled    !== saved.memory_enabled    ||
    draft.max_cost_per_run  !== saved.max_cost_per_run  ||
    draft.max_retries       !== saved.max_retries       ||
    draft.plan              !== saved.plan;

  async function save() {
    setSaving(true); setError(""); setSuccess(false);
    try {
      const res = await fetch(`${API}/settings`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(draft),
      });
      if (!res.ok) { const b = await res.json().catch(() => ({})); throw new Error(b.detail || `Error ${res.status}`); }
      const updated: Settings = await res.json();
      setSaved(updated);
      setDraft({ optimizer_enabled: updated.optimizer_enabled, budget_enabled: updated.budget_enabled, memory_enabled: updated.memory_enabled, max_cost_per_run: updated.max_cost_per_run, max_retries: updated.max_retries, plan: updated.plan });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally { setSaving(false); }
  }

  function cancel() {
    setDraft({ optimizer_enabled: saved.optimizer_enabled, budget_enabled: saved.budget_enabled, memory_enabled: saved.memory_enabled, max_cost_per_run: saved.max_cost_per_run, max_retries: saved.max_retries, plan: saved.plan });
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

      {success && (
        <div style={{ display: "flex", alignItems: "center", gap: 8, background: "var(--green-lt)", border: "1px solid #05966920", borderRadius: 10, padding: "11px 14px", fontSize: 13, fontWeight: 500, color: "var(--green)" }}>
          <CheckCircle size={14} /> Settings saved — changes active from your next run.
        </div>
      )}
      {error && (
        <div style={{ display: "flex", alignItems: "center", gap: 8, background: "var(--red-lt)", border: "1px solid #DC262620", borderRadius: 10, padding: "11px 14px", fontSize: 13, fontWeight: 500, color: "var(--red)" }}>
          <AlertCircle size={14} /> {error}
        </div>
      )}

      {/* Phase 1.7 — Optimizer */}
      <div className="toggle-card" style={{ borderTop: "3px solid var(--mint)" }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12, marginBottom: 14 }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
            <div style={{ width: 36, height: 36, borderRadius: 9, background: "var(--mint-lt)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <Zap size={16} color="var(--mint)" />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 15, fontWeight: 600 }}>Context Optimizer</span>
                <span className="badge badge-muted">Phase 1.7</span>
                <span className="badge badge-mint">Pro</span>
              </div>
              <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 3 }}>Strip repeated context automatically on every run</div>
            </div>
          </div>
          {canAccess("optimizer_enabled", draft.plan)
            ? <Toggle on={draft.optimizer_enabled} onChange={v => setDraft(d => ({ ...d, optimizer_enabled: v }))} />
            : <LockedPill tier="pro" />}
        </div>
        {estimates.optimizerSaving > 0 && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <div style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 12px" }}>
              <div className="toggle-val-label">Saving / run</div>
              <div className="toggle-val-num" style={{ color: "var(--mint)" }}>~${estimates.optimizerSaving.toFixed(4)}</div>
            </div>
            <div style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 12px" }}>
              <div className="toggle-val-label">Repeated tokens</div>
              <div className="toggle-val-num" style={{ color: "var(--mint)" }}>{estimates.repeatedPct.toFixed(0)}%</div>
            </div>
          </div>
        )}
        {!canAccess("optimizer_enabled", draft.plan) && (
          <p style={{ marginTop: 10, fontSize: 12, color: "var(--muted)" }}>
            Upgrade to <span style={{ color: "var(--mint)", fontWeight: 600 }}>Pro ($49/mo)</span> to enable automatic context optimization and proof cards per run.
          </p>
        )}
      </div>

      {/* Phase 1.8 — Budget Governor */}
      <div className="toggle-card" style={{ borderTop: "3px solid var(--amber)" }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12, marginBottom: 14 }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
            <div style={{ width: 36, height: 36, borderRadius: 9, background: "var(--amber-lt)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <Shield size={16} color="var(--amber)" />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 15, fontWeight: 600 }}>Budget Governor</span>
                <span className="badge badge-muted">Phase 1.8</span>
                <span className="badge badge-amber">Team</span>
              </div>
              <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 3 }}>Cap cost and retries — hooks block runaway runs</div>
            </div>
          </div>
          {canAccess("budget_enabled", draft.plan)
            ? <Toggle on={draft.budget_enabled} onChange={v => setDraft(d => ({ ...d, budget_enabled: v }))} />
            : <LockedPill tier="team" />}
        </div>
        {(estimates.totalRetries > 0 || estimates.highestCost > 0) && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: draft.budget_enabled && canAccess("budget_enabled", draft.plan) ? 12 : 0 }}>
            {estimates.totalRetries > 0 && (
              <div style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 12px" }}>
                <div className="toggle-val-label">Retries detected</div>
                <div className="toggle-val-num" style={{ color: "var(--amber)" }}>{estimates.totalRetries} <span style={{ fontSize: 12, color: "var(--muted)", fontFamily: "inherit", fontWeight: 400 }}>total</span></div>
                <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>~${estimates.retryWaste.toFixed(4)} wasted</div>
              </div>
            )}
            {estimates.highestCost > 0 && (
              <div style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 12px" }}>
                <div className="toggle-val-label">Highest run cost</div>
                <div className="toggle-val-num" style={{ color: "var(--amber)" }}>${estimates.highestCost.toFixed(4)}</div>
              </div>
            )}
          </div>
        )}
        {canAccess("budget_enabled", draft.plan) && draft.budget_enabled && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: "var(--muted)" }}>Max cost / run ($)</label>
              <input type="number" step="0.01" min="0.01" value={draft.max_cost_per_run}
                onChange={e => setDraft(d => ({ ...d, max_cost_per_run: parseFloat(e.target.value) || 0.10 }))}
                style={{ background: "var(--bg)", border: "1px solid var(--border2)", borderRadius: 8, padding: "8px 12px", fontSize: 13, fontFamily: "var(--mono)", color: "var(--ink)", outline: "none" }} />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: "var(--muted)" }}>Max retries / task</label>
              <input type="number" step="1" min="1" value={draft.max_retries}
                onChange={e => setDraft(d => ({ ...d, max_retries: parseInt(e.target.value) || 3 }))}
                style={{ background: "var(--bg)", border: "1px solid var(--border2)", borderRadius: 8, padding: "8px 12px", fontSize: 13, fontFamily: "var(--mono)", color: "var(--ink)", outline: "none" }} />
            </div>
          </div>
        )}
        {!canAccess("budget_enabled", draft.plan) && (
          <p style={{ marginTop: 10, fontSize: 12, color: "var(--muted)" }}>
            Upgrade to <span style={{ color: "var(--mint)", fontWeight: 600 }}>Team ($149/mo)</span> to enforce cost caps and retry limits.
          </p>
        )}
      </div>

      {/* Phase 1.9 — Context Memory */}
      <div className="toggle-card" style={{ borderTop: "3px solid var(--border2)", opacity: .85 }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12, marginBottom: 14 }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
            <div style={{ width: 36, height: 36, borderRadius: 9, background: "var(--surface)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <Brain size={16} color="var(--muted)" />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 15, fontWeight: 600 }}>Context Memory</span>
                <span className="badge badge-muted">Phase 1.9</span>
                <span className="badge badge-blue">Enterprise</span>
              </div>
              <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 3 }}>Cache stable context at $0.30/MTok vs $3.00/MTok</div>
            </div>
          </div>
          <LockedPill tier="enterprise" />
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 10 }}>
          <div style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 12px" }}>
            <div className="toggle-val-label">Saving / run</div>
            <div className="toggle-val-num" style={{ color: "var(--muted2)" }}>~${estimates.cacheSaving.toFixed(4)}</div>
          </div>
          <div style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 12px" }}>
            <div className="toggle-val-label">Cache discount</div>
            <div className="toggle-val-num" style={{ color: "var(--muted2)" }}>10×</div>
          </div>
        </div>
        <p style={{ fontSize: 12, color: "var(--muted)" }}>
          Upgrade to <span style={{ color: "var(--blue)", fontWeight: 600 }}>Enterprise</span> — context memory compounds every run.
        </p>
      </div>

      {/* Save */}
      {dirty && (
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <button className="btn btn-primary" onClick={save} disabled={saving}>
            {saving ? "Saving…" : "Save changes"}
          </button>
          <button style={{ fontSize: 13, color: "var(--muted)", background: "none", border: "none", cursor: "pointer" }} onClick={cancel}>Cancel</button>
        </div>
      )}

      {/* Developer plan override */}
      <div style={{ border: "1px dashed var(--border2)", borderRadius: 10, overflow: "hidden" }}>
        <button
          type="button"
          onClick={() => setDevOpen(v => !v)}
          style={{ width: "100%", padding: "11px 14px", display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: 12, fontWeight: 600, color: "var(--muted)", background: "var(--bg)", border: "none", cursor: "pointer" }}
        >
          Developer — plan override (alpha testing)
          {devOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
        {devOpen && (
          <div style={{ padding: 14, borderTop: "1px dashed var(--border2)", background: "var(--card)" }}>
            <div style={{ fontSize: 12, color: "var(--muted2)" }}>Set plan to unlock features locally. In production, set via billing.</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 7, marginTop: 10 }}>
              {(["free", "pro", "team", "enterprise"] as const).map(p => (
                <button key={p} className={`plan-pill ${draft.plan === p ? "active" : ""}`}
                  onClick={() => setDraft(d => ({ ...d, plan: p }))}>
                  {p === "free" ? "Free" : p === "pro" ? "Pro" : p === "team" ? "Team" : "Enterprise"}
                </button>
              ))}
            </div>
            <div style={{ marginTop: 8, fontSize: 12, color: "var(--muted)" }}>
              Current: <strong style={{ color: "var(--ink)" }}>{draft.plan}</strong>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
