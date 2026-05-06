import Link from "next/link";
import type { Task } from "@/lib/types";

export function TaskList({ tasks }: { tasks: Task[] }) {
  if (tasks.length === 0) {
    return (
      <div className="border border-line bg-white p-6">
        <p className="text-sm text-slate-600">No traces imported yet.</p>
      </div>
    );
  }
  return (
    <div className="grid gap-3">
      {tasks.map((task) => (
        <Link key={task.task_id} href={`/tasks/${task.task_id}`} className="block rounded-lg border border-line bg-white p-4 hover:border-mint">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold">{task.goal}</h2>
              <p className="mt-1 text-xs text-slate-500">{task.task_id}</p>
            </div>
            <span className="rounded-md bg-panel px-2 py-1 text-xs font-medium capitalize">{task.status}</span>
          </div>
          {task.summary ? <p className="mt-3 text-sm text-slate-600">{task.summary}</p> : null}
        </Link>
      ))}
    </div>
  );
}
