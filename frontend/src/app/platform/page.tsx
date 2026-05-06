import { PlatformOverview } from "@/components/PlatformOverview";
import { Shell } from "@/components/Shell";
import { getPlatformSummary } from "@/lib/api";

export default async function PlatformPage() {
  const summary = await getPlatformSummary();

  return (
    <Shell>
      <PlatformOverview summary={summary} />
    </Shell>
  );
}
