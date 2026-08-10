"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  pointerWithin,
  rectIntersection,
  type DragEndEvent,
  type DragStartEvent,
  type CollisionDetection,
} from "@dnd-kit/core";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { LoginForm } from "@/components/LoginForm";
import { ThemeToggle } from "@/components/ThemeToggle";
import { EditCardModal } from "@/components/EditCardModal";
import { AIAssistantWidget } from "@/components/AIAssistantWidget";
import { createId, initialData, moveCard, type Card, type BoardData } from "@/lib/kanban";
import { fetchBoard, saveBoard, deleteCardApi } from "@/lib/api";

export const KanbanBoard = () => {
  const [user, setUser] = useState<string | null>(null);
  const [isAuthLoaded, setIsAuthLoaded] = useState(false);
  const [board, setBoard] = useState<BoardData>(() => initialData);
  const [isLoadingBoard, setIsLoadingBoard] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [editingCard, setEditingCard] = useState<Card | null>(null);
  const [aiNotification, setAiNotification] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [priorityFilter, setPriorityFilter] = useState<"all" | "high" | "medium" | "low">("all");

  useEffect(() => {
    const storedUser = localStorage.getItem("pm_auth_user");
    if (storedUser) {
      setUser(storedUser);
    }
    setIsAuthLoaded(true);
  }, []);

  // Fetch board data from backend on login
  useEffect(() => {
    if (!user) return;
    setIsLoadingBoard(true);
    fetchBoard(user)
      .then((data) => {
        if (data && data.columns && data.columns.length > 0) {
          setBoard(data);
        }
      })
      .finally(() => {
        setIsLoadingBoard(false);
      });
  }, [user]);

  const persistBoard = useCallback(
    async (nextBoard: BoardData) => {
      if (!user) return;
      setIsSyncing(true);
      await saveBoard(user, nextBoard);
      setIsSyncing(false);
    },
    [user]
  );

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
    })
  );

  const collisionDetectionStrategy: CollisionDetection = useCallback((args) => {
    const pointerCollisions = pointerWithin(args);
    if (pointerCollisions.length > 0) {
      return pointerCollisions;
    }
    return rectIntersection(args);
  }, []);

  const cardsById = useMemo(() => board.cards, [board.cards]);

  // Priority and search filters
  const filteredBoard = useMemo(() => {
    if (!searchQuery.trim() && priorityFilter === "all") {
      return board;
    }

    const q = searchQuery.toLowerCase().trim();
    const matchingCards: Record<string, Card> = {};

    for (const [id, card] of Object.entries(board.cards)) {
      const matchesSearch =
        !q ||
        card.title.toLowerCase().includes(q) ||
        (card.details && card.details.toLowerCase().includes(q));
      const matchesPriority =
        priorityFilter === "all" || (card.priority || "medium") === priorityFilter;

      if (matchesSearch && matchesPriority) {
        matchingCards[id] = card;
      }
    }

    const filteredCols = board.columns.map((col) => ({
      ...col,
      cardIds: col.cardIds.filter((id) => Boolean(matchingCards[id])),
    }));

    return {
      ...board,
      columns: filteredCols,
      cards: matchingCards,
    };
  }, [board, searchQuery, priorityFilter]);

  const totalTasks = useMemo(() => Object.keys(board.cards).length, [board.cards]);

  const highPriorityCount = useMemo(() => {
    return Object.values(board.cards).filter((c) => c.priority === "high").length;
  }, [board.cards]);

  const completedTasks = useMemo(() => {
    const doneCol = board.columns.find((c) => c.title.toLowerCase().includes("done"));
    return doneCol ? doneCol.cardIds.length : 0;
  }, [board.columns]);

  const completionPercentage = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  const handleLogin = async (username: string, password: string) => {
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem("pm_auth_user", data.user);
        setUser(data.user);
        return true;
      }
    } catch {
      // Fallback for standalone mode
    }

    if (username === "user" && password === "password") {
      localStorage.setItem("pm_auth_user", username);
      setUser(username);
      return true;
    }

    return false;
  };

  const handleLogout = async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } catch {
      // Ignore network failure on logout
    }
    localStorage.removeItem("pm_auth_user");
    setUser(null);
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id) {
      return;
    }

    setBoard((prev) => {
      const nextColumns = moveCard(prev.columns, active.id as string, over.id as string);
      const nextBoard = { ...prev, columns: nextColumns };
      persistBoard(nextBoard);
      return nextBoard;
    });
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    setBoard((prev) => {
      const nextBoard = {
        ...prev,
        columns: prev.columns.map((column) =>
          column.id === columnId ? { ...column, title } : column
        ),
      };
      persistBoard(nextBoard);
      return nextBoard;
    });
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    const id = createId("card");
    setBoard((prev) => {
      const nextBoard = {
        ...prev,
        cards: {
          ...prev.cards,
          [id]: { id, title, details: details || "No details yet.", priority: "medium" as const },
        },
        columns: prev.columns.map((column) =>
          column.id === columnId
            ? { ...column, cardIds: [...column.cardIds, id] }
            : column
        ),
      };
      persistBoard(nextBoard);
      return nextBoard;
    });
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    deleteCardApi(cardId);
    setBoard((prev) => {
      const nextBoard = {
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
      persistBoard(nextBoard);
      return nextBoard;
    });
  };

  const handleSaveCard = (
    cardId: string,
    title: string,
    details: string,
    priority: "high" | "medium" | "low"
  ) => {
    setBoard((prev) => {
      const card = prev.cards[cardId];
      if (!card) return prev;
      const nextBoard = {
        ...prev,
        cards: {
          ...prev.cards,
          [cardId]: { ...card, title, details, priority },
        },
      };
      persistBoard(nextBoard);
      return nextBoard;
    });
  };

  const handleResetBoard = async () => {
    try {
      const response = await fetch("/api/board/reset", { method: "POST" });
      if (response.ok) {
        const data = await response.json();
        setBoard(data);
      }
    } catch {
      // Fallback reset
      setBoard(initialData);
    }
  };

  const handleBoardUpdateFromAI = (nextBoard: BoardData, notificationMessage?: string) => {
    setBoard(nextBoard);
    persistBoard(nextBoard);
    if (notificationMessage) {
      setAiNotification(notificationMessage.replace(/\*\*/g, ""));
      setTimeout(() => setAiNotification(null), 5000);
    }
  };

  if (!isAuthLoaded) {
    return null;
  }

  if (!user) {
    return <LoginForm onLogin={handleLogin} />;
  }

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  return (
    <div className="relative overflow-hidden min-h-screen">
      {/* Background Gradients */}
      <div className="pointer-events-none absolute left-0 top-0 h-[500px] w-[500px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(2,132,199,0.2)_0%,_rgba(2,132,199,0.02)_60%,_transparent_75%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[600px] w-[600px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(147,51,234,0.18)_0%,_rgba(147,51,234,0.02)_60%,_transparent_75%)]" />

      {/* Floating AI Toast Banner */}
      {aiNotification && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-3 rounded-2xl border border-[var(--primary-blue)]/50 bg-[var(--card-bg)] px-5 py-3.5 shadow-2xl backdrop-blur-xl animate-in fade-in slide-in-from-top-4 duration-300">
          <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-tr from-[var(--secondary-purple)] to-[var(--primary-blue)] text-white text-sm font-bold shadow-md">
            ✨
          </span>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--primary-blue)]">
              AI Kanban Action
            </p>
            <p className="text-xs font-semibold text-[var(--navy-dark)]">
              {aiNotification}
            </p>
          </div>
        </div>
      )}

      <main className="relative mx-auto flex min-h-screen max-w-[1600px] flex-col gap-8 px-6 pb-16 pt-10">
        {/* Header Section */}
        <header className="flex flex-col gap-6 rounded-[36px] border border-[var(--stroke)] bg-[var(--card-bg)]/80 p-8 shadow-[var(--shadow)] backdrop-blur-xl">
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-3">
                <span className="flex h-2 w-2 rounded-full bg-[var(--accent-yellow)] animate-pulse" />
                <span className="text-xs font-bold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                  Workspace by YASH
                </span>
                <span className="rounded-full bg-[var(--primary-blue)]/10 px-3 py-0.5 text-xs font-bold text-[var(--primary-blue)]">
                  {totalTasks} Total Tasks
                </span>
                {highPriorityCount > 0 && (
                  <span className="rounded-full bg-red-500/10 px-3 py-0.5 text-xs font-bold text-red-500">
                    🔥 {highPriorityCount} High Priority
                  </span>
                )}
              </div>
              <h1 className="mt-2 font-display text-4xl sm:text-5xl font-extrabold tracking-tight text-[var(--navy-dark)]">
                Drag N Drop
              </h1>
              <p className="mt-2 max-w-xl text-sm leading-relaxed text-[var(--gray-text)]">
                Organize, track, and automate your project workflow seamlessly with interactive drag-and-drop boards and smart AI automation.
              </p>
            </div>

            <div className="flex flex-col items-end gap-4">
              <div className="flex items-center gap-3">
                <ThemeToggle />
                <div className="flex items-center gap-3 rounded-full border border-[var(--stroke)] bg-[var(--surface-strong)] px-4 py-2 shadow-sm">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-xs font-bold uppercase tracking-wider text-[var(--navy-dark)]">
                    {user}
                  </span>
                  <span className="text-xs font-semibold text-[var(--gray-text)] border-l border-[var(--stroke)] pl-3">
                    {isSyncing ? "Syncing..." : isLoadingBoard ? "Loading..." : "Saved"}
                  </span>
                  <button
                    type="button"
                    onClick={handleResetBoard}
                    className="ml-1 rounded-full border border-[var(--stroke)] bg-[var(--surface)] px-3 py-1 text-xs font-bold uppercase tracking-wide text-[var(--navy-dark)] transition hover:bg-[var(--primary-blue)] hover:text-white"
                  >
                    Reset Board
                  </button>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="ml-1 rounded-full bg-red-500/10 px-3 py-1 text-xs font-bold uppercase tracking-wide text-red-600 transition hover:bg-red-500 hover:text-white"
                  >
                    Logout
                  </button>
                </div>
              </div>

              {/* Progress Metric Card */}
              <div className="w-64 rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] p-3.5 shadow-sm">
                <div className="flex items-center justify-between text-xs font-bold text-[var(--navy-dark)]">
                  <span>Sprint Progress</span>
                  <span className="text-[var(--primary-blue)]">{completionPercentage}%</span>
                </div>
                <div className="mt-2 h-2.5 w-full overflow-hidden rounded-full bg-[var(--stroke)]">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-[var(--primary-blue)] to-[var(--secondary-purple)] transition-all duration-500"
                    style={{ width: `${completionPercentage}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Search Bar & Priority Filter Toolbar */}
          <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-[var(--stroke)]">
            <div className="flex flex-1 items-center gap-3 max-w-md rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2.5 shadow-2xs">
              <span className="text-sm opacity-60">🔍</span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search tasks by title or details..."
                className="w-full bg-transparent text-xs font-medium text-[var(--navy-dark)] outline-none placeholder:text-[var(--gray-text)]"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  className="text-xs text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
                >
                  ✕
                </button>
              )}
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--gray-text)] mr-1">
                Priority:
              </span>
              {(["all", "high", "medium", "low"] as const).map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPriorityFilter(p)}
                  className={`rounded-xl px-3 py-1.5 text-xs font-bold uppercase tracking-wider transition ${
                    priorityFilter === p
                      ? p === "high"
                        ? "bg-red-500 text-white shadow-md"
                        : p === "medium"
                        ? "bg-amber-500 text-white shadow-md"
                        : p === "low"
                        ? "bg-emerald-500 text-white shadow-md"
                        : "bg-[var(--navy-dark)] text-white shadow-md"
                      : "border border-[var(--stroke)] bg-[var(--surface)] text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        </header>

        {/* Board Columns Grid */}
        <DndContext
          sensors={sensors}
          collisionDetection={collisionDetectionStrategy}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <section className="grid gap-6 lg:grid-cols-5">
            {filteredBoard.columns.map((column) => (
              <KanbanColumn
                key={column.id}
                column={column}
                cards={column.cardIds.map((cardId) => filteredBoard.cards[cardId]).filter(Boolean)}
                onRename={handleRenameColumn}
                onAddCard={handleAddCard}
                onDeleteCard={handleDeleteCard}
                onEditCard={(card) => setEditingCard(card)}
              />
            ))}
          </section>
          <DragOverlay>
            {activeCard ? (
              <div className="w-[270px]">
                <KanbanCardPreview card={activeCard} />
              </div>
            ) : null}
          </DragOverlay>
        </DndContext>

        <footer className="mt-8 text-center text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
          Designed & Built with ❤️ by <span className="text-[var(--primary-blue)] font-bold">YASH</span>
        </footer>
      </main>

      {/* Card Edit Modal */}
      {editingCard && (
        <EditCardModal
          card={editingCard}
          isOpen={!!editingCard}
          onClose={() => setEditingCard(null)}
          onSave={handleSaveCard}
        />
      )}

      {/* Floating Bottom-Right AI Assistant Widget */}
      <AIAssistantWidget
        board={board}
        onBoardUpdate={handleBoardUpdateFromAI}
      />
    </div>
  );
};
