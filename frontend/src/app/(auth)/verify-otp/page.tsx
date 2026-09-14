import { AuthForm } from "@/components/auth-form";
export default async function VerifyOTPPage({searchParams}: {searchParams: Promise<{email?: string}>}) {
  const {email} = await searchParams;
  return <AuthForm mode="verify" email={email} />;
}
