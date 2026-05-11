"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

export const LoginForm = () => {
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!login(username, password)) {
      setError("Use username user and password password.");
      return;
    }

    router.replace("/");
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-6 py-10">
      <section className="w-full max-w-sm rounded-3xl border border-[var(--stroke)] bg-white p-8 shadow-[var(--shadow)]">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-[var(--gray-text)]">
          Project Management
        </p>
        <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)]">
          Sign in
        </h1>
        <form className="mt-8 flex flex-col gap-5" onSubmit={handleSubmit}>
          <label className="flex flex-col gap-2 text-sm font-semibold text-[var(--navy-dark)]">
            Username
            <input
              value={username}
              onChange={(event) => {
                setUsername(event.target.value);
                setError("");
              }}
              className="h-12 rounded-xl border border-[var(--stroke)] px-4 text-base font-normal outline-none transition focus:border-[var(--primary-blue)]"
              autoComplete="username"
            />
          </label>
          <label className="flex flex-col gap-2 text-sm font-semibold text-[var(--navy-dark)]">
            Password
            <input
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);
                setError("");
              }}
              className="h-12 rounded-xl border border-[var(--stroke)] px-4 text-base font-normal outline-none transition focus:border-[var(--primary-blue)]"
              type="password"
              autoComplete="current-password"
            />
          </label>
          {error && (
            <p className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">
              {error}
            </p>
          )}
          <button
            type="submit"
            className="h-12 rounded-xl bg-[var(--secondary-purple)] px-4 text-sm font-semibold uppercase tracking-[0.16em] text-white transition hover:brightness-110"
          >
            Sign in
          </button>
        </form>
      </section>
    </main>
  );
};

