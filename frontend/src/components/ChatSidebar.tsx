"use client";

import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import clsx from "clsx";
import {
  api,
  type ApiAiBoardUpdateCard,
  type ApiAiBoardUpdateColumn,
  type ApiAiChatResponse,
  type ApiConversationMessage,
} from "@/lib/api";

type ChatSidebarProps = {
  userId: string;
  boardId: string | null;
  onBoardRefresh: () => Promise<void>;
};

type UiMessage = {
  id: string;
  role: "user" | "assistant";
  message: string;
};

const toUiMessages = (items: ApiConversationMessage[]): UiMessage[] =>
  items.map((item) => ({
    id: item.id,
    role: item.role,
    message: item.message,
  }));

const summarizeCardUpdate = (update: ApiAiBoardUpdateCard) => {
  const action = update.action.toLowerCase();
  if (action === "create") {
    return `Create card${update.columnId ? ` in ${update.columnId}` : ""}: ${update.title ?? ""}`.trim();
  }
  if (action === "update") {
    return `Update card ${update.id ?? ""}`.trim();
  }
  if (action === "delete") {
    return `Delete card ${update.id ?? ""}`.trim();
  }
  if (action === "move") {
    return `Move card ${update.id ?? ""}${update.columnId ? ` → ${update.columnId}` : ""}`.trim();
  }
  return `Card action "${update.action}"`;
};

const summarizeColumnUpdate = (update: ApiAiBoardUpdateColumn) =>
  `Rename column ${update.id} → ${update.title}`;

