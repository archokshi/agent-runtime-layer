import Link from "next/link";
import { NavLink } from "./NavLink";
import { LiveRefresher } from "./LiveRefresher";
import {
  Gauge, ListTree, TrendingDown, ScanSearch,
  Wallet, ListChecks, Upload, Hexagon, Settings
} from "lucide-react";

export function Shell({ children, hasData = true }: { children: React.ReactNode; hasData?: boolean }) {
  return (
    <div className="min-h-screen bg-panel">
      <header className="sticky top-0 z-10 border-b border-line bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-3">
          <Link href="/" className="flex items-center gap-2">
            <Hexagon size={22} className="text-mint" fill="currentColor" aria-hidden />
            <span className="text-lg font-bold tracking-tight text-ink">Agentium</span>
          </Link>

          {hasData && (
            <nav className="flex flex-wrap items-center gap-1.5">
              {/* Primary — the journey */}
              <NavLink href="/overview"><Gauge size={14} aria-hidden />Overview</NavLink>
              <NavLink href="/runs"><ListTree size={14} aria-hidden />Runs</NavLink>

              {/* Divider */}
              <span className="h-4 w-px bg-slate-200 mx-0.5" aria-hidden />

              {/* Deep dive */}
              <NavLink href="/bottlenecks"><TrendingDown size={14} aria-hidden />Bottlenecks</NavLink>
              <NavLink href="/context"><ScanSearch size={14} aria-hidden />Context</NavLink>
              <NavLink href="/cost"><Wallet size={14} aria-hidden />Cost</NavLink>
              <NavLink href="/recommendations"><ListChecks size={14} aria-hidden />Recommendations</NavLink>
              <NavLink href="/import"><Upload size={14} aria-hidden />Import</NavLink>

              {/* Divider */}
              <span className="h-4 w-px bg-slate-200 mx-0.5" aria-hidden />

              {/* Control plane */}
              <NavLink href="/settings"><Settings size={14} aria-hidden />Settings</NavLink>
            </nav>
          )}

          <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
            <span className="flex items-center gap-1">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-mint opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-mint" />
              </span>
              Live
            </span>
            <span className="text-slate-300">·</span>
            <span>↺ 30s</span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-5 py-6">
        {children}
      </main>

      <LiveRefresher intervalMs={30000} />
    </div>
  );
}
