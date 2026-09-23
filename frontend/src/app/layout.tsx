import type { Metadata } from "next";
import "./globals.css";
import { NarrationProvider } from "@/components/narration/provider";
import { AppShell } from "@/components/app-shell";

export const metadata: Metadata = {
  title: "Quantum Learn",
  description: "AI-Based Interactive Quantum Algorithm Learning Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <NarrationProvider>
          <AppShell>{children}</AppShell>
        </NarrationProvider>
      </body>
    </html>
  );
}
