import { TelemetryCorpusOverview } from "@/components/TelemetryCorpusOverview";
import { getTelemetrySummary } from "@/lib/api";

export default async function TelemetryPage() {
  const report = await getTelemetrySummary();
  return <TelemetryCorpusOverview report={report} />;
}
