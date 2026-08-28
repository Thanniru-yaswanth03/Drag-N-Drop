"use client";

import type { Column } from "@/lib/kanban";
import {
  type FilterOptions,
  type SortOptionType,
  type DueDateFilterType,
  type PriorityFilterType,
} from "@/lib/filterUtils";

type TaskFilterToolbarProps = {
  columns: Column[];
  availableTags: string[];
  filters: FilterOptions;
  sort: SortOptionType;
  activeCount: number;
  onFilterChange: (nextFilters: FilterOptions) => void;
  onSortChange: (nextSort: SortOptionType) => void;
  onReset: () => void;
};

export const TaskFilterToolbar = ({
  columns,
  availableTags,
  filters,
  sort,
  activeCount,
  onFilterChange,
  onSortChange,
  onReset,
}: TaskFilterToolbarProps) => {
  const updateFilter = <K extends keyof FilterOptions>(
    key: K,
    value: FilterOptions[K]
  ) => {
    onFilterChange({ ...filters, [key]: value });
  };

  return (
    <div className="flex flex-col gap-3 rounded-2xl sm:rounded-3xl border border-[var(--stroke)] bg-[var(--surface-column)]/60 p-3 sm:p-4 shadow-[var(--shadow)] backdrop-blur-xl">
      {/* Top Row: Search Input & Sort & Reset Button */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Global Search Bar */}
        <div className="flex flex-1 items-center gap-2.5 min-w-[240px] rounded-xl border border-[var(--stroke)] bg-[var(--surface-input)] px-3.5 py-2 shadow-2xs transition focus-within:border-[var(--accent-amber)]">
          <span className="text-xs opacity-60">🔍</span>
          <input
            type="text"
            value={filters.searchQuery}
            onChange={(e) => updateFilter("searchQuery", e.target.value)}
            placeholder="Search tasks by title or description..."
            className="w-full bg-transparent text-xs font-medium text-[var(--navy-dark)] outline-none placeholder:text-[var(--gray-text)]"
            aria-label="Search tasks"
          />
          {filters.searchQuery && (
            <button
              type="button"
              onClick={() => updateFilter("searchQuery", "")}
              className="text-xs text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
              aria-label="Clear search"
            >
              ✕
            </button>
          )}
        </div>

        {/* Sort Selector & Reset Actions */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 rounded-xl border border-[var(--stroke)] bg-[var(--surface-input)] px-3 py-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--gray-text)] font-mono">
              Sort:
            </span>
            <select
              value={sort}
              onChange={(e) => onSortChange(e.target.value as SortOptionType)}
              className="bg-transparent text-xs font-semibold text-[var(--navy-dark)] outline-none cursor-pointer"
              aria-label="Sort tasks by"
            >
              <option value="default">Default Order</option>
              <option value="created-desc">Newest Created</option>
              <option value="created-asc">Oldest Created</option>
              <option value="updated-desc">Recently Updated</option>
              <option value="due-asc">Earliest Due Date</option>
              <option value="due-desc">Latest Due Date</option>
              <option value="priority-desc">Highest Priority</option>
              <option value="priority-asc">Lowest Priority</option>
              <option value="title-asc">Title (A - Z)</option>
              <option value="title-desc">Title (Z - A)</option>
            </select>
          </div>

          {activeCount > 0 && (
            <button
              type="button"
              onClick={onReset}
              className="inline-flex items-center gap-1.5 rounded-xl bg-red-500/10 px-3 py-1.5 text-xs font-bold text-red-500 border border-red-500/20 transition hover:bg-red-500 hover:text-white"
            >
              <span>↺ Clear Filters</span>
              <span className="rounded-full bg-red-500 px-1.5 py-0.2 text-[9px] font-mono text-white">
                {activeCount}
              </span>
            </button>
          )}
        </div>
      </div>

      {/* Bottom Row: Granular Filters (Status, Priority, Tags, Due Date) */}
      <div className="flex flex-wrap items-center gap-2 pt-2.5 border-t border-[var(--stroke)]/60 text-xs">
        {/* Status / Column Filter */}
        <div className="flex items-center gap-1.5 rounded-xl border border-[var(--stroke)] bg-[var(--surface-input)] px-2.5 py-1">
          <span className="font-bold text-[var(--gray-text)] uppercase tracking-wider text-[9px] font-mono">
            Status:
          </span>
          <select
            value={filters.columnId}
            onChange={(e) => updateFilter("columnId", e.target.value)}
            className="bg-transparent font-semibold text-[var(--navy-dark)] outline-none cursor-pointer text-xs"
            aria-label="Filter by column status"
          >
            <option value="all">All Columns</option>
            {columns.map((col) => (
              <option key={col.id} value={col.id}>
                {col.title}
              </option>
            ))}
          </select>
        </div>

        {/* Priority Filter */}
        <div className="flex items-center gap-1.5 rounded-xl border border-[var(--stroke)] bg-[var(--surface-input)] px-2.5 py-1">
          <span className="font-bold text-[var(--gray-text)] uppercase tracking-wider text-[9px] font-mono">
            Priority:
          </span>
          <select
            value={filters.priority}
            onChange={(e) => updateFilter("priority", e.target.value as PriorityFilterType)}
            className="bg-transparent font-semibold text-[var(--navy-dark)] outline-none cursor-pointer text-xs"
            aria-label="Filter by priority"
          >
            <option value="all">All Priorities</option>
            <option value="high">High 🔥</option>
            <option value="medium">Medium ⚡</option>
            <option value="low">Low 🟢</option>
          </select>
        </div>

        {/* Tag Filter */}
        <div className="flex items-center gap-1.5 rounded-xl border border-[var(--stroke)] bg-[var(--surface-input)] px-2.5 py-1">
          <span className="font-bold text-[var(--gray-text)] uppercase tracking-wider text-[9px] font-mono">
            Tag:
          </span>
          <select
            value={filters.tag}
            onChange={(e) => updateFilter("tag", e.target.value)}
            className="bg-transparent font-semibold text-[var(--navy-dark)] outline-none cursor-pointer text-xs"
            aria-label="Filter by tag"
          >
            <option value="all">All Tags</option>
            {availableTags.map((t) => (
              <option key={t} value={t}>
                #{t}
              </option>
            ))}
          </select>
        </div>

        {/* Due Date Filter */}
        <div className="flex items-center gap-1.5 rounded-xl border border-[var(--stroke)] bg-[var(--surface-input)] px-2.5 py-1">
          <span className="font-bold text-[var(--gray-text)] uppercase tracking-wider text-[9px] font-mono">
            Due Date:
          </span>
          <select
            value={filters.dueDateFilter}
            onChange={(e) => updateFilter("dueDateFilter", e.target.value as DueDateFilterType)}
            className="bg-transparent font-semibold text-[var(--navy-dark)] outline-none cursor-pointer text-xs"
            aria-label="Filter by due date"
          >
            <option value="all">All Dates</option>
            <option value="overdue">Overdue ⚠️</option>
            <option value="today">Due Today 📅</option>
            <option value="this-week">Due This Week 🗓️</option>
            <option value="has-due-date">Has Due Date</option>
            <option value="no-due-date">No Due Date</option>
          </select>
        </div>
      </div>
    </div>
  );
};
