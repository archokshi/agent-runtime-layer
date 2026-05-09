import { EvidenceQualityOverview } from "@/components/EvidenceQualityOverview";
import { getEvidenceQuality } from "@/lib/api";

export default async function EvidencePage() {
  const report = await getEvidenceQuality();
  return <EvidenceQualityOverview report={report} />;
}
