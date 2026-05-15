import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Agentium",
  description: "See why your coding agent is slow, expensive, or stuck — then fix it.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
