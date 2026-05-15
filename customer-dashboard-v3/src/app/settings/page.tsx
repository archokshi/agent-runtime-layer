import { Shell } from "@/components/Shell";
import { SettingsControlPanel } from "@/components/SettingsControlPanel";
import { getAllAnalyses, getSettings, getTasks } from "@/lib/api";

export default async function SettingsPage() {
  const [settings, tasks] = await Promise.all([
    getSettings().catch(() => null),
    getTasks().catch(() => []),
  ]);
  const analyses = await getAllAnalyses(tasks);

  const n = analyses.length;
  const avgInputTokens    = n > 0 ? analyses.reduce((s, a) => s + a.total_input_tokens, 0) / n : 0;
  const avgRepeatedPct    = n > 0 ? analyses.reduce((s, a) => s + a.repeated_context_percent, 0) / n : 0;
  const avgRepeatedTokens = avgInputTokens * (avgRepeatedPct / 100);
  const optimizerSaving   = avgRepeatedTokens * (2.70 / 1_000_000);
  const totalRetries  = analyses.reduce((s, a) => s + a.retry_count, 0);
  const retryWaste    = analyses.reduce((s, a) => {
    const f = a.model_call_count > 0 ? a.retry_count / a.model_call_count : 0;
    return s + a.estimated_total_cost_dollars * f;
  }, 0);
  const highestCost   = n > 0 ? Math.max(...analyses.map(a => a.estimated_total_cost_dollars)) : 0;
  const cacheSaving   = avgRepeatedTokens * (2.70 / 1_000_000);

  const defaults = {
    plan: "free" as const, optimizer_enabled: false, budget_enabled: false,
    memory_enabled: false, max_cost_per_run: 0.10, max_retries: 3,
    enabled_at: null, baseline_avg_tokens: null, baseline_avg_cost: null,
    baseline_avg_retries: null, updated_at: new Date().toISOString(),
  };

  return (
    <Shell>
      <div style={{ maxWidth: 620 }}>
        <div style={{ marginBottom: 20 }}>
          <div className="page-title">Control Plane</div>
          <div className="page-sub">Enable optimizations — each applies from your next agent run.</div>
        </div>
        <SettingsControlPanel
          initial={settings ?? defaults}
          estimates={{ optimizerSaving, totalRetries, retryWaste, highestCost, cacheSaving, repeatedPct: avgRepeatedPct }}
        />
      </div>
    </Shell>
  );
}
