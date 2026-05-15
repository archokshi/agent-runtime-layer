import Link from "next/link";
import { Shell } from "@/components/Shell";
import { getAllAnalyses, getBudgetSummary, getContextMemorySummary, getPhase1ExitPackages, getSettings, getTasks } from "@/lib/api";
import { TrendingUp, Settings } from "lucide-react";

export default async function OverviewPage() {
  const tasks = await getTasks().catch(() => []);
  const [reports, budgetSummary, memSummary, currentSettings] = await Promise.all([
    getPhase1ExitPackages(),
    getBudgetSummary(),
    getContextMemorySummary(),
    getSettings().catch(() => null),
  ]);
  const analyses = await getAllAnalyses(tasks);

  const n = analyses.length;
  const latestReport = reports?.[0] ?? null;

  const totalModelMs = analyses.reduce((s, a) => s + a.model_time_ms, 0);
  const totalToolMs  = analyses.reduce((s, a) => s + a.tool_time_ms, 0);
  const totalIdleMs  = analyses.reduce((s, a) => s + a.orchestration_idle_ms, 0);
  const totalMs = totalModelMs + totalToolMs + totalIdleMs;
  const modelPct = totalMs > 0 ? (totalModelMs / totalMs) * 100 : 0;
  const toolPct  = totalMs > 0 ? (totalToolMs  / totalMs) * 100 : 0;
  const idlePct  = totalMs > 0 ? (totalIdleMs  / totalMs) * 100 : 0;
  const avgModelSec = n > 0 ? (totalModelMs / n / 1000).toFixed(1) : "0";
  const avgToolSec  = n > 0 ? (totalToolMs  / n / 1000).toFixed(1) : "0";
  const avgIdleSec  = n > 0 ? (totalIdleMs  / n / 1000).toFixed(1) : "0";

  const ctxProfile = latestReport?.workload_evaluation_package?.context_kv_reuse_profile as Record<string, unknown> | undefined;
  const repeatedPct = typeof ctxProfile?.avg_repeated_context_percent === "number"
    ? ctxProfile.avg_repeated_context_percent as number
    : n > 0 ? analyses.reduce((s, a) => s + a.repeated_context_percent, 0) / n : 0;

  const successTasks = tasks.filter(t => t.status === "completed");
  const failedTasks  = tasks.filter(t => t.status === "failed");
  const successRate  = tasks.length > 0 ? (successTasks.length / tasks.length) * 100 : 0;
  const successAnalyses = analyses.filter(a => tasks.find(t => t.task_id === a.task_id)?.status === "completed");
  const avgCost = successAnalyses.length > 0
    ? successAnalyses.reduce((s, a) => s + a.estimated_total_cost_dollars, 0) / successAnalyses.length : null;

  const totalRetries = analyses.reduce((s, a) => s + a.retry_count, 0);
  const retryWaste = analyses.reduce((s, a) => {
    const f = a.model_call_count > 0 ? a.retry_count / a.model_call_count : 0;
    return s + a.estimated_total_cost_dollars * f;
  }, 0);
  const highCostRun = n > 0 ? Math.max(...analyses.map(a => a.estimated_total_cost_dollars)) : 0;
  const avgInputTokens    = n > 0 ? analyses.reduce((s, a) => s + a.total_input_tokens, 0) / n : 0;
  const avgRepeatedTokens = avgInputTokens * (repeatedPct / 100);
  const cacheSavingPerRun = avgRepeatedTokens * (2.70 / 1_000_000);

  // Gains since enabled
  const enabledAt = currentSettings?.enabled_at ?? null;
  const anyEnabled = currentSettings
    ? currentSettings.optimizer_enabled || currentSettings.budget_enabled || currentSettings.memory_enabled
    : false;
  const postAnalyses = enabledAt
    ? analyses.filter(a => { const t = tasks.find(tk => tk.task_id === a.task_id); return t?.started_at && t.started_at > enabledAt; })
    : [];
  const postN = postAnalyses.length;
  const baselineTokens  = currentSettings?.baseline_avg_tokens ?? null;
  const baselineCost    = currentSettings?.baseline_avg_cost   ?? null;
  const baselineRetries = currentSettings?.baseline_avg_retries ?? null;
  const postAvgTokens  = postN > 0 ? postAnalyses.reduce((s, a) => s + a.total_input_tokens, 0) / postN : null;
  const postAvgCost    = postN > 0 ? postAnalyses.reduce((s, a) => s + a.estimated_total_cost_dollars, 0) / postN : null;
  const postAvgRetries = postN > 0 ? postAnalyses.reduce((s, a) => s + a.retry_count, 0) / postN : null;
  const showGains = anyEnabled && enabledAt && postN > 0 && baselineTokens !== null;

  const h2Count = analyses.filter(a => a.repeated_context_percent >= 15).length;
  const h1Count = analyses.filter(a => a.total_task_duration_ms > 0 && a.tool_time_ms / a.total_task_duration_ms >= 0.25).length;
  const h6Count = analyses.filter(a => a.retry_count > 0).length;

  if (tasks.length === 0) {
    return (
      <Shell>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "80px 0", textAlign: "center" }}>
          <h1 className="page-title">No traces yet</h1>
          <p style={{ fontSize: 13, color: "var(--muted)", marginTop: 8, maxWidth: 400 }}>
            Install the SDK and run your agent to see performance data.
          </p>
          <div style={{ marginTop: 24, display: "flex", gap: 10 }}>
            <Link href="/settings" className="btn btn-primary">Go to Settings</Link>
          </div>
        </div>
      </Shell>
    );
  }

  // Total savings (hero banner)
  const totalSaved = postN > 0 && baselineCost && postAvgCost
    ? (baselineCost - postAvgCost) * postN : null;

  return (
    <Shell runCount={tasks.length}>
      <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

        <div>
          <div className="page-title">Overview</div>
          <div className="page-sub">{tasks.length} agent runs traced · live data</div>
        </div>

        {/* Hero banner — savings */}
        {showGains && totalSaved !== null ? (
          <div className="hero-banner">
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, letterSpacing: ".6px", textTransform: "uppercase", color: "var(--mint)", marginBottom: 6 }}>
                ⚡ Optimizations active — {Math.floor((Date.now() - new Date(enabledAt!).getTime()) / 86400000)} day(s)
              </div>
              <div className="hero-num">
                ${totalSaved.toFixed(2)}{" "}
                <span style={{ fontSize: 18, fontWeight: 500, color: "var(--muted)", fontFamily: "inherit" }}>saved so far</span>
              </div>
              <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 5 }}>
                Based on {postN} run{postN !== 1 ? "s" : ""} since you enabled the Control Plane
              </div>
            </div>
            <div style={{ display: "flex", gap: 0 }}>
              {[
                { val: postAvgTokens && baselineTokens ? `−${(((baselineTokens - postAvgTokens) / baselineTokens) * 100).toFixed(0)}%` : "—", label: "tokens" },
                { val: postAvgCost && baselineCost ? `−${(((baselineCost - postAvgCost) / baselineCost) * 100).toFixed(0)}%` : "—", label: "cost/run" },
                { val: postAvgRetries !== null && baselineRetries && baselineRetries > 0 ? `−${(((baselineRetries - postAvgRetries) / baselineRetries) * 100).toFixed(0)}%` : "—", label: "retries" },
              ].map(({ val, label }) => (
                <div key={label} style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "0 20px", borderLeft: "1px solid var(--border)" }}>
                  <span style={{ fontSize: 22, fontWeight: 700, fontFamily: "var(--mono)", color: "var(--green)", letterSpacing: "-.5px" }}>{val}</span>
                  <span style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>{label}</span>
                </div>
              ))}
            </div>
          </div>
        ) : anyEnabled && enabledAt && postN === 0 ? (
          <div style={{ background: "var(--mint-lt)", border: "1px solid var(--mint-md)", borderRadius: 12, padding: "14px 18px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <p style={{ fontSize: 13, fontWeight: 500, color: "var(--mint)" }}>⚡ Optimizations active — gains card will appear after your next agent run.</p>
            <Link href="/settings" style={{ fontSize: 12, fontWeight: 600, color: "var(--mint)" }}>View settings →</Link>
          </div>
        ) : !anyEnabled ? (
          <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "14px 18px", display: "flex", alignItems: "center", justifyContent: "space-between", boxShadow: "var(--shadow)" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Settings size={15} color="var(--muted)" />
              <p style={{ fontSize: 13, color: "var(--muted)" }}>Optimizations not enabled yet — turn them on to see gains here.</p>
            </div>
            <Link href="/settings" className="btn btn-primary btn-sm">Open Control Plane →</Link>
          </div>
        ) : null}

        {/* 3 metric cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,minmax(0,1fr))", gap: 12 }}>
          <div className="metric-card">
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
              <div className="section-label">Repeated tokens</div>
            </div>
            <div className="metric-val" style={{ color: repeatedPct >= 30 ? "var(--red)" : "var(--ink)" }}>
              {repeatedPct.toFixed(1)}<span style={{ fontSize: 18, opacity: .6, fontFamily: "inherit" }}>%</span>
            </div>
            <div className={`metric-delta ${repeatedPct >= 30 ? "delta-bad" : "delta-neu"}`}>
              {repeatedPct >= 30 ? "↑" : "~"} of input tokens re-sent every call
            </div>
          </div>
          <div className="metric-card">
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
              <div className="section-label">Cost / run</div>
            </div>
            <div className="metric-val">{avgCost !== null ? `$${avgCost.toFixed(4)}` : "—"}</div>
            <div className="metric-delta delta-neu">{successAnalyses.length} successful runs</div>
          </div>
          <div className="metric-card">
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
              <div className="section-label">Success rate</div>
            </div>
            <div className="metric-val" style={{ color: successRate >= 80 ? "var(--green)" : successRate >= 50 ? "var(--amber)" : "var(--red)" }}>
              {tasks.length > 0 ? successRate.toFixed(0) : "—"}<span style={{ fontSize: 18, opacity: .6, fontFamily: "inherit" }}>%</span>
            </div>
            <div className="metric-delta delta-neu">{successTasks.length} of {tasks.length} runs</div>
          </div>
        </div>

        {/* Gains since enabled (detailed) */}
        {showGains && postAvgTokens !== null && postAvgCost !== null && baselineCost !== null && baselineTokens !== null && (
          <div className="gains-card">
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 13, fontWeight: 600 }}>
                <TrendingUp size={14} color="var(--green)" />
                Gains since you enabled optimizations
              </div>
              <span className="badge badge-green">{postN} run{postN !== 1 ? "s" : ""} · ✓ Verified</span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10 }}>
              {[
                { label: "Avg input tokens", before: `${(baselineTokens/1000).toFixed(1)}k → ${(postAvgTokens/1000).toFixed(1)}k`, pct: (((baselineTokens - postAvgTokens) / baselineTokens) * 100) },
                { label: "Avg cost / run",   before: `$${baselineCost.toFixed(4)} → $${postAvgCost.toFixed(4)}`, pct: (((baselineCost - postAvgCost) / baselineCost) * 100) },
                { label: "Avg retries",      before: baselineRetries !== null ? `${baselineRetries.toFixed(1)} → ${postAvgRetries?.toFixed(1) ?? "—"}` : "—", pct: baselineRetries && baselineRetries > 0 && postAvgRetries !== null ? (((baselineRetries - postAvgRetries) / baselineRetries) * 100) : null },
              ].map(({ label, before, pct }) => (
                <div key={label} style={{ background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 9, padding: "12px 14px" }}>
                  <div className="section-label">{label}</div>
                  <div className="gains-before">{before}</div>
                  <div className="gains-val">{pct !== null ? `−${pct.toFixed(0)}%` : "—"}</div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 12, display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: 12, color: "var(--muted)" }}>
              <span>Enabled {new Date(enabledAt!).toLocaleDateString()} · {postN} run{postN !== 1 ? "s" : ""} after optimizations applied</span>
              <Link href="/settings" style={{ color: "var(--mint)", fontWeight: 600 }}>Manage controls →</Link>
            </div>
          </div>
        )}

        {/* Time split + Patterns */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2,minmax(0,1fr))", gap: 12 }}>
          {n > 0 && (
            <div className="card">
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                <div className="card-title">Where does time go?</div>
                <span className="badge badge-amber">~ Estimated</span>
              </div>
              {[
                { label: "Model inference", pct: modelPct, avg: `${avgModelSec}s`, color: "var(--mint)", warn: false },
                { label: "Tool wait",       pct: toolPct,  avg: `${avgToolSec}s`, color: "var(--amber)", warn: toolPct >= 40 },
                { label: "Idle / CPU",      pct: idlePct,  avg: `${avgIdleSec}s`, color: "var(--border2)", warn: false },
              ].map(({ label, pct, avg, color, warn }) => (
                <div key={label} style={{ marginBottom: 10 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 5 }}>
                    <span style={{ color: warn ? "var(--amber)" : "var(--muted)", fontWeight: warn ? 600 : 400 }}>{label}{warn ? " ⚠" : ""}</span>
                    <span style={{ fontWeight: 600, fontFamily: "var(--mono)", color: warn ? "var(--amber)" : "var(--ink)" }}>{pct.toFixed(0)}% · {avg}</span>
                  </div>
                  <div className="split-bar">
                    <div style={{ width: `${Math.max(pct, 0)}%`, background: color, height: "100%", borderRadius: "99px" }} />
                  </div>
                </div>
              ))}
              {toolPct >= 40 && (
                <div style={{ marginTop: 12, padding: "10px 12px", background: "var(--amber-lt)", border: "1px solid #D9770620", borderRadius: 8, display: "flex", justifyContent: "space-between" }}>
                  <span style={{ fontSize: 12, color: "var(--amber)" }}>⚠ Tool wait using {toolPct.toFixed(0)}% of elapsed time</span>
                  <Link href="/bottlenecks" style={{ fontSize: 12, fontWeight: 600, color: "var(--amber)" }}>See bottlenecks →</Link>
                </div>
              )}
            </div>
          )}

          <div className="card">
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
              <div className="card-title">Detected patterns</div>
              <Link href="/recommendations" style={{ fontSize: 12, fontWeight: 600, color: "var(--mint)" }}>Full analysis →</Link>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                { label: "Repeated context waste", count: h2Count, desc: `${repeatedPct.toFixed(1)}% of input tokens re-sent`, href: "/context", priority: h2Count > n / 2 ? "high" : "med" },
                { label: "Tool wait blocking",     count: h1Count, desc: `Tool windows avg ${avgToolSec}s while model idle`, href: "/bottlenecks", priority: h1Count > n / 2 ? "high" : "med" },
                { label: "Retry overhead",         count: h6Count, desc: `${(totalRetries / Math.max(n, 1)).toFixed(1)} retries/run avg`, href: "/cost", priority: h6Count > n / 3 ? "med" : "low" },
              ].map(({ label, count, desc, href, priority }) => (
                <div key={label} className={`pattern-card ${priority}`}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{label}</span>
                    <span style={{ fontSize: 11, color: "var(--muted)" }}>{count}/{n} runs</span>
                  </div>
                  <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 3 }}>{desc}</div>
                  <Link href={href} style={{ fontSize: 11, fontWeight: 600, color: "var(--mint)", marginTop: 5, display: "inline-block" }}>Inspect →</Link>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Quick links */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,minmax(0,1fr))", gap: 10 }}>
          {[
            { href: "/bottlenecks",     title: "Bottlenecks",    sub: "Time + cost split" },
            { href: "/context",         title: "Context",         sub: "Which tokens repeat?" },
            { href: "/cost",            title: "Cost",            sub: "Per task · per failure" },
            { href: "/settings",        title: "Control Plane",  sub: "Manage optimizations" },
          ].map(({ href, title, sub }) => (
            <Link key={href} href={href} className="quick-link">
              <div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{title}</div>
                <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>{sub}</div>
              </div>
              <span style={{ color: href === "/settings" ? "var(--mint)" : "var(--muted2)", fontWeight: href === "/settings" ? 600 : 400 }}>→</span>
            </Link>
          ))}
        </div>

      </div>
    </Shell>
  );
}
