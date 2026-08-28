"use client";

import { useState, useEffect, useCallback } from "react";
import {
  type NotificationItem,
  fetchNotificationsApi,
  markNotificationReadApi,
  markAllNotificationsReadApi,
} from "@/lib/api";

type NotificationCenterModalProps = {
  username: string;
  isOpen: boolean;
  onClose: () => void;
  onNotificationsChanged?: () => void;
};

const notifIcons: Record<string, string> = {
  due_soon: "⏰",
  assigned: "👤",
  invited: "✉️",
  system: "📢",
};

export const NotificationCenterModal = ({
  username,
  isOpen,
  onClose,
  onNotificationsChanged,
}: NotificationCenterModalProps) => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const loadNotifications = useCallback(async () => {
    if (!isOpen) return;
    setLoading(true);
    const data = await fetchNotificationsApi();
    setNotifications(data.notifications);
    setUnreadCount(data.unreadCount);
    setLoading(false);
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) {
      queueMicrotask(() => loadNotifications());
    }
  }, [isOpen, loadNotifications]);

  if (!isOpen) return null;

  const handleMarkRead = async (id: string) => {
    await markNotificationReadApi(id);
    loadNotifications();
    if (onNotificationsChanged) onNotificationsChanged();
  };

  const handleMarkAllRead = async () => {
    await markAllNotificationsReadApi();
    loadNotifications();
    if (onNotificationsChanged) onNotificationsChanged();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md p-4 overflow-y-auto animate-in fade-in duration-150">
      <div className="w-full max-w-lg rounded-3xl glass-floating p-6 shadow-2xl animate-in zoom-in-95 duration-150 my-8">
        <div className="flex items-center justify-between border-b border-[var(--stroke)] pb-4">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-[var(--surface-input)] border border-[var(--stroke)] text-base">
              🔔
            </span>
            <div>
              <h3 className="font-display text-xl font-bold text-[var(--navy-dark)]">
                Notifications & Reminders
              </h3>
              <p className="text-xs text-[var(--gray-text)] font-mono">
                {username ? `Alerts for @${username} • ` : ""}
                {unreadCount > 0 ? `${unreadCount} unread alert(s)` : "All caught up!"}
              </p>
            </div>
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

        {unreadCount > 0 && (
          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={handleMarkAllRead}
              className="text-xs font-bold text-[var(--accent-amber)] hover:underline font-mono"
            >
              ✓ Mark all as read
            </button>
          </div>
        )}

        {/* Notifications List */}
        <div className="mt-4 space-y-2.5 max-h-80 overflow-y-auto pr-1 scrollbar-none">
          {loading ? (
            <p className="text-center text-xs text-[var(--gray-text)] py-6 font-semibold">Loading notifications...</p>
          ) : notifications.length === 0 ? (
            <div className="text-center py-8 text-[var(--gray-text)]">
              <span className="text-3xl">🎉</span>
              <p className="mt-2 text-xs font-semibold">No notifications right now</p>
            </div>
          ) : (
            notifications.map((n) => {
              const icon = notifIcons[n.type] || "📢";
              return (
                <div
                  key={n.id}
                  onClick={() => !n.isRead && handleMarkRead(n.id)}
                  className={`flex items-start gap-3 rounded-2xl border p-3.5 transition cursor-pointer ${
                    n.isRead
                      ? "border-[var(--stroke)] bg-[var(--surface-input)]/50 opacity-70"
                      : "border-[var(--accent-amber)]/40 bg-[var(--accent-amber)]/5 shadow-xs"
                  }`}
                >
                  <span className="text-base mt-0.5">{icon}</span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-bold text-[var(--navy-dark)]">{n.title}</p>
                      {!n.isRead && (
                        <span className="h-2 w-2 rounded-full bg-[var(--accent-amber)] animate-pulse" title="Unread" />
                      )}
                    </div>
                    <p className="mt-1 text-xs leading-relaxed text-[var(--gray-text)]">{n.message}</p>
                    {n.createdAt && (
                      <p className="mt-1.5 text-[10px] font-semibold text-[var(--gray-text)] opacity-75 font-mono">
                        {new Date(n.createdAt).toLocaleString()}
                      </p>
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
