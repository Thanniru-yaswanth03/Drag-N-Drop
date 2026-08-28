"use client";

import { memo } from "react";
import clsx from "clsx";
import { useDroppable } from "@dnd-kit/core";
import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import type { Card, Column } from "@/lib/kanban";
import { KanbanCard } from "@/components/KanbanCard";
import { NewCardForm } from "@/components/NewCardForm";

type KanbanColumnProps = {
  column: Column;
  cards: Card[];
  onRename: (columnId: string, title: string) => void;
  onAddCard: (columnId: string, title: string, details: string) => void;
  onDeleteCard: (columnId: string, cardId: string) => void;
  onEditCard?: (card: Card) => void;
  onClearColumn?: (columnId: string) => void;
};

const columnAccents: Record<string, { beacon: string; glow: string; text: string }> = {
  "col-backlog": {
    beacon: "bg-slate-400 dark:bg-slate-400",
    glow: "shadow-[0_0_12px_rgba(148,163,184,0.4)]",
    text: "text-slate-400",
  },
  "col-discovery": {
    beacon: "bg-cyan-400 dark:bg-cyan-400",
    glow: "shadow-[0_0_12px_rgba(6,182,212,0.5)]",
    text: "text-cyan-400",
  },
  "col-progress": {
    beacon: "bg-amber-400 dark:bg-amber-400",
    glow: "shadow-[0_0_12px_rgba(245,158,11,0.5)]",
    text: "text-amber-400",
  },
  "col-review": {
    beacon: "bg-purple-400 dark:bg-purple-400",
    glow: "shadow-[0_0_12px_rgba(168,85,247,0.5)]",
    text: "text-purple-400",
  },
  "col-done": {
    beacon: "bg-emerald-400 dark:bg-emerald-400",
    glow: "shadow-[0_0_12px_rgba(16,185,129,0.5)]",
    text: "text-emerald-400",
  },
};

export const KanbanColumn = memo(
  ({
    column,
    cards,
    onRename,
    onAddCard,
    onDeleteCard,
    onEditCard,
    onClearColumn,
  }: KanbanColumnProps) => {
    const { setNodeRef, isOver } = useDroppable({ id: column.id });
    const accent = columnAccents[column.id] || {
      beacon: "bg-amber-400",
      glow: "shadow-[0_0_12px_rgba(245,158,11,0.4)]",
      text: "text-amber-400",
    };

    return (
      <section
        ref={setNodeRef}
        data-testid={`column-${column.id}`}
        className={clsx(
          "flex min-h-[240px] sm:min-h-[560px] flex-col rounded-[26px] border p-4 shadow-[var(--shadow)] transition-all duration-200",
          isOver
            ? "border-[var(--accent-amber)] ring-4 ring-[var(--accent-amber-glow)] bg-[var(--surface-column)] scale-[1.01] shadow-2xl"
            : "border-[var(--stroke)] bg-[var(--surface-column)] hover:border-[var(--stroke-strong)]"
        )}
      >
        {/* Column Header */}
        <div className="flex items-start justify-between gap-3 border-b border-[var(--stroke)] pb-3 mb-3.5">
          <div className="w-full">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span
                  className={clsx(
                    "h-2 w-2 rounded-full transition-transform duration-300",
                    accent.beacon,
                    accent.glow
                  )}
                />
                <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--gray-text)] font-mono">
                  {cards.length} {cards.length === 1 ? "task" : "tasks"}
                </span>
              </div>
              {cards.length > 0 && onClearColumn && (
                <button
                  type="button"
                  onClick={() => onClearColumn(column.id)}
                  className="text-[10px] font-bold uppercase tracking-wider text-[var(--gray-text)] hover:text-red-500 transition px-2 py-0.5 rounded-md hover:bg-red-500/10"
                  title="Clear all tasks in this column"
                  aria-label={`Clear ${column.title} column`}
                >
                  Clear All
                </button>
              )}
            </div>

            <input
              value={column.title}
              onChange={(event) => onRename(column.id, event.target.value)}
              className="mt-2 w-full bg-transparent font-display text-base sm:text-lg font-bold text-[var(--navy-dark)] outline-none focus:ring-1 focus:ring-[var(--accent-amber)]/60 rounded-xl px-2 py-0.5 transition"
              aria-label="Column title"
            />
          </div>
        </div>

        {/* Column Cards Container */}
        <div className="flex flex-1 flex-col gap-3">
          <SortableContext items={cards.map((c) => c.id)} strategy={verticalListSortingStrategy}>
            {cards.map((card) => (
              <KanbanCard
                key={card.id}
                card={card}
                onDelete={(cardId) => onDeleteCard(column.id, cardId)}
                onEdit={onEditCard}
              />
            ))}
          </SortableContext>

          {cards.length === 0 && (
            <div className="flex flex-1 flex-col items-center justify-center rounded-2xl border border-dashed border-[var(--stroke)] p-6 text-center bg-[var(--surface-input)]/40 min-h-[140px]">
              <span className="text-xl opacity-40">📥</span>
              <span className="mt-2 text-[11px] font-bold uppercase tracking-wider text-[var(--gray-text)]">
                Drop cards here
              </span>
            </div>
          )}
        </div>

        {/* Quick Add Form */}
        <div className="mt-3.5">
          <NewCardForm
            onAdd={(title, details) => onAddCard(column.id, title, details)}
          />
        </div>
      </section>
    );
  }
);

KanbanColumn.displayName = "KanbanColumn";
