import Link from "next/link";
import { ActivitySquare, BarChart3, ClipboardCheck, Database, FileText, Gauge, GitBranch, ListChecks, ListTree, RadioTower, ScanSearch, TrendingDown, Wallet, Upload } from "lucide-react";

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
          <Link href="/" className="flex items-center gap-2 text-lg font-semibold">
            <ActivitySquare size={22} aria-hidden />
            Agent Runtime Layer
          </Link>
          <div className="flex flex-wrap items-center justify-end gap-2">
            <Link href="/" className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-panel">
              <Gauge size={16} aria-hidden />
              Overview
            </Link>
            <Link href="/runs" className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-panel">
              <ListTree size={16} aria-hidden />
              Runs
            </Link>
            <Link href="/bottlenecks" className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-panel">
              <TrendingDown size={16} aria-hidden />
              Bottlenecks
            </Link>
            <Link href="/context" className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-panel">
              <ScanSearch size={16} aria-hidden />
              Context
            </Link>
            <Link href="/cost" className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-panel">
              <Wallet size={16} aria-hidden />
              Cost
            </Link>
            <Link href="/recommendations" className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-panel">
              <ListChecks size={16} aria-hidden />
              Recommendations
            </Link>
            <Link href="/benchmarks" className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-panel">
              <BarChart3 size={16} aria-hidden />
              Benchmarks
            </Link>
            <Link href="/corpus" className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-panel">
              <Database size={16} aria-hidden />
              Corpus
            </Link>
            <Link href="/telemetry" className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-panel">
              <RadioTower size={16} aria-hidden />
              Telemetry
            </Link>
            <Link href="/evidence" className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-panel">
              <ListChecks size={16} aria-hidden />
              Evidence
            </Link>
            <Link href="/evidence-campaign" className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-panel">
              <ClipboardCheck size={16} aria-hidden />
              Campaign
            </Link>
            <Link href="/phase-2-handoff" className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-panel">
              <GitBranch size={16} aria-hidden />
              Handoff
            </Link>
            <Link href="/workload-report" className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-panel">
              <FileText size={16} aria-hidden />
              Workload Report
            </Link>
            <Link href="/advanced" className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-panel">
              <ActivitySquare size={16} aria-hidden />
              Advanced
            </Link>
            <Link href="/import" className="inline-flex h-9 items-center gap-2 rounded-md border border-line px-3 text-sm font-medium hover:bg-panel">
              <Upload size={16} aria-hidden />
              Import
            </Link>
          </div>
        </div>
      </header>
      <div className="mx-auto max-w-7xl px-5 py-6">{children}</div>
    </main>
  );
}
