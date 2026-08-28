"use client";

import { useState, useEffect, useMemo, useRef } from "react";
import type { BoardData, Card } from "@/lib/kanban";
import type { Project } from "@/lib/api";
import type { FilterOptions, SortOptionType } from "@/lib/filterUtils";

type CommandPaletteProps = {
  isOpen: boolean;
  onClose: () => void;
  board: BoardData;
  projects: Project[];
  activeProjectId: string | null;
  onSelectProject: (projectId: string) => void;
  onOpenAI: () => void;
  onOpenMembers: () => void;
  onOpenActivity: () => void;
  onOpenNotifications: () => void;
  onSelectCard: (card: Card) => void;
  onFilterChange: (filters: FilterOptions) => void;
  onResetFilters: () => void;
  onUndo: () => void;
  onRedo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  onToggleTheme: () => void;
  onQuickAddTask?: () => void;
};

type PaletteItem = {
  id: string;
  category: "Tasks" | "Actions" | "Navigation" | "Projects";
  title: string;
  subtitle?: string;
  icon: string;
  badge?: string;
  badgeColor?: string;
  shortcut?: string;
  action: () => void;
};

export const CommandPalette = ({
  isOpen,
  onClose,
  board,
  projects,
  onSelectProject,
  onOpenAI,
  onOpenMembers,
  onOpenActivity,
  onOpenNotifications,
  onSelectCard,
  onFilterChange,
  onResetFilters,
  onUndo,
  onRedo,
  canUndo,
  canRedo,
  onToggleTheme,
  onQuickAddTask,
}: CommandPaletteProps) => {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Build searchable items list
  const allItems: PaletteItem[] = useMemo(() => {
    const items: PaletteItem[] = [];

    // 1. Task cards from board
    const cards = Object.values(board.cards || {});
    const columnMap = new Map<string, string>();
    board.columns.forEach((col) => {
      col.cardIds.forEach((cid) => columnMap.set(cid, col.title));
    });

    cards.forEach((c) => {
      const colTitle = columnMap.get(c.id) || "Board";
      const priorityColor =
        c.priority === "high"
          ? "bg-red-500/20 text-red-400 border-red-500/30"
          : c.priority === "medium"
          ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
          : "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";

      items.push({
        id: `card-${c.id}`,
        category: "Tasks",
        title: c.title,
        subtitle: c.details || c.description || `In column: ${colTitle}`,
        icon: "📋",
        badge: colTitle,
        badgeColor: priorityColor,
        action: () => {
          onClose();
          onSelectCard(c);
        },
      });
    });

    // 2. Quick Command Actions
    items.push({
      id: "act-ai",
      category: "Actions",
      title: "Open AI Command Core",
      subtitle: "Ask AI to reorganize, summarize, or automate tasks",
      icon: "✨",
      shortcut: "AI",
      action: () => {
        onClose();
        onOpenAI();
      },
    });

    if (onQuickAddTask) {
      items.push({
        id: "act-new-task",
        category: "Actions",
        title: "Create New Task",
        subtitle: "Add a new task card to the backlog",
        icon: "➕",
        shortcut: "N",
        action: () => {
          onClose();
          onQuickAddTask();
        },
      });
    }

    if (canUndo) {
      items.push({
        id: "act-undo",
        category: "Actions",
        title: "Undo Last Action",
        subtitle: "Revert board change",
        icon: "↩️",
        shortcut: "Ctrl+Z",
        action: () => {
          onClose();
          onUndo();
        },
      });
    }

    if (canRedo) {
      items.push({
        id: "act-redo",
        category: "Actions",
        title: "Redo Action",
        subtitle: "Reapply previously reverted board change",
        icon: "↪️",
        shortcut: "Ctrl+Y",
        action: () => {
          onClose();
          onRedo();
        },
      });
    }

    items.push({
      id: "act-filter-high",
      category: "Actions",
      title: "Filter by High Priority",
      subtitle: "Show only urgent and high priority tasks",
      icon: "🔥",
      action: () => {
        onClose();
        onFilterChange({
          searchQuery: "",
          priority: "high",
          columnId: "all",
          tag: "all",
          dueDateFilter: "all",
        });
      },
    });

    items.push({
      id: "act-filter-overdue",
      category: "Actions",
      title: "Filter Overdue Tasks",
      subtitle: "Show tasks past their due date",
      icon: "⚠️",
      action: () => {
        onClose();
        onFilterChange({
          searchQuery: "",
          priority: "all",
          columnId: "all",
          tag: "all",
          dueDateFilter: "overdue",
        });
      },
    });

    items.push({
      id: "act-reset-filters",
      category: "Actions",
      title: "Clear All Filters",
      subtitle: "Show full board unfiltered",
      icon: "↺",
      action: () => {
        onClose();
        onResetFilters();
      },
    });

    items.push({
      id: "act-theme",
      category: "Actions",
      title: "Toggle Theme Mode",
      subtitle: "Switch between Dark and Light spatial interface",
      icon: "🌓",
      action: () => {
        onClose();
        onToggleTheme();
      },
    });

    // 3. Navigation
    items.push({
      id: "nav-members",
      category: "Navigation",
      title: "Team Members & Permissions",
      subtitle: "Manage workspace collaborators and RBAC roles",
      icon: "👥",
      action: () => {
        onClose();
        onOpenMembers();
      },
    });

    items.push({
      id: "nav-activity",
      category: "Navigation",
      title: "Audit Activity Log",
      subtitle: "View audit trail of project changes",
      icon: "📜",
      action: () => {
        onClose();
        onOpenActivity();
      },
    });

    items.push({
      id: "nav-notifs",
      category: "Navigation",
      title: "Notification Alerts",
      subtitle: "Check upcoming task deadlines and invitations",
      icon: "🔔",
      action: () => {
        onClose();
        onOpenNotifications();
      },
    });

    // 4. Projects Switcher
    projects.forEach((proj) => {
      items.push({
        id: `proj-${proj.id}`,
        category: "Projects",
        title: `Switch to: ${proj.name}`,
        subtitle: `Project ID: ${proj.id}`,
        icon: "📁",
        action: () => {
          onClose();
          onSelectProject(proj.id);
        },
      });
    });

    return items;
  }, [
    board,
    projects,
    canUndo,
    canRedo,
    onClose,
    onSelectCard,
    onOpenAI,
    onQuickAddTask,
    onUndo,
    onRedo,
    onFilterChange,
    onResetFilters,
    onToggleTheme,
    onOpenMembers,
    onOpenActivity,
    onOpenNotifications,
    onSelectProject,
  ]);

  // Filter items matching query
  const filteredItems = useMemo(() => {
    if (!query.trim()) return allItems;
    const q = query.toLowerCase().trim();
    return allItems.filter(
      (item) =>
        item.title.toLowerCase().includes(q) ||
        (item.subtitle && item.subtitle.toLowerCase().includes(q)) ||
        item.category.toLowerCase().includes(q)
    );
  }, [allItems, query]);

  // Reset selected index when filtered items change
  useEffect(() => {
    setSelectedIndex(0);
  }, [filteredItems]);

  // Scroll active item into view
  useEffect(() => {
    if (!listRef.current) return;
    const activeEl = listRef.current.querySelector(`[data-index="${selectedIndex}"]`);
    if (activeEl) {
      activeEl.scrollIntoView({ block: "nearest" });
    }
  }, [selectedIndex]);

  // Keyboard navigation inside palette
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      e.preventDefault();
      onClose();
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, filteredItems.length));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filteredItems.length) % Math.max(1, filteredItems.length));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const selected = filteredItems[selectedIndex];
      if (selected) {
        selected.action();
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 px-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-150"
      onClick={onClose}
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-label="Command Palette"
    >
      <div
        className="w-full max-w-2xl rounded-3xl glass-floating p-2 shadow-2xl flex flex-col max-h-[75vh] overflow-hidden animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[var(--stroke)]">
          <span className="text-base opacity-70">🔍</span>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command or search tasks across the board..."
            className="w-full bg-transparent text-sm font-semibold text-[var(--navy-dark)] outline-none placeholder:text-[var(--gray-text)]"
            aria-label="Command search input"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="text-xs text-[var(--gray-text)] hover:text-[var(--navy-dark)] px-1.5 py-0.5 rounded"
            >
              ✕
            </button>
          )}
          <kbd className="hidden sm:inline-flex items-center gap-1 rounded-lg border border-[var(--stroke)] bg-[var(--surface-input)] px-2 py-0.5 text-[10px] font-bold text-[var(--gray-text)]">
            ESC
          </kbd>
        </div>

        {/* Results List */}
        <div ref={listRef} className="flex-1 overflow-y-auto p-2 space-y-1 scrollbar-none">
          {filteredItems.length === 0 ? (
            <div className="py-12 text-center text-xs font-semibold text-[var(--gray-text)]">
              No matching tasks or commands found for &ldquo;{query}&rdquo;
            </div>
          ) : (
            filteredItems.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.id}
                  data-index={idx}
                  onClick={() => item.action()}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-2xl cursor-pointer transition-all duration-150 ${
                    isSelected
                      ? "bg-[var(--accent-amber)]/15 border border-[var(--accent-amber)]/40 shadow-sm translate-x-1"
                      : "hover:bg-[var(--surface-column)] border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="text-base flex-shrink-0">{item.icon}</span>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-[var(--navy-dark)] truncate">
                          {item.title}
                        </span>
                        {item.badge && (
                          <span
                            className={`rounded-md px-1.5 py-0.2 text-[9px] font-bold border uppercase tracking-wider ${
                              item.badgeColor || "bg-[var(--stroke)] text-[var(--gray-text)]"
                            }`}
                          >
                            {item.badge}
                          </span>
                        )}
                      </div>
                      {item.subtitle && (
                        <p className="text-[11px] text-[var(--gray-text)] truncate mt-0.5">
                          {item.subtitle}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 flex-shrink-0">
                    {item.shortcut && (
                      <kbd className="rounded-md border border-[var(--stroke)] bg-[var(--surface-input)] px-1.5 py-0.5 text-[10px] font-mono text-[var(--gray-text)]">
                        {item.shortcut}
                      </kbd>
                    )}
                    {isSelected && (
                      <span className="text-[10px] font-bold text-[var(--accent-amber)]">
                        ↵
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer info */}
        <div className="flex items-center justify-between px-4 py-2 text-[10px] font-semibold text-[var(--gray-text)] border-t border-[var(--stroke)] bg-[var(--surface-input)]/50 rounded-b-2xl">
          <div className="flex items-center gap-3">
            <span>
              <kbd className="font-mono">↑↓</kbd> Navigate
            </span>
            <span>
              <kbd className="font-mono">↵</kbd> Select
            </span>
            <span>
              <kbd className="font-mono">ESC</kbd> Close
            </span>
          </div>
          <span>{filteredItems.length} items available</span>
        </div>
      </div>
    </div>
  );
};
