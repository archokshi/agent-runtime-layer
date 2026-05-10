import type { AnalysisReport, BackendAwareReport, BenchmarkSuiteSummary, BlueprintPreview, ContextOptimizationReport, EvidenceCampaignReport, EvidenceQualityReport, HardwareAnalysisReport, OptimizationReport, Phase1ExitPackage, Phase2HandoffPackage, PlatformSummary, SchedulerReport, SiliconBlueprintReport, Task, TelemetryCorpusReport, TraceCorpusReport, TraceEvent, TraceReplayReport, ValidationReport } from "./types";

const serverBaseUrl = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";
export const browserBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${serverBaseUrl}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

export function getTasks() {
  return getJson<Task[]>("/tasks");
}

export function getTask(taskId: string) {
  return getJson<Task>(`/tasks/${taskId}`);
}

export function getEvents(taskId: string) {
  return getJson<TraceEvent[]>(`/tasks/${taskId}/events`);
}

export function getAnalysis(taskId: string) {
  return getJson<AnalysisReport>(`/tasks/${taskId}/analysis`);
}

export function getBlueprint(taskId: string) {
  return getJson<BlueprintPreview>(`/tasks/${taskId}/blueprint`);
}

export function getOptimizations(taskId: string) {
  return getJson<OptimizationReport>(`/tasks/${taskId}/optimizations`);
}

export function getValidation(taskId: string) {
  return getJson<ValidationReport>(`/tasks/${taskId}/validation`);
}

export async function getOptimizedContext(taskId: string) {
  const response = await fetch(`${serverBaseUrl}/tasks/${taskId}/optimized-context`, { cache: "no-store" });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<ContextOptimizationReport>;
}

export async function getScheduleReport(taskId: string) {
  const response = await fetch(`${serverBaseUrl}/tasks/${taskId}/schedule`, { cache: "no-store" });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<SchedulerReport>;
}

export async function getBackendHints(taskId: string) {
  const response = await fetch(`${serverBaseUrl}/tasks/${taskId}/backend-hints`, { cache: "no-store" });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<BackendAwareReport>;
}

export async function getHardwareAnalysis(taskId: string) {
  const response = await fetch(`${serverBaseUrl}/tasks/${taskId}/hardware-analysis`, { cache: "no-store" });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<HardwareAnalysisReport>;
}

export function getSiliconBlueprintReports() {
  return getJson<SiliconBlueprintReport[]>("/blueprints");
}

export async function getTraceReplayReports(blueprintId: string) {
  const response = await fetch(`${serverBaseUrl}/blueprints/${blueprintId}/replays`, { cache: "no-store" });
  if (response.status === 404) {
    return [];
  }
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<TraceReplayReport[]>;
}

export function getPlatformSummary() {
  return getJson<PlatformSummary>("/platform/summary");
}

export function getBenchmarkSuiteSummary() {
  return getJson<BenchmarkSuiteSummary>("/benchmarks/summary");
}

export function getPhase1ExitPackages() {
  return getJson<Phase1ExitPackage[]>("/phase-1-exit");
}

export function getTraceCorpusSummary() {
  return getJson<TraceCorpusReport>("/corpus/summary");
}

export function getEvidenceQuality() {
  return getJson<EvidenceQualityReport>("/evidence/quality");
}

export function getEvidenceCampaignReports() {
  return getJson<EvidenceCampaignReport[]>("/evidence-campaign");
}

export function getPhase2HandoffPackages() {
  return getJson<Phase2HandoffPackage[]>("/phase-2-handoff");
}

export function getTelemetrySummary() {
  return getJson<TelemetryCorpusReport>("/telemetry/summary");
}
