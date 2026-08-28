"use client";

import { useState, useEffect, useCallback } from "react";
import {
  type ProjectMember,
  fetchProjectMembers,
  addProjectMemberApi,
  removeProjectMemberApi,
} from "@/lib/api";

type ProjectMembersModalProps = {
  projectId: string;
  currentUsername: string;
  isOpen: boolean;
  onClose: () => void;
  onMembersUpdated?: () => void;
};

const roleBadges: Record<string, { label: string; color: string }> = {
  owner: { label: "👑 Owner", color: "bg-amber-500/15 text-amber-400 border-amber-500/30" },
  admin: { label: "🛡️ Admin", color: "bg-purple-500/15 text-purple-400 border-purple-500/30" },
  member: { label: "👤 Member", color: "bg-blue-500/15 text-blue-400 border-blue-500/30" },
  viewer: { label: "👁️ Viewer", color: "bg-slate-500/15 text-slate-400 border-slate-500/30" },
};

export const ProjectMembersModal = ({
  projectId,
  currentUsername,
  isOpen,
  onClose,
  onMembersUpdated,
}: ProjectMembersModalProps) => {
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [userRole, setUserRole] = useState<string>("viewer");
  const [loading, setLoading] = useState(false);
  const [targetUsername, setTargetUsername] = useState("");
  const [selectedRole, setSelectedRole] = useState<string>("member");
  const [error, setError] = useState<string | null>(null);

  const loadMembers = useCallback(async () => {
    if (!projectId || !isOpen) return;
    setLoading(true);
    const data = await fetchProjectMembers(projectId);
    setMembers(data.members);
    setUserRole(data.userRole);
    setLoading(false);
  }, [projectId, isOpen]);

  useEffect(() => {
    if (isOpen && projectId) {
      queueMicrotask(() => loadMembers());
    }
  }, [isOpen, projectId, loadMembers]);

  if (!isOpen) return null;

  const canManage = userRole === "owner" || userRole === "admin";

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetUsername.trim()) return;
    setError(null);

    const res = await addProjectMemberApi(
      projectId,
      targetUsername.trim(),
      selectedRole
    );

    if (res.success) {
      setTargetUsername("");
      loadMembers();
      if (onMembersUpdated) onMembersUpdated();
    } else {
      setError(res.error || "Failed to add member.");
    }
  };

  const handleRemoveMember = async (usernameToRemove: string) => {
    if (!confirm(`Are you sure you want to remove @${usernameToRemove} from this project?`)) return;
    setError(null);
    const res = await removeProjectMemberApi(projectId, usernameToRemove);

    if (res.success) {
      loadMembers();
      if (onMembersUpdated) onMembersUpdated();
    } else {
      setError(res.error || "Failed to remove member.");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4 overflow-y-auto animate-in fade-in duration-150">
      <div className="w-full max-w-lg rounded-3xl glass-floating p-6 shadow-2xl animate-in zoom-in-95 duration-150 my-8">
        <div className="flex items-center justify-between border-b border-[var(--stroke)] pb-4">
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--accent-amber)] font-mono">
              Collaboration & RBAC
            </span>
            <h3 className="font-display text-xl font-bold text-[var(--navy-dark)]">
              Project Team Members
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

        {error && (
          <div
            role="alert"
            className="mt-4 rounded-2xl border border-red-500/30 bg-red-500/10 p-3 text-xs font-semibold text-red-400"
          >
            {error}
          </div>
        )}

        {/* Add Member Form (Admin/Owner only) */}
        {canManage && (
          <form onSubmit={handleAddMember} className="mt-4 flex flex-col sm:flex-row gap-2">
            <input
              type="text"
              value={targetUsername}
              onChange={(e) => setTargetUsername(e.target.value)}
              placeholder="Username (e.g. dev_alex)"
              required
              className="flex-1 rounded-xl border border-[var(--stroke)] bg-[var(--surface-input)] px-3.5 py-2 text-xs font-semibold text-[var(--navy-dark)] outline-none focus:border-[var(--accent-amber)]"
              aria-label="New member username"
            />
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="rounded-xl border border-[var(--stroke)] bg-[var(--surface-input)] px-3 py-2 text-xs font-semibold text-[var(--navy-dark)] outline-none cursor-pointer"
              aria-label="Select role"
            >
              <option value="admin">Admin</option>
              <option value="member">Member</option>
              <option value="viewer">Viewer</option>
            </select>
            <button
              type="submit"
              className="rounded-xl bg-[var(--accent-amber)] px-4 py-2 text-xs font-bold text-black transition hover:brightness-110"
            >
              + Invite
            </button>
          </form>
        )}

        {/* Member List */}
        <div className="mt-5 space-y-2 max-h-72 overflow-y-auto pr-1 scrollbar-none">
          {loading ? (
            <p className="text-center text-xs text-[var(--gray-text)] py-4 font-semibold">Loading members...</p>
          ) : members.length === 0 ? (
            <p className="text-center text-xs text-[var(--gray-text)] py-4 font-semibold">No team members found.</p>
          ) : (
            members.map((m) => {
              const badge = roleBadges[m.role] || roleBadges.member;
              const isOwner = m.role === "owner";
              return (
                <div
                  key={m.id}
                  className="flex items-center justify-between rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] p-3 shadow-2xs"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[var(--surface-column)] border border-[var(--stroke)] text-xs font-bold text-[var(--accent-amber)] uppercase font-mono">
                      {m.username.substring(0, 2)}
                    </div>
                    <div>
                      <p className="text-xs font-bold text-[var(--navy-dark)]">
                        @{m.username}{" "}
                        {m.username.toLowerCase() === currentUsername.toLowerCase() && (
                          <span className="text-[10px] text-[var(--accent-amber)] font-normal font-mono">(You)</span>
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-bold font-mono ${badge.color}`}
                    >
                      {badge.label}
                    </span>
                    {canManage && !isOwner && m.username.toLowerCase() !== currentUsername.toLowerCase() && (
                      <button
                        type="button"
                        onClick={() => handleRemoveMember(m.username)}
                        className="rounded-lg p-1 text-xs text-[var(--gray-text)] hover:bg-red-500/10 hover:text-red-500 transition"
                        title="Remove member"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div className="mt-6 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-[var(--stroke)] bg-[var(--surface-input)] px-5 py-2 text-xs font-bold text-[var(--navy-dark)] hover:bg-[var(--surface-column)]"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
