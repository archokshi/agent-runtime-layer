import { Shell } from "@/components/Shell";
import { CostExplorer } from "@/components/CostExplorer";
import { getAnalysis, getBenchmarkSuiteSummary, getPhase1ExitPackages, getPlatformSummary, getTasks } from "@/lib/api";

async function optional<T>(promise: Promise<T>): Promise<T | null> {
  try { return await promise; } catch { return null; }
}

export default async function CostPage() {
  const tasks = await getTasks().catch(() => []);
  const [platform, benchmarks, workloadReports] = await Promise.all([
    getPlatformSummary().catch(() => null),
    getBenchmarkSuiteSummary().catch(() => null),
    getPhase1ExitPackages().catch(() => [] as Awaited<ReturnType<typeof getPhase1ExitPackages>>),
  ]);
  const latestReport = workloadReports[0] ?? null;

  // Fetch analyses for all tasks in parallel
  const analyses = (
    await Promise.all(tasks.map((t) => optional(getAnalysis(t.task_id))))
  ).filter((a): a is Awaited<ReturnType<typeof getAnalysis>> => a !== null);

  return (
    <Shell>
      <CostExplorer
        tasks={tasks}
        analyses={analyses}
        platform={platform}
        latestReport={latestReport}
        benchmarks={benchmarks}
      />
    </Shell>
  );
}
