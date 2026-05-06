import { ImportSamples } from "@/components/ImportSamples";
import { Shell } from "@/components/Shell";

export default function ImportPage() {
  return (
    <Shell>
      <div className="mb-5">
        <p className="text-sm font-medium text-mint">Sample traces</p>
        <h1 className="mt-1 text-3xl font-semibold">Import</h1>
      </div>
      <ImportSamples />
    </Shell>
  );
}
