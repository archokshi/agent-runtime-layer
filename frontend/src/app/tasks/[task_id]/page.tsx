import { BottleneckReport } from "@/components/BottleneckReport";
import { BackendAwareRuntimeReport } from "@/components/BackendAwareRuntimeReport";
import { EventTable } from "@/components/EventTable";
import { HardwareAwareRuntimeReport } from "@/components/HardwareAwareRuntimeReport";
import { ExecutionGraph } from "@/components/ExecutionGraph";
import { OptimizationRecommendations } from "@/components/OptimizationRecommendations";
import { OptimizationExecutorReport } from "@/components/OptimizationExecutorReport";
import { RuntimeSchedulerReport } from "@/components/RuntimeSchedulerReport";
import { Shell } from "@/components/Shell";
import { TaskSummary } from "@/components/TaskSummary";
import { Timeline } from "@/components/Timeline";
import { ValidationReport } from "@/components/ValidationReport";
import { getAnalysis, getBackendHints, getBlueprint, getEvents, getHardwareAnalysis, getOptimizations, getOptimizedContext, getScheduleReport, getTask, getValidation } from "@/lib/api";

async function optional<T>(promise: Promise<T>): Promise<T | null> {
  try {
    return await promise;
  } catch {
    return null;
  }
}

export default async function TaskPage({ params }: { params: Promise<{ task_id: string }> }) {
  const { task_id } = await params;
  const [task, events, analysis] = await Promise.all([
    getTask(task_id),
    getEvents(task_id),
    getAnalysis(task_id)
  ]);
  const [blueprint, optimizations, validation, optimizedContext, scheduleReport, backendHints, hardwareAnalysis] = await Promise.all([
    optional(getBlueprint(task_id)),
    optional(getOptimizations(task_id)),
    optional(getValidation(task_id)),
    optional(getOptimizedContext(task_id)),
    optional(getScheduleReport(task_id)),
    optional(getBackendHints(task_id)),
    optional(getHardwareAnalysis(task_id))
  ]);

  return (
    <Shell>
      <div className="grid gap-5">
        <TaskSummary task={task} events={events} analysis={analysis} />
        <Timeline events={events} />
        <ExecutionGraph events={events} />
        <ValidationReport validation={validation} />
        <OptimizationRecommendations optimizations={optimizations} />
        <OptimizationExecutorReport taskId={task_id} initialReport={optimizedContext} />
        <RuntimeSchedulerReport taskId={task_id} initialReport={scheduleReport} />
        <BackendAwareRuntimeReport taskId={task_id} initialReport={backendHints} />
        <HardwareAwareRuntimeReport report={hardwareAnalysis} />
        <BottleneckReport analysis={analysis} blueprint={blueprint} />
        <EventTable events={events} />
      </div>
    </Shell>
  );
}
