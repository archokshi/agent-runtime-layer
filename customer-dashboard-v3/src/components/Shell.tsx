"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutGrid, Music2, Settings, Activity, Search, DollarSign, Star } from "lucide-react";
import { LiveRefresher } from "./LiveRefresher";

const NAV_MAIN = [
  { href: "/overview",  label: "Overview",        icon: LayoutGrid },
  { href: "/runs",      label: "Runs",            icon: Music2 },
  { href: "/settings",  label: "Settings",        icon: Settings },
];

const NAV_ANALYSIS = [
  { href: "/bottlenecks",     label: "Bottlenecks",     icon: Activity },
  { href: "/context",         label: "Context",          icon: Search },
  { href: "/cost",            label: "Cost",             icon: DollarSign },
  { href: "/recommendations", label: "Recommendations",  icon: Star },
];

export function Shell({ children, runCount }: { children: React.ReactNode; runCount?: number }) {
  const pathname = usePathname();

  const isActive = (href: string) =>
    href === "/runs" ? pathname.startsWith("/runs") : pathname === href;

  const isRunDetail = pathname.startsWith("/runs/") && pathname.length > 6;

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-hex" />
          <span className="logo-name">Agentium</span>
        </div>

        <div className="nav-section">
          <div className="nav-group-label">Main</div>
          {NAV_MAIN.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={`nav-item ${isActive(href) ? "active" : ""}`}
            >
              <Icon size={15} />
              {label}
              {label === "Runs" && runCount !== undefined && (
                <span className="nav-badge">{runCount}</span>
              )}
            </Link>
          ))}
        </div>

        <hr className="nav-divider" />

        <div className="nav-section">
          <div className="nav-group-label">Analysis</div>
          {NAV_ANALYSIS.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={`nav-item ${isActive(href) ? "active" : ""}`}
            >
              <Icon size={15} />
              {label}
            </Link>
          ))}
        </div>

        <div className="sidebar-footer">
          <div className="live-dot" />
          <span style={{ fontSize: 12, color: "var(--muted)" }}>Live · ↺ 30s</span>
        </div>
      </aside>

      {/* Main area */}
      <div className="main-area">
        {/* Topbar */}
        <div className="topbar">
          {isRunDetail ? (
            <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, color: "var(--muted)" }}>
              <Link href="/runs" style={{ color: "var(--muted)" }}>Runs</Link>
              <span style={{ color: "var(--muted2)" }}>›</span>
              <span style={{ color: "var(--ink)", fontWeight: 500 }}>Run detail</span>
            </div>
          ) : (
            <div />
          )}
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Link href="/settings">
              <span className="badge badge-muted" style={{ cursor: "pointer" }}>Free plan</span>
            </Link>
            <Link href="/settings" className="btn btn-primary btn-sm">
              Upgrade to Pro
            </Link>
          </div>
        </div>

        {/* Page content */}
        <main className="page-content">
          {children}
        </main>
      </div>

      <LiveRefresher intervalMs={30000} />
    </div>
  );
}