export const ChatSidebar = ({ userId, boardId, onBoardRefresh }: ChatSidebarProps) => {
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const [pending, setPending] = useState<ApiAiChatResponse["boardUpdates"]>(null);
  const [isOpen, setIsOpen] = useState(false);

  const scrollRef = useRef<HTMLDivElement | null>(null);

  const pendingSummary = useMemo(() => {
    if (!pending) {
      return null;
    }
    const columns = pending.columns?.map(summarizeColumnUpdate) ?? [];
    const cards = pending.cards?.map(summarizeCardUpdate) ?? [];
    return [...columns, ...cards];
  }, [pending]);

  useEffect(() => {
    if (!boardId) {
      return;
    }
    setIsLoadingHistory(true);
    setError("");
    api
      .aiHistory(userId, boardId)
      .then((items) => {
        setMessages(toUiMessages(items));
      })
      .catch(() => setError("Unable to load chat history."))
      .finally(() => setIsLoadingHistory(false));
  }, [boardId, userId]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages, pending, isSending, isLoadingHistory]);

  const sendMessage = async (text: string) => {
    if (!boardId) {
      setError("Board is still loading.");
      return;
    }

    setIsSending(true);
    setError("");
    setPending(null);

    const userMsg: UiMessage = {
      id: `local-user-${Date.now()}`,
      role: "user",
      message: text,
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const response = await api.aiChat({
        user_id: userId,
        board_id: boardId,
        message: text,
      });

      setMessages((prev) => [
        ...prev,
        { id: `local-ai-${Date.now()}`, role: "assistant", message: response.message },
      ]);
      setPending(response.boardUpdates ?? null);
    } catch {
      setError("AI request failed. Check the backend logs.");
    } finally {
      setIsSending(false);
    }
  };

  const applyUpdates = async () => {
    if (!boardId || !pending) {
      return;
    }

    setError("");
    setIsSending(true);
    try {
      for (const col of pending.columns ?? []) {
        await api.renameColumn(boardId, col.id, col.title);
      }

      for (const card of pending.cards ?? []) {
        const action = card.action.toLowerCase();
        if (action === "create") {
          if (!card.columnId || !card.title) continue;
          await api.createCard(card.columnId, card.title, card.details ?? "");
          continue;
        }
        if (action === "update") {
          if (!card.id) continue;
          await api.updateCard(card.id, {
            title: card.title ?? undefined,
            details: card.details ?? undefined,
          });
          continue;
        }
        if (action === "delete") {
          if (!card.id) continue;
          await api.deleteCard(card.id);
          continue;
        }
        if (action === "move") {
          if (!card.id || !card.columnId) continue;
          await api.moveCard(card.id, card.columnId, Math.max(0, card.position ?? 0));
          continue;
        }
      }

      setPending(null);
      await onBoardRefresh();
    } catch {
      setError("Failed to apply updates. You can retry, or dismiss and continue manually.");
    } finally {
      setIsSending(false);
    }
  };

  const content = (
    <aside className="flex h-full flex-col rounded-[28px] border border-[var(--stroke)] bg-white/80 shadow-[var(--shadow)] backdrop-blur">
      <header className="flex items-center justify-between gap-3 border-b border-[var(--stroke)] px-5 py-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[var(--gray-text)]">
            AI assistant
          </p>
          <p className="mt-1 font-display text-lg font-semibold text-[var(--navy-dark)]">
            Board chat
          </p>
        </div>
        <button
          type="button"
          onClick={() => setIsOpen(false)}
          className="rounded-xl border border-[var(--stroke)] bg-white px-3 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-[var(--navy-dark)] lg:hidden"
          aria-label="Close chat"
        >
          Close
        </button>
      </header>

      <div className="flex min-h-0 flex-1 flex-col gap-4 px-5 py-4">
        {error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-800">
            {error}
          </div>
        )}

        {pendingSummary && pendingSummary.length > 0 && (
          <section className="rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--gray-text)]">
              Suggested changes
            </p>
            <ul className="mt-3 space-y-2 text-sm font-medium text-[var(--navy-dark)]">
              {pendingSummary.map((line) => (
                <li key={line} className="flex gap-2">
                  <span className="mt-[7px] h-2 w-2 shrink-0 rounded-full bg-[var(--accent-yellow)]" />
                  <span>{line}</span>
                </li>
              ))}
            </ul>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                disabled={isSending}
                onClick={() => void applyUpdates()}
                className="rounded-full bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-white transition hover:brightness-110 disabled:opacity-60"
              >
                Apply changes
              </button>
              <button
                type="button"
                disabled={isSending}
                onClick={() => setPending(null)}
                className="rounded-full border border-[var(--stroke)] bg-white px-4 py-2 text-xs font-semibold uppercase tracking-[0.14em] text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)] disabled:opacity-60"
              >
                Dismiss
              </button>
            </div>
          </section>
        )}

        <div
          ref={scrollRef}
          className="min-h-0 flex-1 space-y-3 overflow-y-auto rounded-2xl border border-[var(--stroke)] bg-white px-4 py-4"
        >
          {isLoadingHistory ? (
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--gray-text)]">
              Loading history
            </p>
          ) : messages.length === 0 ? (
            <p className="text-sm text-[var(--gray-text)]">
              Ask for changes like “Move card-1 to Review” or “Add a new task in Backlog”.
            </p>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={clsx(
                  "rounded-2xl px-4 py-3 text-sm leading-6",
                  msg.role === "user"
                    ? "ml-auto max-w-[90%] bg-[var(--primary-blue)]/10 text-[var(--navy-dark)]"
                    : "mr-auto max-w-[90%] bg-[var(--surface)] text-[var(--navy-dark)]"
                )}
              >
                <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[var(--gray-text)]">
                  {msg.role === "user" ? "You" : "Assistant"}
                </p>
                <p className="mt-1 whitespace-pre-wrap">{msg.message}</p>
              </div>
            ))
          )}
          {isSending && (
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[var(--gray-text)]">
              Thinking
            </p>
          )}
        </div>

        <form
          onSubmit={(event: FormEvent<HTMLFormElement>) => {
            event.preventDefault();
            const text = input.trim();
            if (!text || isSending) return;
            setInput("");
            void sendMessage(text);
          }}
          className="flex gap-2"
        >
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask the assistant…"
            className="h-12 flex-1 rounded-2xl border border-[var(--stroke)] bg-white px-4 text-sm outline-none transition focus:border-[var(--primary-blue)]"
          />
          <button
            type="submit"
            disabled={isSending || !input.trim()}
            className="h-12 rounded-2xl bg-[var(--secondary-purple)] px-5 text-xs font-semibold uppercase tracking-[0.14em] text-white transition hover:brightness-110 disabled:opacity-60"
          >
            Send
          </button>
        </form>
      </div>
    </aside>
  );

  return (
    <>
      <div className="hidden h-[calc(100vh-14rem)] min-h-[520px] lg:block">{content}</div>

      <div className="lg:hidden">
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-40 rounded-full bg-[var(--secondary-purple)] px-5 py-3 text-xs font-semibold uppercase tracking-[0.14em] text-white shadow-[var(--shadow)] transition hover:brightness-110"
        >
          Chat
        </button>
        {isOpen && (
          <div className="fixed inset-0 z-50">
            <div
              className="absolute inset-0 bg-black/30"
              onClick={() => setIsOpen(false)}
            />
            <div className="absolute inset-x-3 bottom-3 top-3">{content}</div>
          </div>
        )}
      </div>
    </>
  );
};

