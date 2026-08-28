"use client";

import { useState, type FormEvent } from "react";

const initialFormState = { title: "", details: "" };

type NewCardFormProps = {
  onAdd: (title: string, details: string) => void;
};

export const NewCardForm = ({ onAdd }: NewCardFormProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [formState, setFormState] = useState(initialFormState);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!formState.title.trim()) {
      return;
    }
    onAdd(formState.title.trim(), formState.details.trim());
    setFormState(initialFormState);
    setIsOpen(false);
  };

  return (
    <div className="mt-3">
      {isOpen ? (
        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-[var(--accent-amber)] bg-[var(--surface-input)] p-3.5 shadow-xl animate-in fade-in zoom-in-95 duration-150 space-y-3"
        >
          <div className="flex items-center justify-between border-b border-[var(--stroke)] pb-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--accent-amber)] flex items-center gap-1.5 font-mono">
              <span>➕</span> Create New Task
            </span>
            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                setFormState(initialFormState);
              }}
              className="text-xs text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
            >
              ✕
            </button>
          </div>

          <div>
            <label className="block text-[10px] font-bold uppercase tracking-wider text-[var(--gray-text)] mb-1 font-mono">
              Task Title
            </label>
            <input
              value={formState.title}
              onChange={(event) =>
                setFormState((prev) => ({ ...prev, title: event.target.value }))
              }
              placeholder="Card title..."
              className="w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface-column)] px-3 py-2 text-xs font-semibold text-[var(--navy-dark)] outline-none transition focus:border-[var(--accent-amber)]"
              autoFocus
              required
            />
          </div>

          <div>
            <label className="block text-[10px] font-bold uppercase tracking-wider text-[var(--gray-text)] mb-1 font-mono">
              Context & Details
            </label>
            <textarea
              value={formState.details}
              onChange={(event) =>
                setFormState((prev) => ({ ...prev, details: event.target.value }))
              }
              placeholder="Details and context..."
              rows={2}
              className="w-full resize-none rounded-xl border border-[var(--stroke)] bg-[var(--surface-column)] px-3 py-2 text-xs text-[var(--navy-dark)] outline-none transition focus:border-[var(--accent-amber)]"
            />
          </div>

          <div className="flex items-center gap-2 pt-1">
            <button
              type="submit"
              className="flex-1 rounded-xl bg-[var(--accent-amber)] px-3 py-2 text-xs font-bold uppercase tracking-wider text-black shadow-md transition hover:brightness-110 active:scale-95"
            >
              Add Task
            </button>
            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                setFormState(initialFormState);
              }}
              className="rounded-xl border border-[var(--stroke)] bg-[var(--surface-column)] px-3 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
            >
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="group w-full flex items-center justify-center gap-2 rounded-2xl border border-dashed border-[var(--stroke-strong)] bg-[var(--surface-input)]/60 px-3.5 py-2.5 text-xs font-bold uppercase tracking-wider text-[var(--gray-text)] transition-all duration-200 hover:border-[var(--accent-amber)] hover:text-[var(--accent-amber)] hover:bg-[var(--accent-amber)]/5 active:scale-[0.99]"
        >
          <span className="text-sm transition-transform group-hover:scale-125">+</span>
          <span>Add Task</span>
        </button>
      )}
    </div>
  );
};
