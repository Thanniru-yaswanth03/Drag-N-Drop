"use client";

import { useState, useMemo, useCallback, useEffect } from "react";
import {
  DndContext,
  DragOverlay,
  type DragEndEvent,
  type DragStartEvent,
  useSensor,
  useSensors,
  PointerSensor,
  TouchSensor,
  MouseSensor,
  type CollisionDetection,
  pointerWithin,
  rectIntersection,
} from "@dnd-kit/core";
import { type BoardData, type Card, emptyBoardData, moveCard } from "@/lib/kanban";
import { useUndoRedo } from "@/lib/useUndoRedo";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { ThemeToggle } from "@/components/ThemeToggle";
import { LoginForm } from "@/components/LoginForm";
import { EditCardModal } from "@/components/EditCardModal";
import { ProjectSwitcher } from "@/components/ProjectSwitcher";
import { ActivityHistoryModal } from "@/components/ActivityHistoryModal";
import { ProjectMembersModal } from "@/components/ProjectMembersModal";
import { NotificationCenterModal } from "@/components/NotificationCenterModal";
import { TaskFilterToolbar } from "@/components/TaskFilterToolbar";
import { AIAssistantWidget } from "@/components/AIAssistantWidget";
import { useWebSocket } from "@/lib/useWebSocket";
import {
  fetchBoard,
  saveBoard,
  fetchProjects,
  createProjectApi,
  updateProjectApi,
  deleteProjectApi,
  createCardApi,
  updateCardApi,
  deleteCardApi,
  moveCardApi,
  updateColumnApi,
  clearColumnApi,
  fetchProjectMembers,
  fetchNotificationsApi,
  loginApi,
  logoutApi,
  checkAuthApi,
  type Project,
} from "@/lib/api";
import {
  filterAndSortBoard,
  extractAvailableTags,
  getActiveFilterCount,
  defaultFilterOptions,
  type FilterOptions,
  type SortOptionType,
  defaultSortOption,
} from "@/lib/filterUtils";

