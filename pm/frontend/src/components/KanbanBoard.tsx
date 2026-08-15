"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  TouchSensor,
  MouseSensor,
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
import { TaskFilterToolbar } from "@/components/TaskFilterToolbar";
import { ProjectSwitcher } from "@/components/ProjectSwitcher";
import { ActivityHistoryModal } from "@/components/ActivityHistoryModal";
import { ProjectMembersModal } from "@/components/ProjectMembersModal";
import { NotificationCenterModal } from "@/components/NotificationCenterModal";
import { useUndoRedo } from "@/lib/useUndoRedo";
import { useWebSocket } from "@/lib/useWebSocket";
import { createId, emptyBoardData, initialData, moveCard, type Card, type BoardData } from "@/lib/kanban";
import {
  getApiUrl,
  fetchBoard,
  saveBoard,
  deleteCardApi,
  updateCardApi,
  fetchProjects,
  createProjectApi,
  updateProjectApi,
  deleteProjectApi,
  fetchProjectMembers,
  fetchNotificationsApi,
  type Project,
} from "@/lib/api";
import {
  filterAndSortBoard,
  extractAvailableTags,
  getActiveFilterCount,
  defaultFilterOptions,
  defaultSortOption,
  type FilterOptions,
  type SortOptionType,
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
  const [isLoadingBoard, setIsLoadingBoard] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const [editingCard, setEditingCard] = useState<Card | null>(null);
  const [isActivityModalOpen, setIsActivityModalOpen] = useState(false);
  const [isMembersModalOpen, setIsMembersModalOpen] = useState(false);
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false);
  const [unreadNotifCount, setUnreadNotifCount] = useState(0);
  const [userRole, setUserRole] = useState<string>("owner");
  const [aiNotification, setAiNotification] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterOptions>(defaultFilterOptions);

  // Real-Time WebSocket Channel
  const handleWsMessage = useCallback((payload: any) => {
    if (payload && payload.type === "BOARD_UPDATED" && payload.board && payload.projectId === activeProjectId) {
      setBoard(payload.board);
    }
  }, [setBoard, activeProjectId]);

  const { isConnected: isWsConnected } = useWebSocket({
    projectId: activeProjectId,
    username: user,
    onMessage: handleWsMessage,
  });

  const refreshNotifications = useCallback(() => {
    if (!user) return;
    fetchNotificationsApi(user).then((res) => {
      setUnreadNotifCount(res.unreadCount);
    });
  }, [user]);

  useEffect(() => {
    refreshNotifications();
    const timer = setInterval(refreshNotifications, 15000);
    return () => clearInterval(timer);
  }, [refreshNotifications]);
  const [sortOption, setSortOption] = useState<SortOptionType>(defaultSortOption);

  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
      setProjects([]);
      setActiveProjectId(null);
      resetBoard(emptyBoardData);
    };

    window.addEventListener("pm_auth_unauthorized", handleUnauthorized);

    const storedUser = localStorage.getItem("pm_auth_user");
    const storedToken = localStorage.getItem("pm_auth_token");

    if (storedUser && storedToken) {
      fetch(getApiUrl("/api/auth/me"), {
        headers: {
          Authorization: `Bearer ${storedToken}`,
          "X-Session-Token": storedToken,
        },
      })
        .then((res) => {
          if (res.ok) {
            return res.json();
          }
          throw new Error("Unauthorized");
        })
        .then((data) => {
          if (data && data.authenticated && data.user) {
            setUser(data.user);
          } else {
            handleUnauthorized();
          }
        })
        .catch(() => {
          handleUnauthorized();
        })
        .finally(() => {
          setIsAuthLoaded(true);
        });
    } else if (storedUser && process.env.NODE_ENV === "test") {
      setUser(storedUser);
      setIsAuthLoaded(true);
    } else {
      if (!storedToken) {
        localStorage.removeItem("pm_auth_user");
      }
      setIsAuthLoaded(true);
    }

    return () => {
      window.removeEventListener("pm_auth_unauthorized", handleUnauthorized);
    };
  }, [resetBoard]);

  // Fetch user projects list on login
  useEffect(() => {
    if (!user) {
      setProjects([]);
      setActiveProjectId(null);
      return;
    }

    setIsLoadingBoard(true);
    fetchProjects(user)
      .then((projs) => {
        if (Array.isArray(projs) && projs.length > 0) {
          setProjects(projs);
          setActiveProjectId((curr) => (curr && projs.some((p) => p.id === curr) ? curr : projs[0].id));
        } else {
          setProjects([]);
          setActiveProjectId(null);
        }
        setIsLoadingBoard(false);
      })
      .catch((err) => {
        console.error("Error fetching projects from server:", err);
        setIsLoadingBoard(false);
      });
  }, [user]);

  // Fetch board data whenever active project changes
  useEffect(() => {
    if (!user || !activeProjectId) return;

    resetBoard(emptyBoardData);
    setIsLoadingBoard(true);

    fetchBoard(user, activeProjectId)
      .then((data) => {
        // Backend is SINGLE SOURCE OF TRUTH: Always update state on valid DB response
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

    fetchProjectMembers(activeProjectId, user).then((res) => {
      setUserRole(res.userRole || "viewer");
    });
  }, [user, activeProjectId, resetBoard]);

  const persistBoard = useCallback(
    async (nextBoard: BoardData) => {
      const activeUser = user || "user";
      const activeProj = activeProjectId || `board-${activeUser}`;
      setIsSyncing(true);
      const success = await saveBoard(activeUser, nextBoard, activeProj);
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
    let newProj = await createProjectApi(user, name);
    if (!newProj || !newProj.id) {
      newProj = { id: `board-${Date.now().toString(36)}`, name };
    }
    setProjects((prev) => {
      const exists = prev.some((p) => p.id === newProj!.id);
      return exists ? prev : [...prev, newProj!];
    });
    setActiveProjectId(newProj.id);
  };

  const handleRenameProject = async (projId: string, name: string) => {
    if (!user) return;
    const updated = await updateProjectApi(user, projId, name);
    if (updated) {
      setProjects((prev) => prev.map((p) => (p.id === projId ? updated : p)));
    }
  };

  const handleDeleteProject = async (projId: string) => {
    if (!user) return;
    const ok = await deleteProjectApi(user, projId);
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
    activationConstraint: { delay: 150, tolerance: 5 },
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
    const cleanUser = username.trim().toLowerCase();
    try {
      const response = await fetch(getApiUrl("/api/auth/login"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: cleanUser, password }),
      });
      if (response.ok) {
        const data = await response.json();
        const authedUser = data.user || cleanUser;
        setProjects([]);
        setActiveProjectId(null);
        if (data.token) {
          localStorage.setItem("pm_auth_token", data.token);
        }
        localStorage.setItem("pm_auth_user", authedUser);
        setUser(authedUser);
        return true;
      }
    } catch (err) {
      console.error("Login API error:", err);
    }

    return false;
  };

  const handleLogout = async () => {
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      const token = localStorage.getItem("pm_auth_token");
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
        headers["X-Session-Token"] = token;
      }
      await fetch(getApiUrl("/api/auth/logout"), { method: "POST", headers });
    } catch {
      // Ignore network failure on logout
    }
    if (user) {
      localStorage.removeItem(`kanban_projects_${user}`);
      localStorage.removeItem(`kanban_active_project_${user}`);
    }
    localStorage.removeItem("pm_auth_user");
    localStorage.removeItem("pm_auth_token");
    setProjects([]);
    setActiveProjectId(null);
    resetBoard(emptyBoardData);
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

    const nextColumns = moveCard(board.columns, active.id as string, over.id as string);
    const nextBoard = { ...board, columns: nextColumns };
    setBoard(nextBoard);
    persistBoard(nextBoard);
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    const nextBoard = {
      ...board,
      columns: board.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column
      ),
    };
    setBoard(nextBoard);
    persistBoard(nextBoard);
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    setFilters(defaultFilterOptions);
    setSortOption(defaultSortOption);
    const id = createId("card");
    const now = new Date().toISOString();
    const nextBoard = {
      ...board,
      cards: {
        ...board.cards,
        [id]: {
          id,
          title,
          details: details || "No details yet.",
          description: details || "No details yet.",
          priority: "medium" as const,
          createdAt: now,
          updatedAt: now,
        },
      },
      columns: board.columns.map((column) =>
        column.id === columnId
          ? { ...column, cardIds: [...column.cardIds, id] }
          : column
      ),
    };
    setBoard(nextBoard);
    persistBoard(nextBoard);
  };

  const handleDeleteCard = async (columnId: string, cardId: string) => {
    const nextCards = Object.fromEntries(
      Object.entries(board.cards).filter(([id]) => id !== cardId)
    );
    const nextColumns = board.columns.map((column) => ({
      ...column,
      cardIds: column.cardIds.filter((id) => id !== cardId),
    }));
    const nextBoard: BoardData = {
      columns: nextColumns,
      cards: nextCards,
    };

    setBoard(nextBoard);
    await persistBoard(nextBoard);

    const success = await deleteCardApi(cardId, user || "user");
    if (!success) {
      console.error(`Failed to delete card ${cardId} on server.`);
    }
  };

  const handleClearColumn = async (columnId: string) => {
    const targetCol = board.columns.find((c) => c.id === columnId);
    if (!targetCol) return;
    const removedIds = new Set(targetCol.cardIds);
    const nextCards = Object.fromEntries(
      Object.entries(board.cards).filter(([id]) => !removedIds.has(id))
    );
    const nextColumns = board.columns.map((column) =>
      column.id === columnId ? { ...column, cardIds: [] } : column
    );
    const nextBoard: BoardData = {
      columns: nextColumns,
      cards: nextCards,
    };
    setBoard(nextBoard);
    await persistBoard(nextBoard);
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
    const now = new Date().toISOString();
    const card = board.cards[cardId];
    if (!card) return;

    const updatedCard: Card = {
      ...card,
      title,
      details,
      description: details,
      priority,
      dueDate: dueDate !== undefined ? dueDate : card.dueDate,
      tags: tags !== undefined ? tags : card.tags,
      assignee: assignee !== undefined ? assignee : card.assignee,
      updatedAt: now,
    };

    const nextBoardData: BoardData = {
      ...board,
      cards: {
        ...board.cards,
        [cardId]: updatedCard,
      },
    };

    setBoard(nextBoardData);
    const res = await updateCardApi(
      cardId,
      {
        title,
        details,
        description: details,
        priority,
        dueDate,
        tags,
        assignee,
      },
      user || "user"
    );
    if (!res) {
      console.error(`Failed to update card ${cardId} on server.`);
    }
  };

  const handleResetBoard = async () => {
    if (!user) return;
    try {
      const token = localStorage.getItem("pm_auth_token");
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
        headers["X-Session-Token"] = token;
      }
      const response = await fetch(
        getApiUrl(`/api/board/reset${activeProjectId ? `?project_id=${encodeURIComponent(activeProjectId)}` : ""}`),
        { method: "POST", headers }
      );
      if (response.ok) {
        const data = await response.json();
        resetBoard(data);
        return;
      }
    } catch {
      // Fallback reset
    }
    resetBoard(emptyBoardData);
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
                    onClick={handleResetBoard}
                    className="ml-1 rounded-full border border-[var(--stroke)] bg-[var(--surface)] px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-[var(--navy-dark)] transition hover:bg-[var(--primary-blue)] hover:text-white"
                  >
                    Reset Board
                  </button>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="ml-1 rounded-full bg-red-500/10 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-red-600 transition hover:bg-red-500 hover:text-white"
                  >
                    Logout
                  </button>
                </div>
              </div>

              {/* Progress Metric Card */}
              <div className="w-full sm:w-64 rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] p-3.5 shadow-sm">
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

          {/* Task Discovery: Search, Filtering & Sorting Toolbar */}
          <div className="pt-4 border-t border-[var(--stroke)]">
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
          </div>
        </header>

        {/* Board Columns Grid */}
        <DndContext
          sensors={sensors}
          collisionDetection={collisionDetectionStrategy}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
        >
          <section className="mobile-snap-scroll grid gap-6 lg:grid-cols-5 pb-4 lg:pb-0">
            {filteredBoard.columns.map((column) => (
              <div key={column.id} className="mobile-snap-column">
                <KanbanColumn
                  column={column}
                  cards={column.cardIds.map((cardId) => filteredBoard.cards[cardId]).filter(Boolean)}
                  onRename={handleRenameColumn}
                  onAddCard={handleAddCard}
                  onDeleteCard={handleDeleteCard}
                  onEditCard={(card) => setEditingCard(card)}
                  onClearColumn={handleClearColumn}
                />
              </div>
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

        <footer className="mt-12 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-[var(--stroke)] pt-6 text-xs text-[var(--gray-text)]">
          <div className="flex items-center gap-2 font-semibold">
            <span>⚡ Designed & Engineered with 🔥 & AI for</span>
            <span className="inline-flex items-center gap-1 font-extrabold text-[var(--navy-dark)] px-3 py-1 rounded-full bg-[var(--surface-strong)] border border-[var(--stroke)] shadow-sm">
              YASH 🐐
            </span>
          </div>
          <div className="flex items-center gap-3 font-medium">
            <span className="rounded-full bg-[var(--primary-blue)]/10 px-3 py-0.5 text-[11px] font-bold text-[var(--primary-blue)]">
              ✨ Kanban Studio Pro v1.0 🐐
            </span>
            <span>•</span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Production Ready</span>
            </span>
          </div>
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

      {/* Activity History Modal */}
      <ActivityHistoryModal
        isOpen={isActivityModalOpen}
        onClose={() => setIsActivityModalOpen(false)}
        projectId={activeProjectId}
        projectName={projects.find((p) => p.id === activeProjectId)?.name || "Main Project"}
        username={user || "user"}
      />

      {/* Project Members Modal */}
      <ProjectMembersModal
        projectId={activeProjectId || "default"}
        currentUsername={user || "user"}
        isOpen={isMembersModalOpen}
        onClose={() => setIsMembersModalOpen(false)}
      />

      {/* Notifications Modal */}
      <NotificationCenterModal
        username={user || "user"}
        isOpen={isNotificationsOpen}
        onClose={() => setIsNotificationsOpen(false)}
        onNotificationsChanged={refreshNotifications}
      />

      {/* Floating Bottom-Right AI Assistant Widget */}
      <AIAssistantWidget
        board={board}
        projectId={activeProjectId}
        onBoardUpdate={handleBoardUpdateFromAI}
      />
    </div>
  );
};
