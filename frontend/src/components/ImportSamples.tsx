"use client";

import { useState } from "react";
import { Upload } from "lucide-react";
import { browserBaseUrl } from "@/lib/api";

const samples = [
  { label: "Successful coding task", path: "/samples/successful-coding-task.json" },
  { label: "Slow tool-heavy task", path: "/samples/slow-tool-heavy-task.json" },
  { label: "Repeated-context task", path: "/samples/repeated-context-task.json" }
];

export function ImportSamples() {
  const [status, setStatus] = useState<string>("");

  async function importSample(path: string) {
    setStatus("Importing trace...");
    const trace = await fetch(path).then((res) => res.json());
    const response = await fetch(`${browserBaseUrl}/traces/import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(trace)
    });
    if (!response.ok) {
      setStatus(`Import failed: ${response.status}`);
      return;
    }
    const result = await response.json();
    setStatus(`Imported ${result.event_count} events for ${result.task_id}`);
  }

  return (
    <div className="grid gap-3 md:grid-cols-3">
      {samples.map((sample) => (
        <button key={sample.path} onClick={() => importSample(sample.path)} className="inline-flex min-h-24 items-center justify-center gap-2 rounded-lg border border-line bg-white px-4 text-sm font-medium hover:border-mint">
          <Upload size={16} aria-hidden />
          {sample.label}
        </button>
      ))}
      {status ? <p className="md:col-span-3 text-sm text-slate-600">{status}</p> : null}
    </div>
  );
}
