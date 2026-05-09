import { Shell } from "@/components/Shell";
import { ContextInspector } from "@/components/ContextInspector";
import { getAnalysis, getOptimizedContext, getPhase1ExitPackages, getTasks } from "@/lib/api";

async function optional<T>(promise: Promise<T>): Promise<T | null> {
  try { return await promise; } catch { return null; }
}

export default async function ContextPage() {
  const tasks = await getTasks().catch(() => []);
  const workloadReports = await getPhase1ExitPackages().catch(() => []);
  const latestReport = workloadReports[0] ?? null;

  // Fetch analyses for all tasks in parallel
  const analyses = (
    await Promise.all(tasks.map((t) => optional(getAnalysis(t.task_id))))
  ).filter((a): a is Awaited<ReturnType<typeof getAnalysis>> => a !== null);

  // Find task with highest repeated context % to feature
  const sorted = [...analyses].sort((a, b) => b.repeated_context_percent - a.repeated_context_percent);
  const featuredTaskId = sorted[0]?.task_id ?? tasks[0]?.task_id ?? null;
  const contextReport = featuredTaskId ? await optional(getOptimizedContext(featuredTaskId)) : null;

  return (
    <Shell>
      <ContextInspector
        tasks={tasks}
        analyses={analyses}
        contextReport={contextReport}
        latestReport={latestReport}
      />
    </Shell>
  );
}
