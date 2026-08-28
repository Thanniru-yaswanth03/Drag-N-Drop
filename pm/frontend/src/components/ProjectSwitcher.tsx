"use client";

import { useState } from "react";
import type { Project } from "@/lib/api";

type ProjectSwitcherProps = {
  projects: Project[];
  activeProjectId: string | null;
  onSelectProject: (projectId: string) => void;
  onCreateProject: (name: string) => void;
  onRenameProject: (projectId: string, name: string) => void;
  onDeleteProject: (projectId: string) => void;
};

export const ProjectSwitcher = ({
  projects,
  activeProjectId,
  onSelectProject,
  onCreateProject,
  onRenameProject,
  onDeleteProject,
}: ProjectSwitcherProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"none" | "create" | "rename" | "delete">("none");
  const [newProjectName, setNewProjectName] = useState("");
  const [renameProjectName, setRenameProjectName] = useState("");

  const safeProjects = Array.isArray(projects) ? projects : [];

  const activeProject =
    safeProjects.find((p) => p.id === activeProjectId) || safeProjects[0] || {
      id: "default",
      name: "Main Project",
    };

  const handleOpenCreate = () => {
    setNewProjectName("");
    setModalMode("create");
    setIsOpen(false);
  };

  const handleOpenRename = () => {
    setRenameProjectName(activeProject.name);
    setModalMode("rename");
    setIsOpen(false);
  };

  const handleOpenDelete = () => {
    setModalMode("delete");
    setIsOpen(false);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    await onCreateProject(newProjectName.trim());
    setModalMode("none");
    setNewProjectName("");
  };

  const handleRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!renameProjectName.trim() || !activeProject) return;
    await onRenameProject(activeProject.id, renameProjectName.trim());
    setModalMode("none");
  };

  const handleDeleteConfirm = async () => {
    if (!activeProject || projects.length <= 1) return;
    await onDeleteProject(activeProject.id);
    setModalMode("none");
  };

  return (
    <div className="relative inline-block text-left">
      {/* Active Project Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-3.5 py-2 text-xs font-bold text-[var(--navy-dark)] shadow-sm transition hover:border-[var(--accent-amber)] hover:bg-[var(--surface-column)] focus:outline-none"
        aria-expanded={isOpen}
        aria-haspopup="true"
        aria-label="Switch project"
      >
        <span className="text-sm">📁</span>
        <span className="max-w-[150px] sm:max-w-[180px] truncate">{activeProject.name}</span>
        <span className="text-[10px] text-[var(--gray-text)] font-mono">▾</span>
      </button>

      {/* Glassmorphic Dropdown Menu */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute left-0 mt-2 w-64 rounded-3xl glass-floating p-2 shadow-2xl z-50 animate-in zoom-in-95 duration-150">
            <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-[var(--gray-text)] border-b border-[var(--stroke)]/60 font-mono">
              Workspace Projects
            </div>

            <div className="max-h-56 overflow-y-auto py-1 scrollbar-none space-y-0.5">
              {safeProjects.map((proj) => {
                const isActive = proj.id === activeProject.id;
                return (
                  <button
                    key={proj.id}
                    type="button"
                    onClick={() => {
                      onSelectProject(proj.id);
                      setIsOpen(false);
                    }}
                    className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-xs font-semibold transition ${
                      isActive
                        ? "bg-[var(--accent-amber)]/15 text-[var(--accent-amber)] border border-[var(--accent-amber)]/30 font-bold"
                        : "text-[var(--navy-dark)] hover:bg-[var(--surface-column)]"
                    }`}
                  >
                    <span className="truncate">{proj.name}</span>
                    {isActive && <span className="text-xs">✓</span>}
                  </button>
                );
              })}
            </div>

            <div className="pt-1.5 border-t border-[var(--stroke)]/60 flex flex-col gap-1">
              <button
                type="button"
                onClick={handleOpenCreate}
                className="flex w-full items-center gap-2 rounded-xl px-3 py-1.5 text-xs font-bold text-[var(--accent-amber)] hover:bg-[var(--accent-amber)]/10 transition"
              >
                <span>➕</span>
                <span>New Project</span>
              </button>

              {activeProject && (
                <div className="flex items-center gap-1 px-1">
                  <button
                    type="button"
                    onClick={handleOpenRename}
                    className="flex-1 flex items-center justify-center gap-1 rounded-xl px-2 py-1 text-[11px] font-semibold text-[var(--navy-dark)] hover:bg-[var(--surface-column)] transition"
                  >
                    ✏️ Rename
                  </button>

                  {safeProjects.length > 1 && (
                    <button
                      type="button"
                      onClick={handleOpenDelete}
                      className="flex-1 flex items-center justify-center gap-1 rounded-xl px-2 py-1 text-[11px] font-semibold text-red-500 hover:bg-red-500/10 transition"
                    >
                      🗑️ Delete
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Modal Dialogs */}
      {modalMode === "create" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4 animate-in fade-in duration-150">
          <div className="w-full max-w-sm rounded-3xl glass-floating p-6 shadow-2xl">
            <h3 className="text-base font-extrabold text-[var(--navy-dark)]">
              Create New Project
            </h3>
            <form onSubmit={handleCreateSubmit} className="mt-4 flex flex-col gap-4">
              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-[var(--gray-text)] font-mono">
                  Project Name
                </label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="e.g. Q4 Marketing Campaign"
                  autoFocus
                  required
                  className="mt-1.5 w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-4 py-2.5 text-xs font-semibold text-[var(--navy-dark)] outline-none focus:border-[var(--accent-amber)]"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setModalMode("none")}
                  className="rounded-xl px-4 py-2 text-xs font-bold text-[var(--gray-text)] hover:bg-[var(--surface-column)] transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-xl bg-[var(--accent-amber)] px-4 py-2 text-xs font-bold text-black shadow-md hover:brightness-110 transition"
                >
                  Create Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {modalMode === "rename" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4 animate-in fade-in duration-150">
          <div className="w-full max-w-sm rounded-3xl glass-floating p-6 shadow-2xl">
            <h3 className="text-base font-extrabold text-[var(--navy-dark)]">
              Rename Project
            </h3>
            <form onSubmit={handleRenameSubmit} className="mt-4 flex flex-col gap-4">
              <div>
                <label className="text-[10px] font-bold uppercase tracking-wider text-[var(--gray-text)] font-mono">
                  Project Name
                </label>
                <input
                  type="text"
                  value={renameProjectName}
                  onChange={(e) => setRenameProjectName(e.target.value)}
                  autoFocus
                  required
                  className="mt-1.5 w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-4 py-2.5 text-xs font-semibold text-[var(--navy-dark)] outline-none focus:border-[var(--accent-amber)]"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setModalMode("none")}
                  className="rounded-xl px-4 py-2 text-xs font-bold text-[var(--gray-text)] hover:bg-[var(--surface-column)] transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-xl bg-[var(--accent-amber)] px-4 py-2 text-xs font-bold text-black shadow-md hover:brightness-110 transition"
                >
                  Save Name
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {modalMode === "delete" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4 animate-in fade-in duration-150">
          <div className="w-full max-w-sm rounded-3xl glass-floating p-6 shadow-2xl border border-red-500/30">
            <h3 className="text-base font-extrabold text-red-500">
              Delete Project?
            </h3>
            <p className="mt-2 text-xs text-[var(--gray-text)] leading-relaxed">
              Are you sure you want to delete <strong className="text-[var(--navy-dark)]">{activeProject.name}</strong>? All columns and tasks in this project will be permanently removed.
            </p>

            <div className="flex justify-end gap-2 pt-5">
              <button
                type="button"
                onClick={() => setModalMode("none")}
                className="rounded-xl px-4 py-2 text-xs font-bold text-[var(--gray-text)] hover:bg-[var(--surface-column)] transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteConfirm}
                className="rounded-xl bg-red-600 px-4 py-2 text-xs font-bold text-white shadow-md hover:bg-red-700 transition"
              >
                Yes, Delete Project
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
