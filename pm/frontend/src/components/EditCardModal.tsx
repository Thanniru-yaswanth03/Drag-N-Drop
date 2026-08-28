"use client";

import { useState } from "react";
import type { Card } from "@/lib/kanban";

type EditCardModalProps = {
  card: Card;
  isOpen: boolean;
  onClose: () => void;
  onSave: (
    cardId: string,
    title: string,
    details: string,
    priority: "high" | "medium" | "low",
    dueDate?: string | null,
    tags?: string[],
    assignee?: string | null
  ) => void;
};

export const EditCardModal = ({
  card,
  isOpen,
  onClose,
  onSave,
}: EditCardModalProps) => {
  const [title, setTitle] = useState(card.title);
  const [details, setDetails] = useState(card.details || card.description || "");
  const [priority, setPriority] = useState<"high" | "medium" | "low">(card.priority || "medium");
  const [dueDate, setDueDate] = useState<string>(card.dueDate || "");
  const [tags, setTags] = useState<string[]>(card.tags || []);
  const [tagInput, setTagInput] = useState("");
  const [assignee, setAssignee] = useState<string>(card.assignee || "");

  if (!isOpen) return null;

  const handleAddTag = (e: React.FormEvent | React.MouseEvent) => {
    e.preventDefault();
    const trimmed = tagInput.trim().replace(/^#/, "");
    if (trimmed && !tags.includes(trimmed)) {
      setTags([...tags, trimmed]);
      setTagInput("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((t) => t !== tagToRemove));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    onSave(
      card.id,
      title.trim(),
      details.trim(),
      priority,
      dueDate || null,
      tags,
      assignee.trim() || null
    );
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4 overflow-y-auto animate-in fade-in duration-150">
      <div className="w-full max-w-xl rounded-3xl glass-floating p-6 shadow-2xl animate-in zoom-in-95 duration-150 my-8">
        <div className="flex items-center justify-between border-b border-[var(--stroke)] pb-4">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--accent-amber)] font-mono">
              Task Details & Settings
            </span>
            <h3 className="font-display text-xl font-bold text-[var(--navy-dark)]">
              Edit Task
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-full p-2 text-[var(--gray-text)] hover:bg-[var(--surface-column)] hover:text-[var(--navy-dark)] transition"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          {/* Title */}
          <div>
            <label className="block text-[10px] font-bold uppercase tracking-wider text-[var(--gray-text)] font-mono">
              Task Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              placeholder="Title..."
              className="mt-1.5 w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-4 py-2.5 text-sm font-semibold text-[var(--navy-dark)] outline-none focus:border-[var(--accent-amber)]"
            />
          </div>

          {/* Description / Details */}
          <div>
            <label className="block text-[10px] font-bold uppercase tracking-wider text-[var(--gray-text)] font-mono">
              Description / Notes
            </label>
            <textarea
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              rows={3}
              placeholder="Add detailed task description..."
              className="mt-1.5 w-full resize-none rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-4 py-2.5 text-xs font-medium text-[var(--navy-dark)] outline-none focus:border-[var(--accent-amber)]"
            />
          </div>

          {/* Priority */}
          <div>
            <label className="block text-[10px] font-bold uppercase tracking-wider text-[var(--gray-text)] font-mono">
              Priority Level
            </label>
            <div className="mt-1.5 flex gap-2">
              {(["low", "medium", "high"] as const).map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPriority(p)}
                  className={`flex-1 rounded-xl py-2 text-xs font-bold uppercase tracking-wider transition ${
                    priority === p
                      ? p === "high"
                        ? "bg-red-500 text-white shadow-md font-extrabold"
                        : p === "medium"
                        ? "bg-amber-500 text-black shadow-md font-extrabold"
                        : "bg-emerald-500 text-white shadow-md font-extrabold"
                      : "border border-[var(--stroke)] bg-[var(--surface-input)] text-[var(--gray-text)] hover:text-[var(--navy-dark)] hover:bg-[var(--surface-column)]"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {/* Due Date & Assignee Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-wider text-[var(--gray-text)] font-mono">
                Due Date
              </label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                className="mt-1.5 w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-4 py-2 text-xs font-semibold text-[var(--navy-dark)] outline-none focus:border-[var(--accent-amber)]"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-wider text-[var(--gray-text)] font-mono">
                Assignee
              </label>
              <input
                type="text"
                value={assignee}
                onChange={(e) => setAssignee(e.target.value)}
                placeholder="Assignee name or user..."
                className="mt-1.5 w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-4 py-2 text-xs font-semibold text-[var(--navy-dark)] outline-none focus:border-[var(--accent-amber)]"
              />
            </div>
          </div>

          {/* Tags Section */}
          <div>
            <label className="block text-[10px] font-bold uppercase tracking-wider text-[var(--gray-text)] font-mono">
              Tags
            </label>
            <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
              {tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 rounded-lg bg-[var(--surface-column)] border border-[var(--stroke)] text-[var(--navy-dark)] px-2.5 py-1 text-xs font-semibold"
                >
                  #{tag}
                  <button
                    type="button"
                    onClick={() => handleRemoveTag(tag)}
                    className="hover:text-red-500 font-bold ml-1"
                  >
                    ✕
                  </button>
                </span>
              ))}
            </div>
            <div className="mt-2 flex items-center gap-2">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddTag(e);
                  }
                }}
                placeholder="New tag..."
                className="flex-1 rounded-xl border border-[var(--stroke)] bg-[var(--surface-input)] px-3 py-1.5 text-xs font-medium text-[var(--navy-dark)] outline-none focus:border-[var(--accent-amber)]"
              />
              <button
                type="button"
                onClick={handleAddTag}
                className="rounded-xl border border-[var(--stroke)] bg-[var(--surface-column)] px-3 py-1.5 text-xs font-bold text-[var(--accent-amber)] hover:bg-[var(--accent-amber)] hover:text-black transition"
              >
                + Add Tag
              </button>
            </div>
          </div>

          {/* Timestamps Readout */}
          {(card.createdAt || card.updatedAt) && (
            <div className="rounded-xl border border-[var(--stroke)] bg-[var(--surface-input)] p-2.5 text-[10px] text-[var(--gray-text)] font-mono space-y-0.5">
              {card.createdAt && (
                <p>
                  <span className="font-bold">Created:</span>{" "}
                  {new Date(card.createdAt).toLocaleString()}
                </p>
              )}
              {card.updatedAt && (
                <p>
                  <span className="font-bold">Last Updated:</span>{" "}
                  {new Date(card.updatedAt).toLocaleString()}
                </p>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-[var(--stroke)]">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-[var(--stroke)] bg-[var(--surface-input)] px-4 py-2 text-xs font-bold uppercase tracking-wider text-[var(--gray-text)] hover:text-[var(--navy-dark)] transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="rounded-xl bg-[var(--accent-amber)] px-5 py-2 text-xs font-bold uppercase tracking-wider text-black shadow-md hover:brightness-110 transition"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
