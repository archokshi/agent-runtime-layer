import Link from "next/link";
import { Activity, Gauge, GitBranch, Layers } from "lucide-react";
import { Shell } from "@/components/Shell";

export default function AdvancedPage() {
  const cards = [
    {
      title: "Backend-aware hints",
      body: "Prefix overlap, cache locality, queue-depth hints, and prefill/decode classification.",
      href: "/platform",
      icon: Gauge,
    },
    {
      title: "Hardware telemetry",
      body: "Imported GPU, memory, queue, cache, prefill, and decode symptoms correlated with agent spans.",
      href: "/platform",
      icon: Activity,
    },
    {
      title: "Silicon Blueprint",
      body: "Workload profile, bottleneck map, memory hierarchy recommendations, and primitive ranking.",
      href: "/blueprints",
      icon: GitBranch,
    },
    {
      title: "Replay projections",
      body: "Projection-only runtime and backend scenarios for planning validation experiments.",
      href: "/blueprints",
      icon: Layers,
    },
  ];

  return (
    <Shell>
      <section className="rounded-md border border-line bg-white p-6">
        <div className="text-sm font-semibold text-teal-700">Advanced evidence</div>
        <h1 className="mt-1 text-3xl font-semibold">Backend, Telemetry, Blueprint, and Replay</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
          These views are useful after developers understand basic traces, bottlenecks, and recommendations. They do not claim real backend control, hardware simulation, or measured hardware speedup.
        </p>
      </section>
      <section className="mt-5 grid gap-3 md:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <Link key={card.title} href={card.href} className="min-h-44 rounded-md border border-line bg-white p-5 hover:border-teal-600">
              <Icon size={22} aria-hidden className="text-teal-700" />
              <div className="mt-3 font-semibold">{card.title}</div>
              <p className="mt-2 text-sm leading-6 text-muted">{card.body}</p>
            </Link>
          );
        })}
      </section>
    </Shell>
  );
}
