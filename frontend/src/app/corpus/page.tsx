import { TraceCorpusOverview } from "@/components/TraceCorpusOverview";
import { getTraceCorpusSummary } from "@/lib/api";

export default async function CorpusPage() {
  const report = await getTraceCorpusSummary();
  return <TraceCorpusOverview report={report} />;
}
