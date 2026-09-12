"use client";
import Link from "next/link";
import { useState } from "react";
import { API_URL } from "@/lib/api";
import { Button } from "./ui/button";
import { Input, FormField } from "./ui/input";
import { Status } from "./ui/page";
type Mode = "login" | "register" | "verify";
const copy = {
  login: {
    title: "Welcome back.",
    description: "Sign in to your quantum learning environment.",
    button: "Sign in",
    number: "01 / ACCESS",
  },
  register: {
    title: "Begin your exploration.",
    description:
      "Create an account. Build your understanding, one experiment at a time.",
    button: "Create account",
    number: "01 / CREATE ACCOUNT",
  },
  verify: {
    title: "Check your inbox.",
    description: "Enter the six-digit verification code sent to your email.",
    button: "Verify email",
    number: "02 / VERIFY EMAIL",
  },
};
export function AuthForm({
  mode,
  email: initialEmail = "",
}: {
  mode: Mode;
  email?: string;
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState(initialEmail);
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const text = copy[mode];
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    if (mode === "verify" && otp.length !== 6) {
      setError("Enter all six digits of your verification code.");
      return;
    }
    setLoading(true);
    try {
      const path =
        mode === "verify"
          ? `/api/auth/verify-otp?email=${encodeURIComponent(email)}&otp=${encodeURIComponent(otp)}`
          : `/api/auth/${mode}`;
      const response = await fetch(`${API_URL}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        ...(mode !== "verify" && {
          body: JSON.stringify(
            mode === "login" ? { email, password } : { name, email, password },
          ),
        }),
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "We couldn’t complete your request. Check your details and try again.",
        );
      if (mode === "login") {
        localStorage.setItem("access_token", data.access_token);
        window.location.href = "/";
      } else if (mode === "register")
        window.location.href = `/verify-otp?email=${encodeURIComponent(email)}`;
      else setSuccess(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to connect. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }
  return (
    <main className="auth-layout">
      <aside className="auth-art">
        <p className="system-label">
          <span />
          IQLRS / LEARNING ENVIRONMENT
        </p>
        <h2>
          Curiosity,
          <br />
          in a new
          <br />
          <span className="text-slate-400">state.</span>
        </h2>
        <div className="auth-field" aria-hidden="true" />
        <p>
          From the first qubit to quantum algorithms. A place to understand the
          theory and put it into practice.
        </p>
      </aside>
      <section className="auth-card panel">
        <header>
          <p className="technical mb-4">{text.number}</p>
          <h1>{text.title}</h1>
          <p>{text.description}</p>
        </header>
        {success ? (
          <div className="space-y-5">
            <Status kind="success">
              Your email is verified. You’re ready to sign in.
            </Status>
            <Button asChild>
              <Link href="/login">Continue to sign in ↗</Link>
            </Button>
          </div>
        ) : (
          <form onSubmit={submit} aria-busy={loading}>
            {mode === "register" && (
              <FormField id="name" label="Full name">
                <Input
                  id="name"
                  autoComplete="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  required
                />
              </FormField>
            )}
            <FormField id="email" label="Email address">
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                readOnly={mode === "verify" && !!initialEmail}
              />
            </FormField>
            {mode !== "verify" ? (
              <FormField id="password" label="Password">
                <Input
                  id="password"
                  type="password"
                  autoComplete={
                    mode === "login" ? "current-password" : "new-password"
                  }
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={
                    mode === "login" ? "Your password" : "Choose a password"
                  }
                  required
                />
              </FormField>
            ) : (
              <FormField id="otp" label="Verification code">
                <Input
                  id="otp"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                  placeholder="000000"
                  required
                  className="font-mono text-xl tracking-[.35em]"
                />
              </FormField>
            )}
            {error && <Status kind="error">{error}</Status>}
            <Button type="submit" disabled={loading}>
              {loading ? "Please wait…" : text.button}
              <span aria-hidden="true">↗</span>
            </Button>
          </form>
        )}
        <p className="mt-6 text-sm text-slate-400">
          {mode === "login" ? (
            <>
              New to IQLRS?{" "}
              <Link className="auth-link" href="/register">
                Create an account
              </Link>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <Link className="auth-link" href="/login">
                Sign in
              </Link>
            </>
          )}
        </p>
      </section>
    </main>
  );
}
