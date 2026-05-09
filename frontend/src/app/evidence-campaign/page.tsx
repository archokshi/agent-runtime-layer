import { EvidenceCampaignDashboard } from "@/components/EvidenceCampaignDashboard";
import { getEvidenceCampaignReports } from "@/lib/api";

export default async function EvidenceCampaignPage() {
  const reports = await getEvidenceCampaignReports();
  return <EvidenceCampaignDashboard initialReports={reports} />;
}
