import Link from "next/link";
import { Shell } from "@/components/Shell";
import { getTasks } from "@/lib/api";
import {
  Hexagon, ArrowRight, CheckCircle, Clock, Search,
  DollarSign, Zap, Package, Code2, Terminal, Bot, TrendingDown
} from "lucide-react";

export default async function LandingPage() {
  // Check if there are existing runs to show a "go to dashboard" prompt
  const tasks = await getTasks().catch(() => []);
  const hasData = tasks.length > 0;

  return (
    <Shell hasData={false}>
      <div className="grid gap-16">

        {/* Existing data banner */}
        {hasData && (
          <div className="flex items-center justify-between rounded-xl border border-teal-200 bg-teal-50 px-5 py-3 shadow-sm">
            <div className="flex items-center gap-3">
              <span className="relative flex h-2.5 w-2.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-mint opacity-75" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-mint" />
              </span>
              <p className="text-sm font-medium text-teal-800">
                {tasks.length} agent run{tasks.length !== 1 ? "s" : ""} already traced — your dashboard is ready.
              </p>
            </div>
            <Link
              href="/overview"
              className="inline-flex items-center gap-2 rounded-lg bg-mint px-4 py-2 text-sm font-semibold text-white hover:opacity-90 transition-opacity"
            >
              Open dashboard <ArrowRight size={14} />
            </Link>
          </div>
        )}

        {/* Hero */}
        <section className="pt-6 text-center">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-mint shadow-lg">
            <Hexagon size={32} className="text-white" fill="currentColor" />
          </div>
          <h1 className="mx-auto max-w-3xl text-5xl font-extrabold leading-tight tracking-tight text-ink">
            See why your coding agent is slow, expensive, or stuck.
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-slate-600">
            Agentium is a self-hosted profiler that captures every model call, tool execution,
            and retry in your coding agent run — then tells you exactly where time and money
            are going, and what to fix first.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/overview"
              className="inline-flex h-12 items-center gap-2 rounded-lg bg-mint px-7 text-sm font-semibold text-white shadow-sm hover:opacity-90 transition-opacity"
            >
              {hasData ? "Open dashboard" : "See live demo"} <ArrowRight size={16} />
            </Link>
            <Link
              href="/import"
              className="inline-flex h-12 items-center gap-2 rounded-lg border border-line bg-white px-6 text-sm font-semibold text-ink hover:bg-panel transition-colors"
            >
              Import a trace
            </Link>
          </div>
          <div className="mt-5 flex flex-wrap items-center justify-center gap-5 text-xs text-slate-400">
            <span className="flex items-center gap-1.5"><CheckCircle size={13} className="text-mint" /> Self-hosted</span>
            <span className="flex items-center gap-1.5"><CheckCircle size={13} className="text-mint" /> Private — no data leaves your machine</span>
            <span className="flex items-center gap-1.5"><CheckCircle size={13} className="text-mint" /> Works with Codex, Claude Code, Cursor, custom agents</span>
          </div>
        </section>

        {/* Who is this for */}
        <section>
          <div className="mb-6 text-center">
            <h2 className="text-2xl font-bold text-ink">Who is this for?</h2>
            <p className="mt-2 text-slate-500">
              Built for developers and teams who run coding agents and want to understand what they are actually doing.
            </p>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {[
              {
                icon: Code2,
                title: "Agent developers",
                body: "Using Codex, Claude Code, or Cursor and wondering why your runs are slow, expensive, or unpredictable.",
              },
              {
                icon: Bot,
                title: "Engineering teams",
                body: "Building custom AI agents with the Anthropic, OpenAI, or any Python SDK and need visibility into what agents actually do in production.",
              },
              {
                icon: DollarSign,
                title: "Cost-aware teams",
                body: "Watching API costs grow month over month and needing to understand exactly what is driving the spend and where to cut.",
              },
            ].map(({ icon: Icon, title, body }) => (
              <div key={title} className="rounded-xl border border-line bg-white p-6 shadow-sm">
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50">
                  <Icon size={20} className="text-mint" />
                </div>
                <h3 className="font-semibold text-ink">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* The problem */}
        <section className="rounded-2xl border border-line bg-white p-8 shadow-sm">
          <h2 className="mb-3 text-2xl font-bold text-ink">The problem Agentium solves</h2>
          <p className="max-w-2xl text-slate-600 leading-relaxed">
            Coding agents are not simple prompt → response calls. They run in loops — calling models,
            waiting on tools, retrying failures, and building up context on every step.
            Without visibility, you are flying blind.
          </p>
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            {[
              "Why did that run take 90 seconds?",
              "Why did the same task cost $0.12 yesterday and $0.04 today?",
              "Why does my agent keep retrying the same failing test?",
              "Am I re-sending 40,000 tokens of context on every single call?",
            ].map((q) => (
              <div key={q} className="flex items-start gap-3 rounded-lg border border-red-100 bg-red-50 px-4 py-3">
                <span className="mt-0.5 font-bold text-red-400">✗</span>
                <p className="text-sm font-medium text-red-800">{q}</p>
              </div>
            ))}
          </div>
          <p className="mt-6 font-semibold text-mint text-lg">Agentium answers all of these.</p>
        </section>

        {/* What you get */}
        <section>
          <div className="mb-6 text-center">
            <h2 className="text-2xl font-bold text-ink">What you get</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {[
              {
                icon: Clock,
                title: "Timeline waterfall",
                body: "See every model call, tool wait, and retry laid out in time. Spot exactly where seconds go with a single glance.",
                href: "/runs",
              },
              {
                icon: Search,
                title: "Context inspector",
                body: "See exactly which tokens you re-send on every call. Stable context — system prompt, tool definitions, repo summary — is the primary cost driver.",
                href: "/context",
              },
              {
                icon: TrendingDown,
                title: "Bottleneck detection",
                body: "Find out if tool wait, repeated context, or retry overhead is your real bottleneck — backed by data across every run you've traced.",
                href: "/bottlenecks",
              },
              {
                icon: DollarSign,
                title: "Cost explorer",
                body: "Cost per successful task, cost per failure, and where retries are burning your budget — with a before/after comparison when you optimize.",
                href: "/cost",
              },
              {
                icon: Zap,
                title: "Ranked recommendations",
                body: "Exactly what to fix and in what order, ranked by impact × confidence ÷ effort. Every recommendation shows its evidence.",
                href: "/recommendations",
              },
              {
                icon: Package,
                title: "Works with your stack",
                body: "Native hooks for Codex, Claude Code, and Cursor. Custom agents via the Python SDK. Import completed traces as JSON.",
                href: "/import",
              },
            ].map(({ icon: Icon, title, body, href }) => (
              <Link
                key={title}
                href={href}
                className="rounded-xl border border-line bg-white p-5 shadow-sm hover:border-mint hover:shadow-md transition-all"
              >
                <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-teal-50">
                  <Icon size={18} className="text-mint" />
                </div>
                <h3 className="font-semibold text-ink">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-500">{body}</p>
                <span className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-mint">
                  Open <ArrowRight size={11} />
                </span>
              </Link>
            ))}
          </div>
        </section>

        {/* Get started */}
        <section className="rounded-2xl border border-mint bg-teal-50 p-8">
          <h2 className="mb-6 text-center text-2xl font-bold text-ink">Get started in 3 steps</h2>
          <div className="grid gap-4 md:grid-cols-3">
            {[
              {
                n: "1", title: "Install",
                code: "pip install agent-runtime-layer\n# or: docker compose up",
                sub: "Works on laptop, dev server, or CI runner.",
              },
              {
                n: "2", title: "Run your agent",
                code: "# Codex, Claude Code, Cursor:\nagent-runtime integrations install codex\n\n# Custom agent:\nfrom agent_runtime_layer import AgentRuntimeTracer",
                sub: "SDK captures every model call, tool, file, and retry automatically.",
              },
              {
                n: "3", title: "See results",
                code: "open http://localhost:4000/overview",
                sub: "Traces appear in real time. Dashboard refreshes every 30 seconds.",
              },
            ].map(({ n, title, code, sub }) => (
              <div key={n} className="rounded-xl border border-teal-200 bg-white p-5 shadow-sm">
                <div className="mb-3 grid h-8 w-8 place-items-center rounded-full bg-mint text-sm font-bold text-white">{n}</div>
                <h3 className="font-semibold text-ink">{title}</h3>
                <pre className="mt-3 rounded-lg bg-ink p-3 text-xs text-teal-300 whitespace-pre-wrap overflow-x-auto">{code}</pre>
                <p className="mt-3 text-xs text-slate-500">{sub}</p>
              </div>
            ))}
          </div>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/overview"
              className="inline-flex h-11 items-center gap-2 rounded-lg bg-mint px-6 text-sm font-semibold text-white shadow-sm hover:opacity-90 transition-opacity"
            >
              {hasData ? "Open my dashboard" : "Open dashboard"} <ArrowRight size={16} />
            </Link>
            <Link
              href="/import"
              className="inline-flex h-11 items-center gap-2 rounded-lg border border-line bg-white px-5 text-sm font-semibold text-ink hover:bg-panel transition-colors"
            >
              Import a trace
            </Link>
          </div>
          <div className="mt-5 flex flex-wrap items-center justify-center gap-5 text-sm text-slate-500">
            <span className="flex items-center gap-2"><Terminal size={14} className="text-mint" /> Codex</span>
            <span className="flex items-center gap-2"><Bot size={14} className="text-mint" /> Claude Code</span>
            <span className="flex items-center gap-2"><Code2 size={14} className="text-mint" /> Cursor Agent</span>
            <span className="flex items-center gap-2"><Package size={14} className="text-mint" /> Custom SDK</span>
          </div>
        </section>

      </div>
    </Shell>
  );
}
