import { Shell } from "@/components/Shell";
import { BottlenecksPage } from "@/components/BottlenecksPage";
import { getAnalysis, getPhase1ExitPackages, getTasks } from "@/lib/api";

async function optional<T>(promise: Promise<T>): Promise<T | null> {
  try { return await promise; } catch { return null; }
}

export default async function BottlenecksRoute() {
  const tasks = await getTasks().catch(() => []);
  const workloadReports = await getPhase1ExitPackages().catch(() => []);
  const latestReport = workloadReports[0] ?? null;

  // Fetch analyses for all tasks in parallel
  const analyses = (
    await Promise.all(tasks.map((t) => optional(getAnalysis(t.task_id))))
  ).filter((a): a is Awaited<ReturnType<typeof getAnalysis>> => a !== null);

  return (
    <Shell>
      <BottlenecksPage tasks={tasks} analyses={analyses} latestReport={latestReport} />
    </Shell>
  );
}
