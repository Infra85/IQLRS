"use client";

import { Suspense, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";

function VerifyOTPContent() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const email = searchParams.get("email") || "";

  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();

    if (otp.length !== 6) {
      alert("Please enter the 6-digit OTP");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/auth/verify-otp?email=${encodeURIComponent(
          email
        )}&otp=${encodeURIComponent(otp)}`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (!response.ok) {
  throw new Error(data.detail || "OTP verification failed");
}

alert("Email verified successfully!");

window.location.href = "/login";

   
    } catch (error) {
      console.error(error);

      alert(
        error instanceof Error
          ? error.message
          : "Something went wrong"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center bg-[#020617] px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-xl">

        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white">
            Verify Your Email
          </h1>

          <p className="mt-2 text-slate-400">
            Enter the 6-digit OTP sent to your email
          </p>

          <p className="mt-2 text-sm text-blue-400 break-all">
            {email}
          </p>
        </div>

        <form onSubmit={handleVerify} className="space-y-5">

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              OTP
            </label>

            <input
              type="text"
              inputMode="numeric"
              maxLength={6}
              value={otp}
              onChange={(e) =>
                setOtp(e.target.value.replace(/\D/g, ""))
              }
              placeholder="Enter 6-digit OTP"
              required
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-4 py-3 text-center text-xl tracking-[0.5em] text-white outline-none focus:border-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-blue-600 py-3 font-semibold text-white hover:bg-blue-700 transition disabled:opacity-50"
          >
            {loading ? "Verifying..." : "Verify Email"}
          </button>

        </form>

      </div>
    </main>
  );
}

export default function VerifyOTPPage() {
  return <Suspense fallback={<main className="min-h-screen bg-[#020617]" />}><VerifyOTPContent /></Suspense>;
}
