"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { ChatSidebar } from "@/components/ChatSidebar";
import { moveCard, type BoardData } from "@/lib/kanban";
import { api, type ApiBoardResponse } from "@/lib/api";

type KanbanBoardProps = {
  userId: string;
  username?: string;
  onLogout?: () => void;
};

const boardFromApi = (payload: ApiBoardResponse): BoardData => ({
  columns: payload.columns.map((column) => ({
    id: column.id,
    title: column.title,
    cardIds: column.cardIds,
  })),
  cards: Object.fromEntries(
    Object.entries(payload.cards).map(([id, card]) => [
      id,
      {
        id: card.id,
        title: card.title,
        details: card.details || "No details yet.",
      },
    ])
  ),
});

export const KanbanBoard = ({ userId, username, onLogout }: KanbanBoardProps) => {
  const [board, setBoard] = useState<BoardData | null>(null);
  const [boardId, setBoardId] = useState<string | null>(null);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>("");

  const loadBoard = useCallback(async () => {
    setIsLoading(true);
    setError("");
    try {
      const data = await api.getBoard(userId);
      setBoard(boardFromApi(data));
      setBoardId(data.id);
    } catch {
      setError("Unable to load your board. Is the backend running?");
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    void loadBoard();
  }, [loadBoard]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const cardsById = useMemo(() => board?.cards ?? {}, [board]);

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!board || !over || active.id === over.id) return;

    const activeId = active.id as string;
    const overId = over.id as string;
    const nextColumns = moveCard(board.columns, activeId, overId);

    setBoard((prev) => (prev ? { ...prev, columns: nextColumns } : prev));

    const nextColumn = nextColumns.find((col) => col.cardIds.includes(activeId));
    if (!nextColumn) return;
    const position = nextColumn.cardIds.indexOf(activeId);
    void api.moveCard(activeId, nextColumn.id, Math.max(0, position)).catch(async () => {
      setError("Could not move card.");
      await loadBoard();
    });
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    if (!boardId) return;

    const originalTitle =
      board?.columns.find((c) => c.id === columnId)?.title ?? title;

    setBoard((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        columns: prev.columns.map((col) =>
          col.id === columnId ? { ...col, title } : col
        ),
      };
    });

    void api.renameColumn(boardId, columnId, title).catch(() => {
      setBoard((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          columns: prev.columns.map((col) =>
            col.id === columnId ? { ...col, title: originalTitle } : col
          ),
        };
      });
      setError("Could not rename column.");
    });
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    void api
      .createCard(columnId, title, details)
      .then((card) => {
        setBoard((prev) => {
          if (!prev) {
            return prev;
          }
          return {
            ...prev,
            cards: {
              ...prev.cards,
              [card.id]: {
                id: card.id,
                title: card.title,
                details: card.details || "No details yet.",
              },
            },
            columns: prev.columns.map((column) =>
              column.id === columnId
                ? { ...column, cardIds: [...column.cardIds, card.id] }
                : column
            ),
          };
        });
      })
      .catch(() => {
        setError("Could not add card. Is the backend running?");
      });
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    setBoard((prev) => {
      if (!prev) {
        return prev;
      }
      return {
        ...prev,
        cards: Object.fromEntries(
          Object.entries(prev.cards).filter(([id]) => id !== cardId)
        ),
        columns: prev.columns.map((column) =>
          column.id === columnId
            ? {
                ...column,
                cardIds: column.cardIds.filter((id) => id !== cardId),
              }
            : column
        ),
      };
    });

    void api.deleteCard(cardId).catch(async () => {
      setError("Could not delete card. Retrying…");
      await loadBoard();
    });
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-10 px-6 pb-16 pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-8 shadow-[var(--shadow)] backdrop-blur">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-4xl font-semibold text-[var(--navy-dark)]">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="flex flex-col items-start gap-3 rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4 sm:items-end">
              {username && (
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                  Signed in as {username}
                </p>
              )}
              <p className="text-lg font-semibold text-[var(--primary-blue)]">
                One board. Five columns. Zero clutter.
              </p>
              {onLogout && (
                <button
                  type="button"
                  onClick={onLogout}
                  className="rounded-xl bg-[var(--secondary-purple)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-white transition hover:brightness-110"
                >
                  Logout
                </button>
              )}
            </div>
          </div>
          {error && (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm font-semibold text-red-800">
              {error}
            </div>
          )}
          <div className="flex flex-wrap items-center gap-4">
            {board?.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1fr_380px] lg:items-start">
          {isLoading || !board ? (
            <div className="flex min-h-[520px] items-center justify-center rounded-[32px] border border-[var(--stroke)] bg-white/70 p-8 text-sm font-semibold uppercase tracking-[0.24em] text-[var(--gray-text)] shadow-[var(--shadow)]">
              Loading board
            </div>
          ) : (
            <DndContext
              sensors={sensors}
              collisionDetection={closestCorners}
              onDragStart={handleDragStart}
              onDragEnd={handleDragEnd}
            >
              <section className="grid gap-6 lg:grid-cols-5">
                {board.columns.map((column) => (
                  <KanbanColumn
                    key={column.id}
                    column={column}
                    cards={column.cardIds.map((cardId) => board.cards[cardId])}
                    onRename={handleRenameColumn}
                    onAddCard={handleAddCard}
                    onDeleteCard={handleDeleteCard}
                  />
                ))}
              </section>
              <DragOverlay>
                {activeCard ? (
                  <div className="w-[260px]">
                    <KanbanCardPreview card={activeCard} />
                  </div>
                ) : null}
              </DragOverlay>
            </DndContext>
          )}

          <ChatSidebar userId={userId} boardId={boardId} onBoardRefresh={loadBoard} />
        </section>
      </main>
    </div>
  );
};
