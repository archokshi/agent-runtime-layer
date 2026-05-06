"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { browserBaseUrl } from "@/lib/api";

type ImportResponse = {
  task_id: string;
  event_count: number;
};

async function postJson(path: string, body?: unknown) {
  const response = await fetch(`${browserBaseUrl}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`${path} failed with ${response.status}`);
  }
  return response;
}

export function StartDemoButton() {
  const router = useRouter();
  const [status, setStatus] = useState<"idle" | "running" | "failed">("idle");

  async function startDemo() {
    try {
      setStatus("running");
      const trace = await fetch("/samples/golden-coding-agent-demo.json").then((response) => {
        if (!response.ok) {
          throw new Error("Demo trace could not be loaded.");
        }
        return response.json();
      });
      const imported = await postJson("/traces/import", trace).then((response) => response.json() as Promise<ImportResponse>);
      await postJson(`/tasks/${imported.task_id}/optimize-context`);
      await postJson(`/tasks/${imported.task_id}/schedule`);
      await postJson(`/tasks/${imported.task_id}/backend-hints`);
      await postJson("/phase-1-exit/generate");
      router.push(`/tasks/${imported.task_id}`);
      router.refresh();
    } catch (error) {
      console.error(error);
      setStatus("failed");
    }
  }

  return (
    <div>
      <button
        type="button"
        onClick={startDemo}
        disabled={status === "running"}
        className="inline-flex h-11 items-center rounded-md bg-teal-700 px-4 text-sm font-semibold text-white hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-70"
      >
        {status === "running" ? "Starting demo..." : "Start demo"}
      </button>
      {status === "failed" ? (
        <div className="mt-2 text-sm text-red-700">Demo setup failed. Check that the backend is running at {browserBaseUrl}.</div>
      ) : null}
    </div>
  );
}
