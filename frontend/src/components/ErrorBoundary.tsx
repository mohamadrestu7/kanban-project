"use client";

import { Component, type ReactNode } from "react";

type Props = { children: ReactNode };
type State = { hasError: boolean };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    console.error("ErrorBoundary caught:", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="flex min-h-screen items-center justify-center bg-[var(--surface)] px-6">
          <div className="w-full max-w-sm rounded-3xl border border-[var(--stroke)] bg-white p-8 text-center shadow-[var(--shadow)]">
            <p className="text-sm font-semibold text-[var(--navy-dark)]">
              Something went wrong. Please refresh the page.
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-4 rounded-xl bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-white transition hover:brightness-110"
            >
              Refresh
            </button>
          </div>
        </main>
      );
    }
    return this.props.children;
  }
}
