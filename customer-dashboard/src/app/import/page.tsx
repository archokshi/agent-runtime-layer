import Link from "next/link";
import { Shell } from "@/components/Shell";
import { ArrowRight, Terminal, Bot, Code2, Package, Upload } from "lucide-react";

export default function ImportPage() {
  return (
    <Shell hasData={false}>
      <div className="grid gap-8 max-w-3xl mx-auto pt-8">
        <div>
          <h1 className="text-2xl font-bold text-ink">Get your agent data into Agentium</h1>
          <p className="mt-2 text-slate-500">Three ways to capture traces. Pick the one that fits your setup.</p>
        </div>

        {/* Native integrations */}
        <section>
          <h2 className="mb-4 font-semibold text-ink">Native integrations — zero code changes</h2>
          <div className="grid gap-3">
            {[
              {
                icon: Terminal, title: "Codex", badge: "Hooks",
                steps: [
                  "Start Agentium: docker compose up",
                  "Install hooks: agent-runtime integrations install codex --repo .",
                  "Run Codex normally — traces appear automatically",
                ],
              },
              {
                icon: Bot, title: "Claude Code", badge: "Hooks",
                steps: [
                  "Start Agentium: docker compose up",
                  "Install hooks: agent-runtime integrations install claude-code --repo .",
                  "Run Claude Code — every turn is captured as a trace",
                ],
              },
              {
                icon: Code2, title: "Cursor Agent", badge: "CLI",
                steps: [
                  "Start Agentium: docker compose up",
                  "Install capture helper: agent-runtime integrations install cursor",
                  "Pipe output: cursor agent run | agent-runtime capture cursor",
                ],
              },
            ].map(({ icon: Icon, title, badge, steps }) => (
              <div key={title} className="rounded-xl border border-line bg-white p-5 shadow-sm">
                <div className="flex items-center gap-3 mb-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-50">
                    <Icon size={18} className="text-mint" />
                  </div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-ink">{title}</h3>
                    <span className="rounded-full border border-line bg-panel px-2 py-0.5 text-xs font-medium text-slate-500">{badge}</span>
                  </div>
                </div>
                <ol className="space-y-2">
                  {steps.map((step, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <span className="mt-0.5 grid h-4 w-4 flex-shrink-0 place-items-center rounded-full bg-teal-50 text-xs font-bold text-mint">{i + 1}</span>
                      <code className="text-slate-700 bg-slate-50 rounded px-1.5 py-0.5 text-xs">{step}</code>
                    </li>
                  ))}
                </ol>
              </div>
            ))}
          </div>
        </section>

        {/* Python SDK */}
        <section>
          <h2 className="mb-4 font-semibold text-ink">
            <Package size={16} className="inline mr-2 text-mint" />
            Custom agent — Python SDK
          </h2>
          <div className="rounded-xl border border-line bg-white p-5 shadow-sm">
            <pre className="rounded-lg bg-ink p-4 text-xs text-teal-300 overflow-x-auto">{`pip install agent-runtime-layer

from agent_runtime_layer import AgentRuntimeTracer

tracer = AgentRuntimeTracer(project_id="my-project")

with tracer.task(goal="fix the auth bug") as task:
    with tracer.model_call(model="claude-3-5-sonnet") as span:
        response = my_llm_call(prompt)
        span.finish(input_tokens=50000, output_tokens=800)

    with tracer.tool_call(tool_name="bash") as span:
        result = subprocess.run(["pytest"])
        span.finish(exit_code=result.returncode)

    task.finish(success=True)`}</pre>
            <p className="mt-3 text-xs text-slate-400">Full SDK docs at <a href="http://localhost:3000" target="_blank" rel="noopener noreferrer" className="text-mint hover:underline">localhost:3000</a></p>
          </div>
        </section>

        {/* Import JSON */}
        <section>
          <h2 className="mb-4 font-semibold text-ink">
            <Upload size={16} className="inline mr-2 text-mint" />
            Import a completed trace file
          </h2>
          <div className="rounded-xl border border-line bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-600 mb-4">Have a trace JSON file already? Import it directly into Agentium.</p>
            <a
              href="http://localhost:3000/import"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-lg border border-mint bg-teal-50 px-4 py-2 text-sm font-semibold text-mint hover:bg-teal-100 transition-colors"
            >
              Open import tool <ArrowRight size={14} />
            </a>
            <p className="mt-3 text-xs text-slate-400">Opens the import tool in the dev dashboard (localhost:3000)</p>
          </div>
        </section>

        <div className="flex items-center gap-3">
          <Link href="/" className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-4 py-2 text-sm font-medium text-ink hover:border-mint hover:text-mint transition-colors">
            ← Back to overview
          </Link>
        </div>
      </div>
    </Shell>
  );
}
