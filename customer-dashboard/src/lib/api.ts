import type { AnalysisReport, ContextOptimizationReport, OptimizationReport, Phase1ExitPackage, PlatformSummary, Task, TraceEvent } from "./types";

const serverBase = process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${serverBase}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json();
}

async function optional<T>(p: Promise<T>): Promise<T | null> {
  try { return await p; } catch { return null; }
}

export const getTasks = () => get<Task[]>("/tasks");
export const getTask = (id: string) => get<Task>(`/tasks/${id}`);
export const getEvents = (id: string) => get<TraceEvent[]>(`/tasks/${id}/events`);
export const getAnalysis = (id: string) => get<AnalysisReport>(`/tasks/${id}/analysis`);
export const getOptimizations = (id: string) => get<OptimizationReport>(`/tasks/${id}/optimizations`);
export const getOptimizedContext = (id: string) => optional(get<ContextOptimizationReport>(`/tasks/${id}/optimized-context`));
export const getPlatformSummary = () => optional(get<PlatformSummary>("/platform/summary"));
export const getPhase1ExitPackages = () => optional(get<Phase1ExitPackage[]>("/phase-1-exit"));

export async function getAllAnalyses(tasks: Task[]): Promise<AnalysisReport[]> {
  const results = await Promise.all(tasks.map((t) => optional(getAnalysis(t.task_id))));
  return results.filter((r): r is AnalysisReport => r !== null);
}
