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
    if (!username || !isOpen) return;
    setLoading(true);
    const data = await fetchNotificationsApi(username);
    setNotifications(data.notifications);
    setUnreadCount(data.unreadCount);
    setLoading(false);
  }, [username, isOpen]);

  useEffect(() => {
    if (isOpen && username) {
      queueMicrotask(() => loadNotifications());
    }
  }, [isOpen, username, loadNotifications]);

  if (!isOpen) return null;

  const handleMarkRead = async (id: string) => {
    await markNotificationReadApi(id, username);
    loadNotifications();
    if (onNotificationsChanged) onNotificationsChanged();
  };

  const handleMarkAllRead = async () => {
    await markAllNotificationsReadApi(username);
    loadNotifications();
    if (onNotificationsChanged) onNotificationsChanged();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="w-full max-w-lg rounded-[28px] border border-[var(--stroke)] bg-[var(--card-bg)] p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200 my-8">
        <div className="flex items-center justify-between border-b border-[var(--stroke)] pb-4">
          <div className="flex items-center gap-2">
            <span className="text-xl">🔔</span>
            <div>
              <h3 className="font-display text-xl font-semibold text-[var(--navy-dark)]">
                Notifications & Reminders
              </h3>
              <p className="text-xs text-[var(--gray-text)]">
                {unreadCount > 0 ? `${unreadCount} unread message(s)` : "All caught up!"}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-full p-2 text-[var(--gray-text)] hover:bg-[var(--surface)] hover:text-[var(--navy-dark)] transition"
          >
            ✕
          </button>
        </div>

        {unreadCount > 0 && (
          <div className="mt-4 flex justify-end">
            <button
              type="button"
              onClick={handleMarkAllRead}
              className="text-xs font-bold text-[var(--primary-blue)] hover:underline"
            >
              ✓ Mark all as read
            </button>
          </div>
        )}

        {/* Notifications List */}
        <div className="mt-4 space-y-2.5 max-h-80 overflow-y-auto pr-1">
          {loading ? (
            <p className="text-center text-xs text-[var(--gray-text)] py-4">Loading notifications...</p>
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
                      ? "border-[var(--stroke)]/60 bg-[var(--surface)]/50 opacity-75"
                      : "border-[var(--primary-blue)]/40 bg-[var(--primary-blue)]/5 shadow-xs"
                  }`}
                >
                  <span className="text-lg mt-0.5">{icon}</span>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-bold text-[var(--navy-dark)]">{n.title}</p>
                      {!n.isRead && (
                        <span className="h-2 w-2 rounded-full bg-[var(--primary-blue)]" title="Unread" />
                      )}
                    </div>
                    <p className="mt-1 text-xs leading-relaxed text-[var(--gray-text)]">{n.message}</p>
                    {n.createdAt && (
                      <p className="mt-1.5 text-[10px] font-semibold text-[var(--gray-text)] opacity-75">
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
            className="rounded-xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-2 text-xs font-bold text-[var(--navy-dark)] hover:bg-[var(--stroke)]"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
