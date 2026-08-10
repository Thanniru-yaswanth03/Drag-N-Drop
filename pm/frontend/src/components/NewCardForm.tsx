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
          className="rounded-2xl border-2 border-[var(--primary-blue)] bg-[var(--card-bg)] p-4 shadow-xl animate-in fade-in zoom-in-95 duration-150 space-y-3.5"
        >
          <div className="flex items-center justify-between border-b border-[var(--stroke)] pb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[var(--primary-blue)] flex items-center gap-1.5">
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
            <label className="block text-[10px] font-bold uppercase tracking-wider text-[var(--gray-text)] mb-1">
              Task Title
            </label>
            <input
              value={formState.title}
              onChange={(event) =>
                setFormState((prev) => ({ ...prev, title: event.target.value }))
              }
              placeholder="Card title..."
              className="w-full rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3.5 py-2.5 text-xs font-semibold text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)] focus:ring-1 focus:ring-[var(--primary-blue)]"
              autoFocus
              required
            />
          </div>

          <div>
            <label className="block text-[10px] font-bold uppercase tracking-wider text-[var(--gray-text)] mb-1">
              Context & Details
            </label>
            <textarea
              value={formState.details}
              onChange={(event) =>
                setFormState((prev) => ({ ...prev, details: event.target.value }))
              }
              placeholder="Details and context..."
              rows={3}
              className="w-full resize-none rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3.5 py-2.5 text-xs text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)] focus:ring-1 focus:ring-[var(--primary-blue)]"
            />
          </div>

          <div className="flex items-center gap-2 pt-1">
            <button
              type="submit"
              className="flex-1 rounded-xl bg-gradient-to-r from-[var(--secondary-purple)] to-[var(--primary-blue)] px-4 py-2.5 text-xs font-bold uppercase tracking-wider text-white shadow-md transition hover:brightness-110 active:scale-95"
            >
              Add Task
            </button>
            <button
              type="button"
              onClick={() => {
                setIsOpen(false);
                setFormState(initialFormState);
              }}
              className="rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-3.5 py-2.5 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
            >
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="group w-full flex items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-[var(--primary-blue)]/40 bg-[var(--primary-blue)]/5 px-4 py-3 text-xs font-bold uppercase tracking-wider text-[var(--primary-blue)] transition duration-200 hover:bg-[var(--primary-blue)] hover:text-white hover:border-transparent hover:shadow-lg active:scale-98"
        >
          <span className="text-base transition group-hover:scale-125">+</span>
          <span>Add Task</span>
        </button>
      )}
    </div>
  );
};
