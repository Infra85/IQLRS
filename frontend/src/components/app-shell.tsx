"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { BrandMark } from "./brand-mark";
const navigation = [
  { href: "/", label: "Overview" },
  { href: "/learn", label: "Learn" },
  { href: "/builder", label: "Circuit builder" },
  { href: "/editor", label: "Code lab" },
  { href: "/dashboard", label: "My progress" },
  { href: "/instructor", label: "Instructor" },
];
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuButton = useRef<HTMLButtonElement>(null);
  const isAuth = ["/login", "/register", "/verify-otp"].includes(pathname);
  useEffect(() => setMenuOpen(false), [pathname]);
  const links = navigation.map((item) => (
    <Link
      key={item.href}
      href={item.href}
      className="nav-link"
      aria-current={
        pathname === item.href ||
        (item.href !== "/" && pathname.startsWith(item.href + "/"))
          ? "page"
          : undefined
      }
      onClick={() => setMenuOpen(false)}
    >
      {item.label}
    </Link>
  ));
  return (
    <div className="min-h-screen">
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>
      <header
        className="shell-header"
        onKeyDown={(e) => {
          if (e.key === "Escape") {
            setMenuOpen(false);
            menuButton.current?.focus();
          }
        }}
      >
        <div className="shell-bar">
          <Link href="/" aria-label="IQLRS home">
            <BrandMark />
          </Link>
          {isAuth ? (
            <Link
              className="nav-link"
              href={pathname === "/login" ? "/register" : "/login"}
            >
              {pathname === "/login" ? "Create account" : "Sign in"} ↗
            </Link>
          ) : (
            <>
              <nav aria-label="Primary" className="hidden lg:flex items-center">
                {links}
              </nav>
              <button
                ref={menuButton}
                className="ui-button button-ghost lg:hidden"
                aria-label={menuOpen ? "Close navigation" : "Open navigation"}
                aria-expanded={menuOpen}
                aria-controls="mobile-navigation"
                onClick={() => setMenuOpen(!menuOpen)}
              >
                {menuOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            </>
          )}
        </div>
        {!isAuth && (
          <nav
            id="mobile-navigation"
            aria-label="Mobile primary"
            hidden={!menuOpen}
            className="border-t px-5 py-3 lg:!hidden"
          >
            <div className="grid">{links}</div>
          </nav>
        )}
      </header>
      <div id="main-content" tabIndex={-1} className="app-shell-main">
        {children}
      </div>
      <footer className="shell-footer technical">
        <span>IQLRS / Quantum learning environment</span>
        <Link href="/learn">Understand. Experiment. Observe. ↗</Link>
      </footer>
    </div>
  );
}
