import { BenchmarkSuiteOverview } from "@/components/BenchmarkSuiteOverview";
import { getBenchmarkSuiteSummary } from "@/lib/api";

export default async function BenchmarksPage() {
  const summary = await getBenchmarkSuiteSummary();
  return <BenchmarkSuiteOverview summary={summary} />;
}
