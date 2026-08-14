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

const columnAccents: Record<string, { gradient: string; text: string }> = {
  "col-backlog": { gradient: "from-slate-500 to-indigo-500", text: "text-slate-500" },
  "col-discovery": { gradient: "from-sky-400 to-blue-600", text: "text-sky-500" },
  "col-progress": { gradient: "from-amber-400 to-orange-500", text: "text-amber-500" },
  "col-review": { gradient: "from-purple-500 to-indigo-600", text: "text-purple-500" },
  "col-done": { gradient: "from-emerald-400 to-teal-600", text: "text-emerald-500" },
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
    const accent = columnAccents[column.id] || { gradient: "from-blue-500 to-indigo-500", text: "text-blue-500" };

    return (
      <section
        ref={setNodeRef}
        data-testid={`column-${column.id}`}
        className={clsx(
          "flex min-h-[540px] flex-col rounded-[28px] border border-[var(--stroke)] bg-[var(--surface-strong)] p-4 shadow-[var(--shadow)] transition-all duration-200",
          isOver && "ring-2 ring-[var(--primary-blue)] scale-[1.01] bg-[var(--surface)]"
        )}
      >
        <div className="flex items-start justify-between gap-3 border-b border-[var(--stroke)] pb-3.5 mb-3.5">
          <div className="w-full">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={clsx("h-2.5 w-8 rounded-full bg-gradient-to-r shadow-sm", accent.gradient)} />
                <span className="text-[11px] font-bold uppercase tracking-[0.2em] text-[var(--gray-text)]">
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
              className="mt-2.5 w-full bg-transparent font-display text-lg font-bold text-[var(--navy-dark)] outline-none focus:ring-2 focus:ring-[var(--primary-blue)]/50 rounded-xl px-2 py-0.5 transition"
              aria-label="Column title"
            />
          </div>
        </div>

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
            <div className="flex flex-1 flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[var(--stroke)] p-6 text-center">
              <span className="text-2xl opacity-40">📥</span>
              <span className="mt-2 text-xs font-bold uppercase tracking-wider text-[var(--gray-text)]">
                Drop cards here
              </span>
            </div>
          )}
        </div>

        <div className="mt-3.5">
          <NewCardForm
            onAdd={(title, details) => onAddCard(column.id, title, details)}
          />
        </div>
      </section>
    );
  },
  (prev, next) =>
    prev.column.id === next.column.id &&
    prev.column.title === next.column.title &&
    prev.cards.length === next.cards.length &&
    prev.cards.every((c, i) => c.id === next.cards[i]?.id && c.updatedAt === next.cards[i]?.updatedAt)
);
