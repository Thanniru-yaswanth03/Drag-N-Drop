"use client";

import { useState } from "react";
import type { Card } from "@/lib/kanban";

type EditCardModalProps = {
  card: Card;
  isOpen: boolean;
  onClose: () => void;
  onSave: (cardId: string, title: string, details: string, priority: "high" | "medium" | "low") => void;
};

export const EditCardModal = ({
  card,
  isOpen,
  onClose,
  onSave,
}: EditCardModalProps) => {
  const [title, setTitle] = useState(card.title);
  const [details, setDetails] = useState(card.details);
  const [priority, setPriority] = useState<"high" | "medium" | "low">(card.priority || "medium");

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    onSave(card.id, title.trim(), details.trim(), priority);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-[28px] border border-[var(--stroke)] bg-[var(--card-bg)] p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between border-b border-[var(--stroke)] pb-4">
          <h3 className="font-display text-xl font-semibold text-[var(--navy-dark)]">
            Edit Card
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-2 text-[var(--gray-text)] hover:bg-[var(--surface)] hover:text-[var(--navy-dark)]"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-5">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[var(--gray-text)]">
              Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              className="mt-2 w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm font-semibold text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[var(--gray-text)]">
              Details
            </label>
            <textarea
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              rows={4}
              className="mt-2 w-full resize-none rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--navy-dark)] outline-none focus:border-[var(--primary-blue)]"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-[var(--gray-text)]">
              Priority Tag
            </label>
            <div className="mt-2 flex gap-3">
              {(["low", "medium", "high"] as const).map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPriority(p)}
                  className={`flex-1 rounded-xl py-2.5 text-xs font-bold uppercase tracking-wider transition ${
                    priority === p
                      ? p === "high"
                        ? "bg-red-500 text-white shadow-md"
                        : p === "medium"
                        ? "bg-amber-500 text-white shadow-md"
                        : "bg-emerald-500 text-white shadow-md"
                      : "border border-[var(--stroke)] bg-[var(--surface)] text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-4 border-t border-[var(--stroke)]">
            <button
              type="button"
              onClick={onClose}
              className="rounded-full border border-[var(--stroke)] px-5 py-2.5 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-full bg-[var(--secondary-purple)] px-6 py-2.5 text-xs font-semibold uppercase tracking-wide text-white shadow-md hover:brightness-110"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
