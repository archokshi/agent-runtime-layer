import { Shell } from "@/components/Shell";
import { TaskList } from "@/components/TaskList";
import { getTasks } from "@/lib/api";

export default async function RunsPage() {
  const tasks = await getTasks().catch(() => []);
  return (
    <Shell>
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-teal-700">Traced agent runs</p>
          <h1 className="mt-1 text-3xl font-semibold">Runs</h1>
          <p className="mt-2 text-sm text-muted">Open a run to inspect execution graph, events, bottlenecks, recommendations, and evidence.</p>
        </div>
      </div>
      <TaskList tasks={tasks} />
    </Shell>
  );
}
