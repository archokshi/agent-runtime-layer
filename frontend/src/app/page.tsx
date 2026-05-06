import { Shell } from "@/components/Shell";
import { OverviewDashboard } from "@/components/OverviewDashboard";
import { getBenchmarkSuiteSummary, getPhase1ExitPackages, getPlatformSummary, getTasks } from "@/lib/api";

export default async function HomePage() {
  const tasks = await getTasks().catch(() => []);
  const platform = await getPlatformSummary().catch(() => null);
  const benchmarks = await getBenchmarkSuiteSummary().catch(() => null);
  const workloadReports = await getPhase1ExitPackages().catch(() => []);
  return (
    <Shell>
      <OverviewDashboard tasks={tasks} platform={platform} benchmarks={benchmarks} workloadReports={workloadReports} />
    </Shell>
  );
}
