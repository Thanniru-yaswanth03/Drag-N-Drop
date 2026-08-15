"use client";

import { useEffect, useState } from "react";
import { fetchProjectActivity, type ActivityItem } from "@/lib/api";

type ActivityHistoryModalProps = {
  isOpen: boolean;
  onClose: () => void;
  projectId: string | null;
  projectName: string;
  username?: string;
};

export const ActivityHistoryModal = ({
  isOpen,
  onClose,
  projectId,
  projectName,
}: ActivityHistoryModalProps) => {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    if (isOpen && projectId) {
      queueMicrotask(() => setIsLoading(true));
      fetchProjectActivity(projectId)
        .then((data) => {
          setActivities(data);
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, [isOpen, projectId]);

  if (!isOpen) return null;

  const filteredActivities = activities.filter((act) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      act.message.toLowerCase().includes(term) ||
      act.actionType.toLowerCase().includes(term) ||
      act.userId.toLowerCase().includes(term)
    );
  });

  const getActionBadge = (actionType: string) => {
    switch (actionType) {
      case "card_created":
        return <span className="rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 text-[10px] font-bold">➕ Created</span>;
      case "card_updated":
        return <span className="rounded-full bg-blue-500/10 text-blue-600 dark:text-blue-400 px-2 py-0.5 text-[10px] font-bold">✏️ Updated</span>;
      case "card_deleted":
        return <span className="rounded-full bg-red-500/10 text-red-600 dark:text-red-400 px-2 py-0.5 text-[10px] font-bold">🗑️ Deleted</span>;
      case "card_moved":
        return <span className="rounded-full bg-purple-500/10 text-purple-600 dark:text-purple-400 px-2 py-0.5 text-[10px] font-bold">🔀 Moved</span>;
      case "project_created":
        return <span className="rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 px-2 py-0.5 text-[10px] font-bold">📁 Project Created</span>;
      case "project_updated":
        return <span className="rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 px-2 py-0.5 text-[10px] font-bold">📝 Project Renamed</span>;
      default:
        return <span className="rounded-full bg-slate-500/10 text-slate-600 dark:text-slate-400 px-2 py-0.5 text-[10px] font-bold">⚡ Event</span>;
    }
  };

  const formatTimestamp = (ts?: string | null) => {
    if (!ts) return "Just now";
    try {
      const date = new Date(ts.endsWith("Z") ? ts : ts + "Z");
      if (isNaN(date.getTime())) return ts;
      return date.toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return ts;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div
        className="w-full max-w-lg rounded-3xl border border-[var(--stroke)] bg-[var(--card-bg)] p-6 shadow-2xl flex flex-col max-h-[85vh]"
        role="dialog"
        aria-modal="true"
        aria-labelledby="activity-modal-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[var(--stroke)]/60 pb-4">
          <div>
            <h2 id="activity-modal-title" className="text-lg font-extrabold text-[var(--navy-dark)]">
              📜 Activity History
            </h2>
            <p className="text-xs text-[var(--gray-text)] font-medium">
              Audit log for <span className="font-bold text-[var(--navy-dark)]">{projectName}</span>
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close activity history"
            className="rounded-full p-2 text-[var(--gray-text)] hover:bg-[var(--surface)] transition text-sm font-bold"
          >
            ✕
          </button>
        </div>

        {/* Filter Search input */}
        <div className="mt-4">
          <input
            type="text"
            placeholder="Search activity log..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2 text-xs text-[var(--navy-dark)] placeholder-[var(--gray-text)] outline-none focus:border-[var(--primary-blue)] transition"
          />
        </div>

        {/* Timeline list */}
        <div className="mt-4 flex-1 overflow-y-auto pr-1">
          {isLoading ? (
            <div className="py-12 text-center text-xs font-semibold text-[var(--gray-text)]">
              Loading activity history...
            </div>
          ) : filteredActivities.length === 0 ? (
            <div className="py-12 text-center text-xs font-semibold text-[var(--gray-text)]">
              {searchTerm ? "No activity matching search filter." : "No activities recorded yet."}
            </div>
          ) : (
            <div className="space-y-3 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-[var(--stroke)]">
              {filteredActivities.map((act) => (
                <div key={act.id} className="relative pl-7 flex flex-col gap-1 text-xs">
                  <div className="absolute left-1.5 top-1 h-3 w-3 rounded-full bg-[var(--primary-blue)] border-2 border-[var(--card-bg)] ring-2 ring-[var(--stroke)]" />
                  
                  <div className="flex items-center gap-2 flex-wrap">
                    {getActionBadge(act.actionType)}
                    <span className="text-[10px] font-medium text-[var(--gray-text)]">
                      by <strong className="text-[var(--navy-dark)]">{act.userId}</strong>
                    </span>
                    <span className="ml-auto text-[10px] font-medium text-[var(--gray-text)]">
                      {formatTimestamp(act.createdAt)}
                    </span>
                  </div>

                  <p className="font-semibold text-[var(--navy-dark)] leading-snug">
                    {act.message}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-4 pt-3 border-t border-[var(--stroke)]/60 flex items-center justify-between text-[11px] text-[var(--gray-text)]">
          <span>{filteredActivities.length} event(s) recorded</span>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl bg-[var(--surface)] border border-[var(--stroke)] px-4 py-1.5 text-xs font-bold text-[var(--navy-dark)] hover:bg-[var(--stroke)] transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
