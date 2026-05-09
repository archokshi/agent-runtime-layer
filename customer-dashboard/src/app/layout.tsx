import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Agentium — Agent Performance Dashboard",
  description: "See why your coding agent is slow, expensive, or stuck."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