export const KanbanBoard = () => {
  const [user, setUser] = useState<string | null>(null);
  const [isAuthLoaded, setIsAuthLoaded] = useState(false);
  const {
    state: board,
    set: setBoard,
    reset: resetBoard,
    undo,
    redo,
    canUndo,
    canRedo,
  } = useUndoRedo<BoardData>(emptyBoardData);
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [, setIsLoadingBoard] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [editingCard, setEditingCard] = useState<Card | null>(null);
  const [isActivityModalOpen, setIsActivityModalOpen] = useState(false);
  const [isMembersModalOpen, setIsMembersModalOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [unreadNotifCount, setUnreadNotifCount] = useState(0);
  const [, setUserRole] = useState<string>("owner");
  const [aiNotification, setAiNotification] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterOptions>(defaultFilterOptions);
  const [sortOption, setSortOption] = useState<SortOptionType>(defaultSortOption);

  // Real-Time WebSocket Channel
  const handleWsMessage = useCallback((payload: unknown) => {
    const data = payload as { type?: string; board?: BoardData; projectId?: string };
    if (data && data.type === "BOARD_UPDATED" && data.board && data.projectId === activeProjectId) {
      setBoard(data.board);
    }
  }, [setBoard, activeProjectId]);

  const { isConnected: isWsConnected } = useWebSocket({
    projectId: activeProjectId,
    username: user,
    onMessage: handleWsMessage,
  });

  const refreshNotifications = useCallback(() => {
    if (!user) return;
    fetchNotificationsApi().then((res) => {
      setUnreadNotifCount(res.unreadCount);
    });
  }, [user]);

  useEffect(() => {
    refreshNotifications();
    const timer = setInterval(refreshNotifications, 15000);
    return () => clearInterval(timer);
  }, [refreshNotifications]);

  // Initial Auth Verification (Single Source of Truth)
  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
      setProjects([]);
      setActiveProjectId(null);
      resetBoard(emptyBoardData);
    };

    window.addEventListener("pm_auth_unauthorized", handleUnauthorized);

    checkAuthApi()
      .then((res) => {
        if (res.authenticated && res.user) {
          setUser(res.user);
        } else {
          setUser(null);
        }
      })
      .catch(() => {
        setUser(null);
      })
      .finally(() => {
        setIsAuthLoaded(true);
      });

    return () => {
      window.removeEventListener("pm_auth_unauthorized", handleUnauthorized);
    };
  }, [resetBoard]);

  // Fetch user projects list whenever authenticated user changes
  useEffect(() => {
    if (!user) {
      setProjects([]);
      setActiveProjectId(null);
      return;
    }

    setIsLoadingBoard(true);
    fetchProjects()
      .then((projs) => {
        if (Array.isArray(projs) && projs.length > 0) {
          setProjects(projs);
          setActiveProjectId((curr) => (curr && projs.some((p) => p.id === curr) ? curr : projs[0].id));
        } else {
          setProjects([]);
          setActiveProjectId(null);
        }
      })
      .catch((err) => {
        console.error("Error fetching projects from server:", err);
      })
      .finally(() => {
        setIsLoadingBoard(false);
      });
  }, [user]);

  // Fetch board data whenever active project changes
  useEffect(() => {
    if (!user || !activeProjectId) {
      resetBoard(emptyBoardData);
      return;
    }

    resetBoard(emptyBoardData);
    setIsLoadingBoard(true);

    fetchBoard(activeProjectId)
      .then((data) => {
        if (data && data.columns && Array.isArray(data.columns)) {
          resetBoard(data);
        }
      })
      .catch((err) => {
        console.error("Error fetching board from backend:", err);
      })
      .finally(() => {
        setIsLoadingBoard(false);
      });

    fetchProjectMembers(activeProjectId).then((res) => {
      setUserRole(res.userRole || "viewer");
    });
  }, [user, activeProjectId, resetBoard]);

  const persistBoard = useCallback(
    async (nextBoard: BoardData) => {
      if (!user || !activeProjectId) return;
      setIsSyncing(true);
      const success = await saveBoard(nextBoard, activeProjectId);
      setIsSyncing(false);
      if (!success) {
        console.error("Failed to persist board to backend");
      }
    },
    [user, activeProjectId]
  );

  // Keyboard Shortcuts for Undo (Ctrl+Z) and Redo (Ctrl+Y / Ctrl+Shift+Z)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const targetTag = (e.target as HTMLElement)?.tagName;
      if (["INPUT", "TEXTAREA", "SELECT"].includes(targetTag)) return;

      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
        if (e.shiftKey) {
          e.preventDefault();
          if (canRedo) {
            const next = redo();
            if (next) persistBoard(next);
          }
        } else {
          e.preventDefault();
          if (canUndo) {
            const prev = undo();
            if (prev) persistBoard(prev);
          }
        }
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") {
        e.preventDefault();
        if (canRedo) {
          const next = redo();
          if (next) persistBoard(next);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [canUndo, canRedo, undo, redo, persistBoard]);

  const handleCreateProject = async (name: string) => {
    if (!user) return;
    const newProj = await createProjectApi(name);
    if (newProj && newProj.id) {
      setProjects((prev) => [...prev, newProj]);
      setActiveProjectId(newProj.id);
    }
  };

  const handleRenameProject = async (projId: string, name: string) => {
    if (!user) return;
    const updated = await updateProjectApi(projId, name);
    if (updated) {
      setProjects((prev) => prev.map((p) => (p.id === projId ? updated : p)));
    }
  };

  const handleDeleteProject = async (projId: string) => {
    if (!user) return;
    const ok = await deleteProjectApi(projId);
    if (ok) {
      const remaining = projects.filter((p) => p.id !== projId);
      setProjects(remaining);
      if (remaining.length > 0) {
        setActiveProjectId(remaining[0].id);
      } else {
        setActiveProjectId(null);
      }
    }
  };

  const pointerSensor = useSensor(PointerSensor, {
    activationConstraint: { distance: 5 },
  });

  const touchSensor = useSensor(TouchSensor, {
    activationConstraint: { delay: 200, tolerance: 8 },
  });

  const mouseSensor = useSensor(MouseSensor, {
    activationConstraint: { distance: 5 },
  });

  const sensors = useSensors(pointerSensor, touchSensor, mouseSensor);

  const collisionDetectionStrategy: CollisionDetection = useCallback((args) => {
    const pointerCollisions = pointerWithin(args);
    if (pointerCollisions.length > 0) {
      return pointerCollisions;
    }
    return rectIntersection(args);
  }, []);

  const cardsById = useMemo(() => board.cards, [board.cards]);
  const availableTags = useMemo(() => extractAvailableTags(board.cards), [board.cards]);

  const filteredBoard = useMemo(() => {
    return filterAndSortBoard(board, filters, sortOption);
  }, [board, filters, sortOption]);

  const activeFilterCount = useMemo(() => {
    return getActiveFilterCount(filters, sortOption);
  }, [filters, sortOption]);

  const handleResetFilters = useCallback(() => {
    setFilters(defaultFilterOptions);
    setSortOption(defaultSortOption);
  }, []);

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
    const res = await loginApi(username, password);
    if (res.success && res.user) {
      setProjects([]);
      setActiveProjectId(null);
      setUser(res.user);
      return true;
    }
    return false;
  };

  const handleLogout = async () => {
    await logoutApi();
    setProjects([]);
    setActiveProjectId(null);
    resetBoard(emptyBoardData);
    setUser(null);
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveCardId(event.active.id as string);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id) {
      return;
    }

    const targetCol = board.columns.find((c) => c.cardIds.includes(over.id as string) || c.id === over.id);
    const destColumnId = targetCol ? targetCol.id : (over.id as string);
    const destPosIndex = targetCol ? targetCol.cardIds.indexOf(over.id as string) : 0;
    const destPosition = destPosIndex >= 0 ? destPosIndex : 0;

    const nextColumns = moveCard(board.columns, active.id as string, over.id as string);
    const nextBoard = { ...board, columns: nextColumns };
    setBoard(nextBoard);

    await moveCardApi(active.id as string, destColumnId, destPosition);
  };

  const handleRenameColumn = async (columnId: string, title: string) => {
    setBoard((prev) => ({
      ...prev,
      columns: prev.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column
      ),
    }));
    await updateColumnApi(columnId, title);
  };

  const handleAddCard = async (columnId: string, title: string, details: string) => {
    if (!user) return;
    setFilters(defaultFilterOptions);
    setSortOption(defaultSortOption);
    const createdCard = await createCardApi(columnId, title, details);
    if (createdCard) {
      const id = createdCard.id;
      setBoard((prev) => ({
        ...prev,
        cards: {
          ...prev.cards,
          [id]: createdCard,
        },
        columns: prev.columns.map((col) =>
          col.id === columnId
            ? { ...col, cardIds: col.cardIds.includes(id) ? col.cardIds : [...col.cardIds, id] }
            : col
        ),
      }));
    }
  };

  const handleDeleteCard = async (columnId: string, cardId: string) => {
    if (!user) return;
    const success = await deleteCardApi(cardId);
    if (success) {
      setBoard((prev) => {
        const nextCards = Object.fromEntries(
          Object.entries(prev.cards).filter(([id]) => id !== cardId)
        );
        const nextColumns = prev.columns.map((column) => ({
          ...column,
          cardIds: column.cardIds.filter((id) => id !== cardId),
        }));
        return {
          columns: nextColumns,
          cards: nextCards,
        };
      });
    } else {
      console.error(`Failed to delete card ${cardId} on server.`);
    }
  };

  const handleClearColumn = async (columnId: string) => {
    const targetCol = board.columns.find((c) => c.id === columnId);
    if (!targetCol) return;
    const success = await clearColumnApi(columnId);
    if (success) {
      const removedIds = new Set(targetCol.cardIds);
      setBoard((prev) => ({
        ...prev,
        cards: Object.fromEntries(
          Object.entries(prev.cards).filter(([id]) => !removedIds.has(id))
        ),
        columns: prev.columns.map((col) =>
          col.id === columnId ? { ...col, cardIds: [] } : col
        ),
      }));
    }
  };

  const handleSaveCard = async (
    cardId: string,
    title: string,
    details: string,
    priority: "high" | "medium" | "low",
    dueDate?: string | null,
    tags?: string[],
    assignee?: string | null
  ) => {
    if (!user) return;
    const res = await updateCardApi(cardId, {
      title,
      details,
      description: details,
      priority,
      dueDate,
      tags,
      assignee,
    });
    if (res) {
      setBoard((prev) => ({
        ...prev,
        cards: {
          ...prev.cards,
          [cardId]: res,
        },
      }));
    } else {
      console.error(`Failed to update card ${cardId} on server.`);
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

  const handleRegisterSuccess = useCallback((username: string) => {
    setProjects([]);
    setActiveProjectId(null);
    setUser(username);
  }, []);

  if (!isAuthLoaded) {
    return null;
  }

  if (!user) {
    return <LoginForm onLogin={handleLogin} onRegisterSuccess={handleRegisterSuccess} />;
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

      <main className="relative mx-auto flex min-h-screen max-w-[1600px] flex-col gap-6 sm:gap-8 px-3 sm:px-6 pb-12 sm:pb-16 pt-4 sm:pt-10 w-full max-w-full overflow-x-hidden">
        {/* Header Section */}
        <header className="flex flex-col gap-6 rounded-2xl sm:rounded-[36px] border border-[var(--stroke)] bg-[var(--card-bg)]/80 p-4 sm:p-8 shadow-[var(--shadow)] backdrop-blur-xl w-full max-w-full overflow-hidden">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 w-full max-w-full">
            <div className="w-full lg:w-auto">
              <div className="flex flex-wrap items-center gap-2 sm:gap-3">
                <ProjectSwitcher
                  projects={projects}
                  activeProjectId={activeProjectId}
                  onSelectProject={setActiveProjectId}
                  onCreateProject={handleCreateProject}
                  onRenameProject={handleRenameProject}
                  onDeleteProject={handleDeleteProject}
                />
                <span className="rounded-full border border-[var(--stroke)] bg-[var(--surface-strong)] px-3 py-1 text-xs font-bold uppercase tracking-wider text-[var(--navy-dark)] shadow-sm">
                  Workspace by YASH 🐐
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
              <h1 className="mt-2 font-display text-3xl sm:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-[var(--navy-dark)] via-[var(--primary-blue)] to-[var(--secondary-purple)] bg-clip-text text-transparent">
                Drag N Drop <span className="inline-block animate-bounce text-2xl sm:text-4xl">✨</span>
              </h1>
              <p className="mt-2 max-w-xl text-xs sm:text-sm leading-relaxed text-[var(--gray-text)]">
                Organize, track, and automate your project workflow seamlessly with interactive drag-and-drop boards and smart AI automation.
              </p>
            </div>

            <div className="flex flex-col sm:items-end gap-3 w-full lg:w-auto">
              <div className="flex flex-wrap items-center gap-2 sm:gap-3 w-full sm:w-auto">
                <button
                  type="button"
                  onClick={() => {
                    const prev = undo();
                    if (prev) persistBoard(prev);
                  }}
                  disabled={!canUndo}
                  className="inline-flex items-center gap-1 rounded-full border border-[var(--stroke)] bg-[var(--surface-strong)] px-3 py-2 text-xs font-bold text-[var(--navy-dark)] shadow-sm transition hover:bg-[var(--stroke)] disabled:opacity-40 disabled:cursor-not-allowed"
                  title="Undo (Ctrl+Z)"
                  aria-label="Undo"
                >
                  <span>↩️</span>
                  <span className="hidden sm:inline">Undo</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const next = redo();
                    if (next) persistBoard(next);
                  }}
                  disabled={!canRedo}
                  className="inline-flex items-center gap-1 rounded-full border border-[var(--stroke)] bg-[var(--surface-strong)] px-3 py-2 text-xs font-bold text-[var(--navy-dark)] shadow-sm transition hover:bg-[var(--stroke)] disabled:opacity-40 disabled:cursor-not-allowed"
                  title="Redo (Ctrl+Y)"
                  aria-label="Redo"
                >
                  <span>↪️</span>
                  <span className="hidden sm:inline">Redo</span>
                </button>
                <button
                  type="button"
                  onClick={() => setIsMembersModalOpen(true)}
                  className="inline-flex items-center gap-1.5 rounded-full border border-[var(--stroke)] bg-[var(--surface-strong)] px-3 py-2 text-xs font-bold text-[var(--navy-dark)] shadow-sm transition hover:bg-[var(--stroke)] focus:outline-none"
                  aria-label="Team Members"
                >
                  <span>👥</span>
                  <span>Members</span>
                </button>
                <button
                  type="button"
                  onClick={() => setIsNotificationsOpen(true)}
                  className="relative inline-flex items-center gap-1.5 rounded-full border border-[var(--stroke)] bg-[var(--surface-strong)] px-3 py-2 text-xs font-bold text-[var(--navy-dark)] shadow-sm transition hover:bg-[var(--stroke)] focus:outline-none"
                  aria-label="Notifications"
                >
                  <span>🔔</span>
                  <span>Alerts</span>
                  {unreadNotifCount > 0 && (
                    <span className="flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-extrabold text-white">
                      {unreadNotifCount}
                    </span>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setIsActivityModalOpen(true)}
                  className="inline-flex items-center gap-1.5 rounded-full border border-[var(--stroke)] bg-[var(--surface-strong)] px-3 py-2 text-xs font-bold text-[var(--navy-dark)] shadow-sm transition hover:bg-[var(--stroke)] focus:outline-none"
                  aria-label="Activity Log"
                >
                  <span>📜</span>
                  <span>Activity Log</span>
                </button>
                <ThemeToggle />
                <div className="flex flex-wrap items-center gap-2 rounded-2xl sm:rounded-full border border-[var(--stroke)] bg-[var(--surface-strong)] px-3 py-2 sm:px-4 sm:py-2 shadow-sm text-xs max-w-full">
                  <span
                    className={`h-2.5 w-2.5 rounded-full ${
                      isWsConnected ? "bg-emerald-500 animate-pulse" : "bg-amber-500"
                    }`}
                    title={isWsConnected ? "Live Sync Active" : "Reconnecting..."}
                  />
                  <span className="font-bold uppercase tracking-wider text-[var(--navy-dark)]">
                    {user}
                  </span>
                  <span className="font-semibold text-[var(--gray-text)] border-l border-[var(--stroke)] pl-2 sm:pl-3">
                    {isSyncing ? "Syncing..." : isWsConnected ? "Live Sync" : "Saved"}
                  </span>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="ml-1 rounded-full bg-red-500/10 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-red-600 transition hover:bg-red-500 hover:text-white"
                  >
                    Logout
                  </button>
                </div>
              </div>

              {/* Progress Bar Component */}
              <div className="flex items-center gap-3 w-full sm:w-72 bg-[var(--surface)] p-2.5 rounded-2xl border border-[var(--stroke)]">
                <div className="flex-1">
                  <div className="flex justify-between text-[11px] font-bold text-[var(--navy-dark)] mb-1">
                    <span>Sprint Completion</span>
                    <span className="text-[var(--primary-blue)]">{completionPercentage}%</span>
                  </div>
                  <div className="h-2 w-full bg-[var(--surface-strong)] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-[var(--primary-blue)] to-emerald-500 transition-all duration-500 rounded-full"
                      style={{ width: `${completionPercentage}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Filtering and Sorting Toolbar */}
          <TaskFilterToolbar
            columns={board.columns}
            availableTags={availableTags}
            filters={filters}
            sort={sortOption}
            activeCount={activeFilterCount}
            onFilterChange={setFilters}
            onSortChange={setSortOption}
            onReset={handleResetFilters}
          />
        </header>

        {/* Dynamic Board Columns */}
        <DndContext
          sensors={sensors}
          collisionDetection={collisionDetectionStrategy}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <section
            aria-label="Project Management Board"
            className="flex-1 rounded-2xl sm:rounded-[36px] border border-[var(--stroke)] bg-[var(--card-bg)]/40 p-3 sm:p-6 shadow-[var(--shadow)] backdrop-blur-md"
          >
            <div className="flex gap-4 sm:gap-6 overflow-x-auto pb-4 pt-1 snap-x no-scrollbar">
              {filteredBoard.columns.map((column) => {
                const cardsInColumn = column.cardIds
                  .map((id) => cardsById[id])
                  .filter(Boolean);

                return (
                  <KanbanColumn
                    key={column.id}
                    column={column}
                    cards={cardsInColumn}
                    onAddCard={handleAddCard}
                    onDeleteCard={handleDeleteCard}
                    onRename={handleRenameColumn}
                    onClearColumn={handleClearColumn}
                    onEditCard={setEditingCard}
                  />
                );
              })}
            </div>
          </section>

          <DragOverlay>
            {activeCard ? <KanbanCardPreview card={activeCard} /> : null}
          </DragOverlay>
        </DndContext>
      </main>

      {/* Task Details & Edit Modal */}
      {editingCard && (
        <EditCardModal
          card={editingCard}
          isOpen={true}
          onClose={() => setEditingCard(null)}
          onSave={handleSaveCard}
        />
      )}

      {/* Audit History & Activity Log Modal */}
      {isActivityModalOpen && activeProjectId && (
        <ActivityHistoryModal
          projectId={activeProjectId}
          projectName={projects.find((p) => p.id === activeProjectId)?.name || "Project"}
          isOpen={isActivityModalOpen}
          onClose={() => setIsActivityModalOpen(false)}
        />
      )}

      {/* Project Team Members Modal */}
      {isMembersModalOpen && activeProjectId && (
        <ProjectMembersModal
          projectId={activeProjectId}
          currentUsername={user}
          isOpen={isMembersModalOpen}
          onClose={() => setIsMembersModalOpen(false)}
        />
      )}

      {/* User Notifications Modal */}
      {isNotificationsOpen && (
        <NotificationCenterModal
          username={user}
          isOpen={isNotificationsOpen}
          onClose={() => setIsNotificationsOpen(false)}
          onNotificationsChanged={refreshNotifications}
        />
      )}

      {/* AI Assistant Floating Widget */}
      <AIAssistantWidget
        board={board}
        projectId={activeProjectId}
        onBoardUpdate={handleBoardUpdateFromAI}
      />
    </div>
  );
};
