import { memo } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import type { Card } from "@/lib/kanban";

type KanbanCardProps = {
  card: Card;
  onDelete: (cardId: string) => void;
  onEdit?: (card: Card) => void;
};

export const KanbanCard = memo(
  ({ card, onDelete, onEdit }: KanbanCardProps) => {
    const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
      useSortable({ id: card.id });

    const style = {
      transform: CSS.Transform.toString(transform),
      transition,
    };

    const priorityStyles = {
      high: {
        badge: "bg-red-500/10 text-red-600 border-red-500/30 dark:bg-red-500/20 dark:text-red-400",
        dot: "bg-red-500 animate-pulse",
        icon: "🔥",
        label: "High",
      },
      medium: {
        badge: "bg-amber-500/10 text-amber-600 border-amber-500/30 dark:bg-amber-500/20 dark:text-amber-400",
        dot: "bg-amber-500",
        icon: "⚡",
        label: "Medium",
      },
      low: {
        badge: "bg-emerald-500/10 text-emerald-600 border-emerald-500/30 dark:bg-emerald-500/20 dark:text-emerald-400",
        dot: "bg-emerald-500",
        icon: "🟢",
        label: "Low",
      },
    };

    const priority = card.priority || "medium";
    const pStyle = priorityStyles[priority];

    return (
      <article
        ref={setNodeRef}
        style={style}
        data-testid={`card-${card.id}`}
        className={clsx(
          "group relative rounded-2xl border border-[var(--stroke)] bg-[var(--card-bg)] p-4 shadow-[0_4px_20px_rgba(0,0,0,0.04)]",
          "transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_12px_28px_rgba(0,0,0,0.12)] hover:border-[var(--primary-blue)]/40",
          isDragging && "opacity-60 shadow-2xl ring-2 ring-[var(--primary-blue)] scale-[1.02]"
        )}
        {...attributes}
        {...listeners}
      >
        <div className="flex items-center justify-between gap-2 mb-2.5">
          <span
            className={clsx(
              "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider",
              pStyle.badge
            )}
          >
            <span className={clsx("h-1.5 w-1.5 rounded-full", pStyle.dot)} />
            <span>{pStyle.icon}</span>
            <span>{pStyle.label}</span>
          </span>
          <div className="flex items-center gap-1 opacity-70 group-hover:opacity-100 transition">
            {onEdit && (
              <button
                type="button"
                onPointerDown={(e) => e.stopPropagation()}
                onClick={(e) => {
                  e.stopPropagation();
                  onEdit(card);
                }}
                className="rounded-lg px-2 py-1 text-xs font-semibold text-[var(--gray-text)] hover:bg-[var(--surface)] hover:text-[var(--primary-blue)] transition"
                aria-label={`Edit ${card.title}`}
              >
                ✏️ Edit
              </button>
            )}
            <button
              type="button"
              onPointerDown={(e) => e.stopPropagation()}
              onClick={(e) => {
                e.stopPropagation();
                onDelete(card.id);
              }}
              className="rounded-lg px-2 py-1 text-xs font-semibold text-[var(--gray-text)] hover:bg-red-500/10 hover:text-red-600 transition"
              aria-label={`Delete ${card.title}`}
            >
              🗑️
            </button>
          </div>
        </div>

        <h4 className="font-display text-base font-bold text-[var(--navy-dark)] leading-snug">
          {card.title}
        </h4>
        {(card.details || card.description) && (
          <p className="mt-1.5 text-xs leading-relaxed text-[var(--gray-text)] line-clamp-3">
            {card.details || card.description}
          </p>
        )}

        <div className="mt-3 flex flex-wrap items-center gap-2 pt-2 border-t border-[var(--stroke)]/50">
          {card.dueDate && (
            <span
              className={clsx(
                "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold border",
                new Date(card.dueDate) < new Date(new Date().setHours(0, 0, 0, 0))
                  ? "bg-red-500/10 text-red-600 border-red-500/30"
                  : "bg-[var(--surface)] text-[var(--gray-text)] border-[var(--stroke)]"
              )}
              title={`Due: ${card.dueDate}`}
            >
              <span>📅</span>
              <span>{card.dueDate}</span>
            </span>
          )}

          {card.tags && card.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {card.tags.map((tag, idx) => (
                <span
                  key={`${tag}-${idx}`}
                  className="inline-flex items-center rounded-md bg-[var(--primary-blue)]/10 text-[var(--primary-blue)] px-1.5 py-0.5 text-[10px] font-semibold"
                >
                  #{tag}
                </span>
              ))}
            </div>
          )}

          {card.assignee && (
            <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-[var(--secondary-purple)]/10 text-[var(--secondary-purple)] px-2 py-0.5 text-[10px] font-bold border border-[var(--secondary-purple)]/20">
              <span>👤</span>
              <span>{card.assignee}</span>
            </span>
          )}
        </div>

      </article>
    );
  },
  (prev, next) =>
    prev.card.id === next.card.id &&
    prev.card.title === next.card.title &&
    prev.card.details === next.card.details &&
    prev.card.priority === next.card.priority &&
    prev.card.dueDate === next.card.dueDate &&
    prev.card.assignee === next.card.assignee &&
    JSON.stringify(prev.card.tags) === JSON.stringify(next.card.tags)
);

KanbanCard.displayName = "KanbanCard";
