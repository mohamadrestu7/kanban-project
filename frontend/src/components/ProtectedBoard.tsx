"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";
import { KanbanBoard } from "@/components/KanbanBoard";

export const ProtectedBoard = () => {
  const router = useRouter();
  const { isReady, isLoggedIn, username, logout } = useAuth();

  useEffect(() => {
    if (isReady && !isLoggedIn) {
      router.replace("/login");
    }
  }, [isReady, isLoggedIn, router]);

  if (!isReady || !isLoggedIn) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-6">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[var(--gray-text)]">
          Loading workspace
        </p>
      </main>
    );
  }

  return <KanbanBoard username={username ?? "user"} onLogout={logout} />;
};

