import { Shell } from "@/components/Shell";
import { RecommendationsPage } from "@/components/RecommendationsPage";
import { getPhase1ExitPackages, getTasks } from "@/lib/api";

export default async function RecommendationsRoute() {
  const [tasks, workloadReports] = await Promise.all([
    getTasks().catch(() => []),
    getPhase1ExitPackages().catch(() => [] as Awaited<ReturnType<typeof getPhase1ExitPackages>>),
  ]);
  const latestReport = workloadReports[0] ?? null;

  return (
    <Shell>
      <RecommendationsPage latestReport={latestReport} tasks={tasks} />
    </Shell>
  );
}
