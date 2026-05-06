import { Phase1ExitDashboard } from "@/components/Phase1ExitDashboard";
import { Shell } from "@/components/Shell";
import { getPhase1ExitPackages } from "@/lib/api";

export default async function Phase1ExitPage() {
  const packages = await getPhase1ExitPackages();

  return (
    <Shell>
      <Phase1ExitDashboard initialPackages={packages} />
    </Shell>
  );
}
