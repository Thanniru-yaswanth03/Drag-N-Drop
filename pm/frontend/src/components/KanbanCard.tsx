"use client";

import { memo, useState, useRef, useCallback } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import clsx from "clsx";
import type { Card } from "@/lib/kanban";

type KanbanCardProps = {
  card: Card;
  onDelete: (cardId: string) => void;
  onEdit?: (card: Card) => void;
};

const priorityConfig = {
  high: {
    badge: "bg-red-500/10 text-red-500 border-red-500/30 dark:bg-red-500/15 dark:text-red-400 dark:border-red-500/30",
    dot: "bg-red-500 animate-pulse",
    icon: "🔥",
    label: "High",
  },
  medium: {
    badge: "bg-amber-500/10 text-amber-600 border-amber-500/30 dark:bg-amber-500/15 dark:text-amber-400 dark:border-amber-500/30",
    dot: "bg-amber-500",
    icon: "⚡",
    label: "Medium",
  },
  low: {
    badge: "bg-emerald-500/10 text-emerald-600 border-emerald-500/30 dark:bg-emerald-500/15 dark:text-emerald-400 dark:border-emerald-500/30",
    dot: "bg-emerald-500",
    icon: "🟢",
    label: "Low",
  },
};

export const KanbanCard = memo(({ card, onDelete, onEdit }: KanbanCardProps) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: card.id });

  const [tilt, setTilt] = useState<{ rx: number; ry: number; x: number; y: number; active: boolean }>({
    rx: 0,
    ry: 0,
    x: 50,
    y: 50,
    active: false,
  });

  const cardRef = useRef<HTMLElement | null>(null);

  const setCombinedRef = useCallback(
    (node: HTMLElement | null) => {
      cardRef.current = node;
      setNodeRef(node);
    },
    [setNodeRef]
  );

  const handlePointerMove = (e: React.PointerEvent<HTMLElement>) => {
    if (isDragging || e.pointerType === "touch") return;
    if (!cardRef.current) return;

    const rect = cardRef.current.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;
    const normX = (px / rect.width - 0.5) * 2;
    const normY = (py / rect.height - 0.5) * 2;

    const rx = -normY * 2;
    const ry = normX * 2;

    setTilt({
      rx,
      ry,
      x: (px / rect.width) * 100,
      y: (py / rect.height) * 100,
      active: true,
    });
  };

  const handlePointerLeave = () => {
    setTilt({ rx: 0, ry: 0, x: 50, y: 50, active: false });
  };

  const transformString = CSS.Transform.toString(transform);

  const style: React.CSSProperties = {
    transform: isDragging
      ? transformString
      : tilt.active
      ? `${transformString ? `${transformString} ` : ""}perspective(800px) rotateX(${tilt.rx}deg) rotateY(${tilt.ry}deg) translateZ(3px)`
      : transformString || undefined,
    transition: isDragging
      ? undefined
      : transition || (tilt.active ? "transform 0.05s ease-out" : "transform 0.15s ease, box-shadow 0.15s ease"),
    touchAction: "none",
  };

  const priority = card.priority || "medium";
  const pStyle = priorityConfig[priority] || priorityConfig.medium;

  const isOverdue =
    card.dueDate && new Date(card.dueDate) < new Date(new Date().setHours(0, 0, 0, 0));

  return (
    <article
      ref={setCombinedRef}
      style={style}
      data-testid={`card-${card.id}`}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      className={clsx(
        "group relative rounded-2xl border p-4 transition-colors duration-150 cursor-grab active:cursor-grabbing select-none overflow-hidden",
        isDragging
          ? "opacity-20 border-2 border-dashed border-[var(--accent-amber)] bg-[var(--accent-amber)]/5 shadow-none"
          : "border-[var(--stroke)] bg-[var(--surface-card)] hover:bg-[var(--surface-card-hover)] shadow-[var(--shadow-card)] hover:shadow-[var(--shadow)] hover:border-[var(--stroke-highlight)]"
      )}
      {...attributes}
      {...listeners}
    >
      {/* Specular dynamic light sheen on hover */}
      {tilt.active && !isDragging && (
        <div
          className="pointer-events-none absolute inset-0 rounded-2xl opacity-35 transition-opacity duration-150"
          style={{
            background: `radial-gradient(circle at ${tilt.x}% ${tilt.y}%, rgba(255, 255, 255, 0.14) 0%, transparent 60%)`,
          }}
          aria-hidden="true"
        />
      )}

      {/* Top Header: Priority Badge & Micro Actions */}
      <div className="flex items-center justify-between gap-2 mb-2.5">
        <span
          className={clsx(
            "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider transition-transform group-hover:scale-[1.02]",
            pStyle.badge
          )}
        >
          <span className={clsx("h-1.5 w-1.5 rounded-full", pStyle.dot)} />
          <span>{pStyle.icon}</span>
          <span>{pStyle.label}</span>
        </span>

        <div className="flex items-center gap-1 opacity-70 group-hover:opacity-100 transition-opacity duration-150">
          {onEdit && (
            <button
              type="button"
              onPointerDown={(e) => e.stopPropagation()}
              onMouseDown={(e) => e.stopPropagation()}
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
                onEdit(card);
              }}
              className="rounded-lg px-2 py-1 text-xs font-semibold text-[var(--gray-text)] hover:bg-[var(--surface-column-header)] hover:text-[var(--accent-amber)] transition-colors"
              aria-label={`Edit ${card.title}`}
            >
              ✏️ Edit
            </button>
          )}
          <button
            type="button"
            onPointerDown={(e) => e.stopPropagation()}
            onMouseDown={(e) => e.stopPropagation()}
            onClick={(e) => {
              e.stopPropagation();
              e.preventDefault();
              onDelete(card.id);
            }}
            className="rounded-lg px-2 py-1 text-xs font-semibold text-[var(--gray-text)] hover:bg-red-500/10 hover:text-red-500 transition-colors"
            aria-label={`Delete ${card.title}`}
          >
            🗑️
          </button>
        </div>
      </div>

      {/* Card Title */}
      <h4 className="font-display text-sm sm:text-base font-bold text-[var(--navy-dark)] leading-snug tracking-tight">
        {card.title}
      </h4>

      {/* Description Snippet */}
      {(card.details || card.description) && (
        <p className="mt-1.5 text-xs leading-relaxed text-[var(--gray-text)] line-clamp-3">
          {card.details || card.description}
        </p>
      )}

      {/* Footer Meta: Due Date, Tags, Assignee */}
      <div className="mt-3 flex flex-wrap items-center gap-2 pt-2.5 border-t border-[var(--stroke)]">
        {card.dueDate && (
          <span
            className={clsx(
              "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold border transition-colors",
              isOverdue
                ? "bg-red-500/15 text-red-500 border-red-500/30"
                : "bg-[var(--surface-input)] text-[var(--gray-text)] border-[var(--stroke)]"
            )}
            title={`Due: ${card.dueDate}${isOverdue ? " (Overdue)" : ""}`}
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
                className="inline-flex items-center rounded-md bg-[var(--surface-input)] border border-[var(--stroke)] text-[var(--navy-dark)] px-1.5 py-0.5 text-[10px] font-semibold"
              >
                #{tag}
              </span>
            ))}
          </div>
        )}

        {card.assignee && (
          <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-[var(--surface-input)] border border-[var(--stroke)] text-[var(--navy-dark)] px-2 py-0.5 text-[10px] font-bold shadow-2xs">
            <span className="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-[var(--accent-amber)]/20 text-[var(--accent-amber)] text-[8px]">
              👤
            </span>
            <span>{card.assignee}</span>
          </span>
        )}
      </div>
    </article>
  );
});

KanbanCard.displayName = "KanbanCard";
