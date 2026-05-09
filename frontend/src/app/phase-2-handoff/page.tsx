import { Phase2HandoffDashboard } from "@/components/Phase2HandoffDashboard";
import { getPhase2HandoffPackages } from "@/lib/api";

export default async function Phase2HandoffPage() {
  const packages = await getPhase2HandoffPackages();
  return <Phase2HandoffDashboard initialPackages={packages} />;
}
