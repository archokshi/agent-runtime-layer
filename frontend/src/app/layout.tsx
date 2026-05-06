import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Agent Runtime Layer",
  description: "Self-hosted profiler for coding agents"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
