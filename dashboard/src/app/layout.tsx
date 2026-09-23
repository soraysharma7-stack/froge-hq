import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FROGÉ HQ — Virtual AI Organization",
  description:
    "FROGÉ HQ — a virtual AI organization headquarters. Maya, your Chief AI Orchestrator, leads a team of AI agents that research, plan, build, and verify real work.",
};

export const viewport: Viewport = {
  themeColor: "#0a0a0f",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
