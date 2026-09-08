"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { useState } from "react";
import { BrandMark } from "@/components/brand-mark";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navigation = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/learn", label: "Learn" },
  { href: "/builder", label: "Circuit Builder" },
  { href: "/editor", label: "Code Lab" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const isAuth = pathname === "/login" || pathname === "/register";

  return (
    <div className="min-h-screen">
      <header className="app-shell-header sticky top-0 z-50 border-b border-white/[0.08] bg-ink-950/80 backdrop-blur-xl">
        <div className="mx-auto flex h-[4.5rem] max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" aria-label="QuantumLearn home" className="rounded-xl">
            <BrandMark />
          </Link>

          {!isAuth && (
            <nav aria-label="Primary navigation" className="hidden items-center gap-1 md:flex">
              {navigation.map((item) => {
                const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "rounded-lg px-3 py-2 text-sm font-medium transition-colors duration-200",
                      active
                        ? "bg-quantum-500/15 text-quantum-200"
                        : "text-slate-400 hover:bg-white/[0.06] hover:text-slate-100",
                    )}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>
          )}

          <div className="hidden items-center gap-3 md:flex">
            {isAuth ? (
              <Button asChild size="sm">
                <Link href={pathname === "/login" ? "/register" : "/login"}>
                  {pathname === "/login" ? "Create account" : "Sign in"}
                </Link>
              </Button>
            ) : (
              <Link className="rounded-lg px-3 py-2 text-sm font-medium text-slate-300 transition hover:text-white" href="/instructor">
                Instructor view
              </Link>
            )}
          </div>

          {!isAuth && (
            <button
              type="button"
              className="rounded-lg p-2 text-slate-200 transition hover:bg-white/[0.08] md:hidden"
              aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((open) => !open)}
            >
              {menuOpen ? <X size={21} /> : <Menu size={21} />}
            </button>
          )}
        </div>

        {!isAuth && menuOpen && (
          <nav aria-label="Mobile primary navigation" className="border-t border-white/[0.08] bg-ink-900 px-4 py-3 md:hidden">
            <div className="mx-auto grid max-w-7xl gap-1">
              {navigation.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setMenuOpen(false)}
                  className="rounded-lg px-3 py-2.5 text-sm font-medium text-slate-200 transition hover:bg-white/[0.07]"
                >
                  {item.label}
                </Link>
              ))}
              <Link href="/instructor" onClick={() => setMenuOpen(false)} className="rounded-lg px-3 py-2.5 text-sm font-medium text-slate-200 transition hover:bg-white/[0.07]">
                Instructor view
              </Link>
            </div>
          </nav>
        )}
      </header>
      <div className="app-shell-main quantum-grid">{children}</div>
    </div>
  );
}
