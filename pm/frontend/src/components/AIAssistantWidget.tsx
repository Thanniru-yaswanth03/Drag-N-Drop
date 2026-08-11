"use client";

import { useState, useRef, useEffect, type FormEvent } from "react";
import type { BoardData } from "@/lib/kanban";
import { getApiUrl } from "@/lib/api";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  time: string;
};

type AIAssistantWidgetProps = {
  board: BoardData;
  projectId?: string | null;
  onBoardUpdate: (nextBoard: BoardData, notificationMessage?: string) => void;
};

export const AIAssistantWidget = ({ board, projectId, onBoardUpdate }: AIAssistantWidgetProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "msg-welcome",
      role: "assistant",
      content:
        "Hello! I am your AI Kanban Assistant. Ask me to clear cards from columns, add new tasks, or move cards!",
      time: "Just now",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSend = async (messageText: string) => {
    if (!messageText.trim() || loading) return;

    const userMsg: Message = {
      id: `usr-${Date.now()}`,
      role: "user",
      content: messageText.trim(),
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const activeUser = localStorage.getItem("pm_auth_user") || "user";
      const response = await fetch(getApiUrl(`/api/ai/chat?username=${encodeURIComponent(activeUser)}`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: messageText.trim(),
          history,
          board,
          project_id: projectId || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();

      const aiMsg: Message = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        content: data.reply || "I completed your request.",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, aiMsg]);

      // Automatically refresh Kanban board if AI performed a board update
      if (data.board_update) {
        onBoardUpdate(data.board_update, data.reply);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: `Connection error: ${error instanceof Error ? error.message : "Unable to reach AI service."}`,
          time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    handleSend(input);
  };

  const renderContent = (content: string) => {
    // Render bold (**text**) and italic (*text*) syntax cleanly
    const parts = content.split(/(\*\*.*?\*\*|\*.*?\*)/g);
    return parts.map((part, idx) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={idx} className="font-semibold text-[var(--primary-blue)]">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
        return <em key={idx} className="italic text-gray-400">{part.slice(1, -1)}</em>;
      }
      return part;
    });
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Trigger Button */}
      {!isOpen && (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="group relative flex items-center gap-3 rounded-full bg-gradient-to-r from-[var(--secondary-purple)] to-[var(--primary-blue)] px-5 py-3.5 text-xs font-bold uppercase tracking-wider text-white shadow-2xl transition hover:scale-105 active:scale-95"
          aria-label="Open AI Assistant"
        >
          <span className="relative flex h-3 w-3">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-3 w-3 rounded-full bg-emerald-500" />
          </span>
          <span className="text-sm">✨</span>
          <span>AI Assistant</span>
        </button>
      )}

      {/* Floating Chat Drawer Window */}
      {isOpen && (
        <div className="flex h-[580px] w-[calc(100vw-32px)] sm:w-[420px] max-w-[420px] flex-col rounded-[28px] border border-[var(--stroke)] bg-[var(--card-bg)] shadow-2xl backdrop-blur-xl animate-in fade-in slide-in-from-bottom-6 duration-200">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[var(--stroke)] px-6 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-gradient-to-tr from-[var(--secondary-purple)] to-[var(--primary-blue)] text-white shadow-md text-base">
                ✨
              </div>
              <div>
                <h3 className="font-display text-sm font-semibold text-[var(--navy-dark)]">
                  Kanban AI Assistant
                </h3>
                <p className="text-[10px] uppercase tracking-wider text-[var(--gray-text)] font-semibold">
                  NLP Powered • Auto Persistence
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="rounded-full p-2 text-[var(--gray-text)] hover:bg-[var(--surface)] hover:text-[var(--navy-dark)]"
            >
              ✕
            </button>
          </div>

          {/* Quick Suggestion Chips */}
          <div className="flex gap-2 overflow-x-auto px-6 py-3 border-b border-[var(--stroke)] scrollbar-none">
            {[
              "What are my backlogs for today?",
              "Clear a card from In Progress",
              "Add a task for QA Testing",
              "Move card to Done",
              "Board status summary",
            ].map((chip) => (
              <button
                key={chip}
                type="button"
                onClick={() => handleSend(chip)}
                disabled={loading}
                className="whitespace-nowrap rounded-full border border-[var(--stroke)] bg-[var(--surface)] px-3.5 py-1 text-[11px] font-medium text-[var(--navy-dark)] transition hover:border-[var(--primary-blue)] hover:bg-[var(--primary-blue)]/10 disabled:opacity-50"
              >
                {chip}
              </button>
            ))}
          </div>

          {/* Chat Message History */}
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${
                  msg.role === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`max-w-[88%] rounded-2xl px-4 py-3 text-xs leading-relaxed whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "bg-[var(--secondary-purple)] text-white shadow-sm"
                      : "border border-[var(--stroke)] bg-[var(--surface)] text-[var(--navy-dark)]"
                  }`}
                >
                  {renderContent(msg.content)}
                </div>
                <span className="mt-1 text-[10px] text-[var(--gray-text)] px-1">
                  {msg.time}
                </span>
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-2 text-xs text-[var(--gray-text)]">
                <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--primary-blue)]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--secondary-purple)] delay-100" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-[var(--accent-yellow)] delay-200" />
                <span className="ml-1 text-[11px]">Processing request...</span>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Quick AI Intelligence Action Presets */}
          <div className="flex flex-wrap items-center gap-1.5 px-4 pt-2.5">
            <button
              type="button"
              onClick={() => handleSend("Summarize project")}
              disabled={loading}
              className="rounded-full border border-[var(--stroke)] bg-[var(--surface)] px-2.5 py-1 text-[10px] font-bold text-[var(--navy-dark)] hover:bg-[var(--primary-blue)] hover:text-white transition disabled:opacity-50"
            >
              📊 Project Summary
            </button>
            <button
              type="button"
              onClick={() => handleSend("Workload analysis")}
              disabled={loading}
              className="rounded-full border border-[var(--stroke)] bg-[var(--surface)] px-2.5 py-1 text-[10px] font-bold text-[var(--navy-dark)] hover:bg-[var(--primary-blue)] hover:text-white transition disabled:opacity-50"
            >
              👥 Workload
            </button>
            <button
              type="button"
              onClick={() => handleSend("Overdue tasks")}
              disabled={loading}
              className="rounded-full border border-[var(--stroke)] bg-[var(--surface)] px-2.5 py-1 text-[10px] font-bold text-[var(--navy-dark)] hover:bg-[var(--primary-blue)] hover:text-white transition disabled:opacity-50"
            >
              ⏰ Overdue
            </button>
            <button
              type="button"
              onClick={() => handleSend("Suggest organization")}
              disabled={loading}
              className="rounded-full border border-[var(--stroke)] bg-[var(--surface)] px-2.5 py-1 text-[10px] font-bold text-[var(--navy-dark)] hover:bg-[var(--primary-blue)] hover:text-white transition disabled:opacity-50"
            >
              ⚡ Re-Prioritize
            </button>
          </div>

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="border-t border-[var(--stroke)] p-4 pt-2">
            <div className="flex items-center gap-2 rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-3.5 py-2.5">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask AI or pick an action above..."
                disabled={loading}
                className="w-full bg-transparent text-xs font-medium text-[var(--navy-dark)] outline-none placeholder:text-[var(--gray-text)]"
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="flex h-8 w-8 items-center justify-center rounded-xl bg-[var(--secondary-purple)] text-white transition hover:brightness-110 disabled:opacity-40"
              >
                ➔
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
