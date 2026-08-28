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
  KeyboardSensor,
  type CollisionDetection,
  pointerWithin,
  rectIntersection,
} from "@dnd-kit/core";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
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
import { SpatialBackground } from "@/components/SpatialBackground";
import { CommandPalette } from "@/components/CommandPalette";
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
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [unreadNotifCount, setUnreadNotifCount] = useState(0);
  const [, setUserRole] = useState<string>("owner");
  const [aiNotification, setAiNotification] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterOptions>(defaultFilterOptions);
  const [sortOption, setSortOption] = useState<SortOptionType>(defaultSortOption);

  const showToast = useCallback((msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  }, []);

  // Real-Time WebSocket Channel
  const handleWsMessage = useCallback((payload: unknown) => {
    const data = payload as { type?: string; board?: BoardData; projectId?: string };
    if (data && data.type === "BOARD_UPDATED" && data.board && data.projectId === activeProjectId) {
      setBoard(data.board);
      showToast("⚡ Board synchronized with live changes");
    }
  }, [setBoard, activeProjectId, showToast]);

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

  // Initial Auth Verification
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
      queueMicrotask(() => {
        setProjects([]);
        setActiveProjectId(null);
      });
      return;
    }

    let isMounted = true;
    queueMicrotask(() => setIsLoadingBoard(true));

    fetchProjects()
      .then((projs) => {
        if (!isMounted) return;
        if (Array.isArray(projs) && projs.length > 0) {
          setProjects(projs);
          setActiveProjectId((curr) => (curr && projs.some((p) => p.id === curr) ? curr : projs[0].id));
        } else {
          setProjects([]);
          setActiveProjectId(null);
        }
      })
      .catch((err) => {
        if (isMounted) console.error("Error fetching projects from server:", err);
      })
      .finally(() => {
        if (isMounted) setIsLoadingBoard(false);
      });

    return () => {
      isMounted = false;
    };
  }, [user]);

  // Fetch board data whenever active project changes
  useEffect(() => {
    if (!user || !activeProjectId) {
      queueMicrotask(() => resetBoard(emptyBoardData));
      return;
    }

    let isMounted = true;
    queueMicrotask(() => {
      resetBoard(emptyBoardData);
      setIsLoadingBoard(true);
    });

    fetchBoard(activeProjectId)
      .then((data) => {
        if (!isMounted) return;
        if (data && data.columns && Array.isArray(data.columns)) {
          resetBoard(data);
        }
      })
      .catch((err) => {
        if (isMounted) console.error("Error fetching board from backend:", err);
      })
      .finally(() => {
        if (isMounted) setIsLoadingBoard(false);
      });

    fetchProjectMembers(activeProjectId).then((res) => {
      if (isMounted) setUserRole(res.userRole || "viewer");
    });

    return () => {
      isMounted = false;
    };
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

  // Global Keyboard Shortcuts (Ctrl+K, Undo Ctrl+Z, Redo Ctrl+Y / Shift+Z)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Command Palette (Ctrl+K / Cmd+K)
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
        return;
      }

      const targetTag = (e.target as HTMLElement)?.tagName;
      if (["INPUT", "TEXTAREA", "SELECT"].includes(targetTag)) return;

      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
        if (e.shiftKey) {
          e.preventDefault();
          if (canRedo) {
            const next = redo();
            if (next) {
              persistBoard(next);
              showToast("↪️ Reapplied board action");
            }
          }
        } else {
          e.preventDefault();
          if (canUndo) {
            const prev = undo();
            if (prev) {
              persistBoard(prev);
              showToast("↩️ Reverted last board action");
            }
          }
        }
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") {
        e.preventDefault();
        if (canRedo) {
          const next = redo();
          if (next) {
            persistBoard(next);
            showToast("↪️ Reapplied board action");
          }
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [canUndo, canRedo, undo, redo, persistBoard, showToast]);

  const handleCreateProject = async (name: string) => {
    if (!user) return;
    const newProj = await createProjectApi(name);
    if (newProj && newProj.id) {
      setProjects((prev) => [...prev, newProj]);
      setActiveProjectId(newProj.id);
      showToast(`📁 Created project "${name}"`);
    }
  };

  const handleRenameProject = async (projId: string, name: string) => {
    if (!user) return;
    const updated = await updateProjectApi(projId, name);
    if (updated) {
      setProjects((prev) => prev.map((p) => (p.id === projId ? updated : p)));
      showToast(`📝 Renamed project to "${name}"`);
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
      showToast("🗑️ Project deleted");
    }
  };

  const pointerSensor = useSensor(PointerSensor, {
    activationConstraint: { distance: 3 },
  });

  const keyboardSensor = useSensor(KeyboardSensor, {
    coordinateGetter: sortableKeyboardCoordinates,
  });

  const sensors = useSensors(pointerSensor, keyboardSensor);

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
    showToast("↺ Filters reset to default view");
  }, [showToast]);

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

    try {
      const createdCard = await createCardApi(columnId, title, details);
      if (createdCard && createdCard.id) {
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
        showToast(`➕ Added task "${title}"`);
        return;
      }
    } catch {
      // Fallback below
    }

    // Seamless offline/instant fallback
    const fallbackId = `card-${Date.now()}`;
    const fallbackCard: Card = {
      id: fallbackId,
      title,
      details,
      description: details,
      priority: "medium",
      tags: [],
    };
    setBoard((prev) => ({
      ...prev,
      cards: {
        ...prev.cards,
        [fallbackId]: fallbackCard,
      },
      columns: prev.columns.map((col) =>
        col.id === columnId ? { ...col, cardIds: [...col.cardIds, fallbackId] } : col
      ),
    }));
    showToast(`➕ Added task "${title}"`);
  };

  const handleDeleteCard = async (columnId: string, cardId: string) => {
    if (!user) return;

    // Instant optimistic removal from board state
    setBoard((prev) => ({
      ...prev,
      cards: Object.fromEntries(
        Object.entries(prev.cards).filter(([id]) => id !== cardId)
      ),
      columns: prev.columns.map((column) => ({
        ...column,
        cardIds: column.cardIds.filter((id) => id !== cardId),
      })),
    }));
    showToast("🗑️ Task deleted");

    deleteCardApi(cardId).catch((err) => {
      console.warn(`Card deletion on server error for ${cardId}:`, err);
    });
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
      showToast(`🧹 Cleared all tasks in ${targetCol.title}`);
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
      showToast(`✏️ Updated "${title}"`);
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

  const handleToggleTheme = useCallback(() => {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const next = current === "light" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("pm_theme", next);
  }, []);

  if (!isAuthLoaded) {
    return null;
  }

  if (!user) {
    return <LoginForm onLogin={handleLogin} onRegisterSuccess={handleRegisterSuccess} />;
  }

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  return (
    <div className="relative overflow-hidden min-h-screen spatial-perspective select-text">
      {/* Layer 0: Spatial Environment Canvas (Matrix Grid & Ambient Illumination) */}
      <SpatialBackground />

      {/* Real-Time Toast Notifications */}
      {toastMessage && (
        <div className="fixed top-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 rounded-2xl border border-[var(--stroke-strong)] bg-[var(--surface-floating)] px-4 py-2.5 shadow-2xl backdrop-blur-2xl animate-in fade-in slide-in-from-top-3 duration-200">
          <span className="text-xs font-semibold text-[var(--navy-dark)]">
            {toastMessage}
          </span>
        </div>
      )}

      {/* Floating AI Notification Banner */}
      {aiNotification && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-3 rounded-2xl border border-[var(--accent-amber)] bg-[var(--surface-floating)] px-5 py-3 shadow-2xl backdrop-blur-2xl animate-in fade-in slide-in-from-top-4 duration-300">
          <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-[var(--accent-amber)] text-black text-sm font-bold shadow-md">
            ✨
          </span>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--accent-amber)] font-mono">
              AI Command Core Action
            </p>
            <p className="text-xs font-semibold text-[var(--navy-dark)]">
              {aiNotification}
            </p>
          </div>
        </div>
      )}

      {/* Main Command Center Chassis */}
      <main className="relative mx-auto flex min-h-screen max-w-[1680px] flex-col gap-5 sm:gap-6 px-3 sm:px-6 pb-12 sm:pb-16 pt-4 sm:pt-6 w-full max-w-full overflow-x-hidden z-10">
        {/* Layer 1: Spatial Command Header */}
        <header className="flex flex-col gap-4 rounded-3xl glass-panel p-4 sm:p-6 shadow-[var(--shadow)] backdrop-blur-2xl w-full max-w-full overflow-hidden">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5 w-full max-w-full">
            {/* Left Header Section: Project, Badges, Title */}
            <div className="w-full lg:w-auto">
              <div className="flex flex-wrap items-center gap-2 sm:gap-2.5">
                <ProjectSwitcher
                  projects={projects}
                  activeProjectId={activeProjectId}
                  onSelectProject={setActiveProjectId}
                  onCreateProject={handleCreateProject}
                  onRenameProject={handleRenameProject}
                  onDeleteProject={handleDeleteProject}
                />
                <span className="rounded-full border border-[var(--stroke)] bg-[var(--surface-input)] px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-[var(--navy-dark)] shadow-2xs font-mono">
                  Workspace by YASH 🐐
                </span>
                <span className="rounded-full bg-[var(--surface-input)] border border-[var(--stroke)] px-3 py-0.5 text-[11px] font-semibold text-[var(--navy-dark)] font-mono">
                  {totalTasks} Total Tasks
                </span>
                {highPriorityCount > 0 && (
                  <span className="rounded-full bg-red-500/15 border border-red-500/30 px-3 py-0.5 text-[11px] font-bold text-red-500 font-mono">
                    🔥 {highPriorityCount} High Priority
                  </span>
                )}
              </div>

              <div className="mt-2.5 flex flex-wrap items-baseline gap-3">
                <h1 className="font-display text-2xl sm:text-4xl font-extrabold tracking-tight text-[var(--navy-dark)]">
                  Drag N Drop <span className="inline-block animate-float text-xl sm:text-3xl">✨</span>
                </h1>
                <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--accent-amber)] font-mono bg-[var(--accent-amber)]/10 px-2 py-0.5 rounded-md border border-[var(--accent-amber)]/25">
                  Spatial Command Center
                </span>
              </div>
              <p className="mt-1 max-w-xl text-xs sm:text-sm leading-relaxed text-[var(--gray-text)]">
                Organize, track, and automate your project workflow seamlessly with interactive drag-and-drop boards and smart AI automation.
              </p>
            </div>

            {/* Right Header Section: Command Bar, Micro-Actions & Velocity */}
            <div className="flex flex-col sm:items-end gap-3 w-full lg:w-auto">
              <div className="flex flex-wrap items-center gap-2 sm:gap-2.5 w-full sm:w-auto">
                {/* Command Palette Trigger */}
                <button
                  type="button"
                  onClick={() => setIsCommandPaletteOpen(true)}
                  className="inline-flex items-center gap-2 rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-3.5 py-1.5 text-xs font-semibold text-[var(--navy-dark)] shadow-2xs transition hover:border-[var(--accent-amber)] hover:bg-[var(--surface-column)]"
                  title="Open Command Palette (Ctrl+K)"
                  aria-label="Open Command Palette"
                >
                  <span>🔍</span>
                  <span className="hidden sm:inline">Commands</span>
                  <kbd className="rounded-md border border-[var(--stroke)] bg-[var(--surface-column)] px-1.5 py-0.2 text-[10px] font-mono text-[var(--gray-text)]">
                    ⌘K
                  </kbd>
                </button>

                {/* Undo / Redo */}
                <button
                  type="button"
                  onClick={() => {
                    const prev = undo();
                    if (prev) {
                      persistBoard(prev);
                      showToast("↩️ Reverted last board action");
                    }
                  }}
                  disabled={!canUndo}
                  className="inline-flex items-center gap-1 rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-3 py-1.5 text-xs font-bold text-[var(--navy-dark)] shadow-2xs transition hover:bg-[var(--surface-column)] disabled:opacity-40 disabled:cursor-not-allowed"
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
                    if (next) {
                      persistBoard(next);
                      showToast("↪️ Reapplied board action");
                    }
                  }}
                  disabled={!canRedo}
                  className="inline-flex items-center gap-1 rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-3 py-1.5 text-xs font-bold text-[var(--navy-dark)] shadow-2xs transition hover:bg-[var(--surface-column)] disabled:opacity-40 disabled:cursor-not-allowed"
                  title="Redo (Ctrl+Y)"
                  aria-label="Redo"
                >
                  <span>↪️</span>
                  <span className="hidden sm:inline">Redo</span>
                </button>

                {/* Modal Triggers */}
                <button
                  type="button"
                  onClick={() => setIsMembersModalOpen(true)}
                  className="inline-flex items-center gap-1.5 rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-3 py-1.5 text-xs font-bold text-[var(--navy-dark)] shadow-2xs transition hover:bg-[var(--surface-column)] focus:outline-none"
                  aria-label="Team Members"
                >
                  <span>👥</span>
                  <span>Members</span>
                </button>
                <button
                  type="button"
                  onClick={() => setIsNotificationsOpen(true)}
                  className="relative inline-flex items-center gap-1.5 rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-3 py-1.5 text-xs font-bold text-[var(--navy-dark)] shadow-2xs transition hover:bg-[var(--surface-column)] focus:outline-none"
                  aria-label="Notifications"
                >
                  <span>🔔</span>
                  <span>Alerts</span>
                  {unreadNotifCount > 0 && (
                    <span className="flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[9px] font-extrabold text-white font-mono">
                      {unreadNotifCount}
                    </span>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => setIsActivityModalOpen(true)}
                  className="inline-flex items-center gap-1.5 rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-3 py-1.5 text-xs font-bold text-[var(--navy-dark)] shadow-2xs transition hover:bg-[var(--surface-column)] focus:outline-none"
                  aria-label="Activity Log"
                >
                  <span>📜</span>
                  <span>Activity Log</span>
                </button>
                <ThemeToggle />

                {/* Live Sync User Status Pill */}
                <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-3 py-1.5 shadow-2xs text-xs max-w-full font-mono">
                  <span
                    className={`h-2 w-2 rounded-full ${
                      isWsConnected ? "bg-emerald-500 animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.6)]" : "bg-amber-500"
                    }`}
                    title={isWsConnected ? "Live Sync Active" : "Reconnecting..."}
                  />
                  <span className="font-bold text-[var(--navy-dark)]">
                    @{user}
                  </span>
                  <span className="text-[11px] font-semibold text-[var(--gray-text)] border-l border-[var(--stroke)] pl-2">
                    {isSyncing ? "Syncing..." : isWsConnected ? "Live" : "Saved"}
                  </span>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="ml-1 rounded-lg bg-red-500/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-red-500 transition hover:bg-red-500 hover:text-white"
                  >
                    Logout
                  </button>
                </div>
              </div>

              {/* Sprint Velocity Progress Component */}
              <div className="flex items-center gap-3 w-full sm:w-80 bg-[var(--surface-input)] p-2.5 rounded-2xl border border-[var(--stroke)]">
                <div className="flex-1">
                  <div className="flex justify-between text-[10px] font-bold uppercase tracking-wider text-[var(--navy-dark)] mb-1 font-mono">
                    <span>Sprint Velocity</span>
                    <span className="text-[var(--accent-amber)] font-extrabold">{completionPercentage}%</span>
                  </div>
                  <div className="h-1.5 w-full bg-[var(--surface-column)] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-[var(--accent-amber)] to-[var(--accent-emerald)] transition-all duration-500 rounded-full"
                      style={{ width: `${completionPercentage}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Filtering and Sorting Command Bar */}
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

        {/* Layer 2: Dynamic Spatial Board Columns */}
        <DndContext
          sensors={sensors}
          collisionDetection={collisionDetectionStrategy}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <section
            aria-label="Project Management Board"
            className="flex-1 rounded-3xl glass-panel p-3 sm:p-5 shadow-[var(--shadow)] backdrop-blur-md"
          >
            <div className="mobile-snap-scroll pb-2 pt-1 no-scrollbar">
              {filteredBoard.columns.map((column) => {
                const cardsInColumn = column.cardIds
                  .map((id) => cardsById[id])
                  .filter(Boolean);

                return (
                  <div key={column.id} className="mobile-snap-column">
                    <KanbanColumn
                      column={column}
                      cards={cardsInColumn}
                      onAddCard={handleAddCard}
                      onDeleteCard={handleDeleteCard}
                      onRename={handleRenameColumn}
                      onClearColumn={handleClearColumn}
                      onEditCard={setEditingCard}
                    />
                  </div>
                );
              })}
            </div>
          </section>

          {/* Layer 4: Drag Overlay with Physical Depth */}
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

      {/* Developer-Grade Command Palette (Ctrl+K) */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        board={board}
        projects={projects}
        activeProjectId={activeProjectId}
        onSelectProject={setActiveProjectId}
        onOpenAI={() => {
          setIsCommandPaletteOpen(false);
          // AI Widget trigger
        }}
        onOpenMembers={() => setIsMembersModalOpen(true)}
        onOpenActivity={() => setIsActivityModalOpen(true)}
        onOpenNotifications={() => setIsNotificationsOpen(true)}
        onSelectCard={(c) => setEditingCard(c)}
        onFilterChange={setFilters}
        onResetFilters={handleResetFilters}
        onUndo={() => {
          const prev = undo();
          if (prev) {
            persistBoard(prev);
            showToast("↩️ Reverted last board action");
          }
        }}
        onRedo={() => {
          const next = redo();
          if (next) {
            persistBoard(next);
            showToast("↪️ Reapplied board action");
          }
        }}
        canUndo={canUndo}
        canRedo={canRedo}
        onToggleTheme={handleToggleTheme}
        onQuickAddTask={() => {
          const firstCol = board.columns[0];
          if (firstCol) {
            handleAddCard(firstCol.id, "New Task", "Created via Command Palette");
          }
        }}
      />

      {/* Layer 5: Signature Floating AI Command Core / Gyro Orb */}
      <AIAssistantWidget
        board={board}
        projectId={activeProjectId}
        onBoardUpdate={handleBoardUpdateFromAI}
      />
    </div>
  );
};
