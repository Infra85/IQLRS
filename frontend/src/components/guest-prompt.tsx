"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Button } from "./ui/button";
export function GuestPrompt() {
  const ref = useRef<HTMLDialogElement>(null);
  const [dismissed, setDismissed] = useState(false);
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog || dismissed || localStorage.getItem("access_token")) return;
    const previous = document.activeElement as HTMLElement | null;
    dialog.showModal();
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      dialog.close();
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, [dismissed]);
  return (
    <dialog
      ref={ref}
      className="modal"
      aria-labelledby="guest-title"
      onCancel={() => setDismissed(true)}
      onClose={() => {
        if (!ref.current?.open) setDismissed(true);
      }}
    >
      <p className="system-label">
        <span />
        ACCOUNT OPTIONAL
      </p>
      <h2 id="guest-title">Make room for discovery.</h2>
      <p>
        Explore the lessons and circuit builder as a guest. Sign in to access
        your personal learning dashboard.
      </p>
      <div className="flex flex-wrap gap-3">
        <Button asChild>
          <Link href="/login">Sign in</Link>
        </Button>
        <Button
          variant="secondary"
          onClick={() => setDismissed(true)}
          autoFocus
        >
          Continue as guest
        </Button>
      </div>
    </dialog>
  );
}
