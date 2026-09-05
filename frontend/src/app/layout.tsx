import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Quantum Learn",
  description:
    "AI-Based Interactive Quantum Algorithm Learning Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
