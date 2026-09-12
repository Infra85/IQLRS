import { AuthForm } from "@/components/auth-form";
export default function VerifyOTPPage({
  searchParams,
}: {
  searchParams: { email?: string };
}) {
  return <AuthForm mode="verify" email={searchParams.email} />;
}
