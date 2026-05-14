import { Shell } from "@/components/Shell";
import { SettingsControlPanel } from "@/components/SettingsControlPanel";
import { getAllAnalyses, getSettings, getTasks } from "@/lib/api";

export default async function SettingsPage() {
  const [settings, tasks] = await Promise.all([
    getSettings().catch(() => null),
    getTasks().catch(() => []),
  ]);
  const analyses = await getAllAnalyses(tasks);

  // Compute value estimates from existing run data
  const n = analyses.length;
  const totalInputTokens = analyses.reduce((s, a) => s + a.total_input_tokens, 0);
  const avgInputTokens = n > 0 ? totalInputTokens / n : 0;
  const avgRepeatedPct = n > 0
    ? analyses.reduce((s, a) => s + a.repeated_context_percent, 0) / n
    : 0;
  const avgRepeatedTokens = avgInputTokens * (avgRepeatedPct / 100);

  // Phase 1.7: optimizer saving = repeated tokens × $2.70/MTok (standard - cache rate)
  const optimizerSavingPerRun = avgRepeatedTokens * (2.70 / 1_000_000);

  // Phase 1.8: retry waste + highest run cost
  const totalRetries = analyses.reduce((s, a) => s + a.retry_count, 0);
  const retryWaste = analyses.reduce((s, a) => {
    const fraction = a.model_call_count > 0 ? a.retry_count / a.model_call_count : 0;
    return s + a.estimated_total_cost_dollars * fraction;
  }, 0);
  const highestRunCost = n > 0 ? Math.max(...analyses.map((a) => a.estimated_total_cost_dollars)) : 0;

  // Phase 1.9: cache saving = same as optimizer (repeated tokens × discount)
  const cacheSavingPerRun = avgRepeatedTokens * (2.70 / 1_000_000);

  const defaultSettings = {
    plan: "free" as const,
    optimizer_enabled: false,
    budget_enabled: false,
    memory_enabled: false,
    max_cost_per_run: 0.10,
    max_retries: 3,
    enabled_at: null,
    baseline_avg_tokens: null,
    baseline_avg_cost: null,
    baseline_avg_retries: null,
    updated_at: new Date().toISOString(),
  };

  return (
    <Shell hasData>
      <div className="mx-auto max-w-2xl">
        <SettingsControlPanel
          initial={settings ?? defaultSettings}
          estimates={{
            optimizerSavingPerRun,
            totalRetries,
            retryWaste,
            highestRunCost,
            cacheSavingPerRun,
            repeatedCtxPct: avgRepeatedPct,
          }}
        />
      </div>
    </Shell>
  );
}
