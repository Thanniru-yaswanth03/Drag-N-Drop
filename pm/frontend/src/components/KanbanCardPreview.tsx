import type { Card } from "@/lib/kanban";
import clsx from "clsx";

type KanbanCardPreviewProps = {
  card: Card;
};

const priorityStyles = {
  high: {
    badge: "bg-red-500/20 text-red-500 border-red-500/40",
    dot: "bg-red-500 animate-pulse",
    icon: "🔥",
    label: "High",
  },
  medium: {
    badge: "bg-amber-500/20 text-amber-500 border-amber-500/40",
    dot: "bg-amber-500",
    icon: "⚡",
    label: "Medium",
  },
  low: {
    badge: "bg-emerald-500/20 text-emerald-500 border-emerald-500/40",
    dot: "bg-emerald-500",
    icon: "🟢",
    label: "Low",
  },
};

export const KanbanCardPreview = ({ card }: KanbanCardPreviewProps) => {
  const priority = card.priority || "medium";
  const pStyle = priorityStyles[priority];

  return (
    <article className="group relative rounded-2xl border-2 border-[var(--primary-blue)] bg-[var(--card-bg)] p-4 shadow-[0_25px_60px_-12px_rgba(2,132,199,0.4)] backdrop-blur-xl rotate-[3deg] scale-[1.04] transition-all duration-150 ring-4 ring-[var(--primary-blue)]/20 cursor-grabbing">
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
        <span className="text-[10px] font-extrabold uppercase tracking-wider text-[var(--primary-blue)] animate-pulse">
          ✨ Dragging Task
        </span>
      </div>

      <h4 className="font-display text-base font-bold text-[var(--navy-dark)] leading-snug">
        {card.title}
      </h4>
      {(card.details || card.description) && (
        <p className="mt-1.5 text-xs leading-relaxed text-[var(--gray-text)] line-clamp-2">
          {card.details || card.description}
        </p>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-2 pt-2 border-t border-[var(--stroke)]/50">
        {card.dueDate && (
          <span className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold bg-[var(--surface)] text-[var(--gray-text)] border border-[var(--stroke)]">
            📅 {card.dueDate}
          </span>
        )}

        {card.tags && card.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {card.tags.slice(0, 2).map((tag, idx) => (
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
          <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-[var(--secondary-purple)]/20 text-[var(--secondary-purple)] px-2 py-0.5 text-[10px] font-bold">
            👤 @{card.assignee}
          </span>
        )}
      </div>
    </article>
  );
};

