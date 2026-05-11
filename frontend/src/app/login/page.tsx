"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { LoginForm } from "@/components/LoginForm";
import { useAuth } from "@/components/AuthProvider";

export default function LoginPage() {
  const router = useRouter();
  const { isReady, isLoggedIn } = useAuth();

  useEffect(() => {
    if (isReady && isLoggedIn) {
      router.replace("/");
    }
  }, [isReady, isLoggedIn, router]);

  if (!isReady || isLoggedIn) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-6">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[var(--gray-text)]">
          Loading sign in
        </p>
      </main>
    );
  }

  return <LoginForm />;
}

