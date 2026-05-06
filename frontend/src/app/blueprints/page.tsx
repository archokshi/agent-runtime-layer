import { Shell } from "@/components/Shell";
import { SiliconBlueprintEngine } from "@/components/SiliconBlueprintEngine";
import { getSiliconBlueprintReports, getTraceReplayReports } from "@/lib/api";

export default async function BlueprintsPage() {
  const reports = await getSiliconBlueprintReports();
  const replayReports = reports[0] ? await getTraceReplayReports(reports[0].blueprint_id) : [];

  return (
    <Shell>
      <SiliconBlueprintEngine initialReports={reports} initialReplayReports={replayReports} />
    </Shell>
  );
}
