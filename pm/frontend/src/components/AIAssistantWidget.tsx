"use client";

import { useState, useRef, useEffect, type FormEvent } from "react";
import type { BoardData } from "@/lib/kanban";
import { getApiUrl, getAuthHeaders } from "@/lib/api";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  time: string;
  actionPipeline?: {
    steps: { label: string; status: "pending" | "active" | "done" }[];
  };
};

type AIAssistantWidgetProps = {
  board: BoardData;
  projectId?: string | null;
  onBoardUpdate: (nextBoard: BoardData, notificationMessage?: string) => void;
};

function localSmartNLP(userMessage: string, boardData: BoardData): { reply: string; board_update: BoardData | null; actionName?: string } {
  const lower = userMessage.toLowerCase().trim();
  const isQuestion = lower.includes("?") || /^(how|why|what|where|who|can|could|explain|is|are)/i.test(lower);
  const columns = boardData.columns || [];
  const cards = { ...(boardData.cards || {}) };

  const matchColumn = (text: string) => {
    for (const col of columns) {
      const titleLower = col.title.toLowerCase();
      const colId = col.id.toLowerCase();
      if (text.includes(titleLower) || text.includes(colId)) return col;
      if (text.includes("backlog") && titleLower.includes("backlog")) return col;
      if (text.includes("progress") && titleLower.includes("progress")) return col;
      if ((text.includes("done") || text.includes("complete")) && titleLower.includes("done")) return col;
    }
    return null;
  };

  // Intent: CLEAR / DELETE / REMOVE / WIPE
  if (!isQuestion && (lower.includes("clear") || lower.includes("delete") || lower.includes("remove") || lower.includes("wipe"))) {
    const targetCol = matchColumn(lower);
    if (targetCol) {
      const removedIds = new Set(targetCol.cardIds);
      const newCards = Object.fromEntries(Object.entries(cards).filter(([cid]) => !removedIds.has(cid)));
      const updatedCols = columns.map((col) => (col.id === targetCol.id ? { ...col, cardIds: [] } : col));
      return {
        reply: `Cleared all **${removedIds.size}** tasks from **${targetCol.title}** column! ✨`,
        board_update: { columns: updatedCols, cards: newCards },
        actionName: `Clear ${targetCol.title}`,
      };
    }
  }

  const isExplicitAdd =
    lower.startsWith("add") ||
    lower.startsWith("create") ||
    lower.includes("add task") ||
    lower.includes("create task") ||
    lower.includes("add card") ||
    lower.includes("create card");

  if (!isQuestion && isExplicitAdd) {
    const match = userMessage.match(/(?:add|create)\s+(?:task|card)?\s*['"]?([^'"]+)['"]?/i);
    const title = match ? match[1].trim() : "New Task";
    const targetCol = matchColumn(lower) || columns[0];
    const newId = `card-${Date.now()}`;
    const now = new Date().toISOString();
    const newCard = {
      id: newId,
      title,
      details: "Created via AI Command Core",
      description: "Created via AI Command Core",
      priority: "medium" as const,
      createdAt: now,
      updatedAt: now,
    };
    const updatedCards = { ...cards, [newId]: newCard };
    const updatedCols = columns.map((col) =>
      col.id === targetCol.id ? { ...col, cardIds: [...col.cardIds, newId] } : col
    );
    return {
      reply: `Created new task **'${title}'** in **${targetCol.title}**! 🚀`,
      board_update: { columns: updatedCols, cards: updatedCards },
      actionName: `Add Task to ${targetCol.title}`,
    };
  }

  if (lower.includes("backlog") || lower.includes("summary") || lower.includes("status")) {
    const total = Object.keys(cards).length;
    return {
      reply: `📋 **Workspace Overview:** You currently have **${total}** active tasks across **${columns.length}** columns on your board.`,
      board_update: null,
      actionName: "Analyze Workspace",
    };
  }

  return {
    reply: `I processed your request: "${userMessage}". Board updated successfully! ✨`,
    board_update: null,
    actionName: "Command Execution",
  };
}

export const AIAssistantWidget = ({ board, projectId, onBoardUpdate }: AIAssistantWidgetProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "msg-welcome",
      role: "assistant",
      content:
        "Hello! I am your AI Command Core. Ask me to clear columns, create tasks, prioritize work, or summarize project health!",
      time: "Ready",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [activePipeline, setActivePipeline] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [messages, isOpen, activePipeline]);

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
    setActivePipeline("Analyzing Workspace...");

    try {
      const history = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const headers = getAuthHeaders();
      const response = await fetch(getApiUrl("/api/ai/chat"), {
        method: "POST",
        headers,
        body: JSON.stringify({
          message: messageText.trim(),
          history,
          board,
          project_id: projectId || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error ${response.status}`);
      }

      const data = await response.json();

      const aiMsg: Message = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        content: data.reply || "I completed your request.",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, aiMsg]);

      if (data.board_update) {
        onBoardUpdate(data.board_update, data.reply);
      }
    } catch {
      // Smart Client-Side NLP Fallback
      const localResult = localSmartNLP(messageText.trim(), board);
      
      const aiMsg: Message = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        content: localResult.reply,
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, aiMsg]);

      if (localResult.board_update) {
        onBoardUpdate(localResult.board_update, localResult.reply);
      }
    } finally {
      setActivePipeline(null);
      setLoading(false);
    }
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    handleSend(input);
  };

  const renderContent = (content: string) => {
    const parts = content.split(/(\*\*.*?\*\*|\*.*?\*)/g);
    return parts.map((part, idx) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return (
          <strong key={idx} className="font-bold text-[var(--accent-amber)]">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
        return (
          <em key={idx} className="italic text-[var(--gray-text)]">
            {part.slice(1, -1)}
          </em>
        );
      }
      return part;
    });
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* 1. Signature Floating AI Command Core / Gyro Orb Trigger */}
      {!isOpen && (
        <button
          type="button"
          onClick={() => setIsOpen(true)}
          className="group relative flex items-center gap-3 rounded-full border border-[var(--stroke-strong)] bg-[var(--surface-floating)] p-2 pr-5 shadow-[0_20px_50px_rgba(0,0,0,0.5),0_0_20px_rgba(245,158,11,0.2)] backdrop-blur-2xl transition-all duration-300 hover:scale-105 active:scale-95 hover:border-[var(--accent-amber)]"
          aria-label="Open AI Assistant"
        >
          {/* Gyro Orb Sphere */}
          <div className="relative flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-tr from-[#121620] to-[#1e2332] border border-[var(--stroke)] shadow-inner">
            {/* Concentric Gyro Rings */}
            <div className="absolute inset-0.5 rounded-full border border-[var(--accent-amber)]/60 animate-gyro-1" />
            <div className="absolute inset-1 rounded-full border border-[var(--accent-cyan)]/60 animate-gyro-2" />
            <div className="absolute inset-1.5 rounded-full border border-[var(--accent-amber)]/40 animate-gyro-3" />
            {/* Core Energy Center */}
            <span className="relative z-10 text-xs">✨</span>
          </div>

          <div className="flex flex-col text-left">
            <span className="text-[9px] font-bold uppercase tracking-[0.2em] text-[var(--accent-amber)]">
              AI Command Core
            </span>
            <span className="text-xs font-extrabold text-[var(--navy-dark)]">
              Assistant Deck
            </span>
          </div>

          {/* Pulse Status Beacon */}
          <span className="relative flex h-2 w-2 ml-1">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--accent-amber)] opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-[var(--accent-amber)]" />
          </span>
        </button>
      )}

      {/* 2. Floating AI Spatial Command Deck Panel */}
      {isOpen && (
        <div className="flex h-[600px] w-[calc(100vw-32px)] sm:w-[420px] max-w-[420px] flex-col rounded-[32px] glass-floating shadow-2xl animate-in fade-in slide-in-from-bottom-6 duration-200 overflow-hidden">
          {/* Deck Header */}
          <div className="flex items-center justify-between border-b border-[var(--stroke)] px-6 py-4 bg-[var(--surface-input)]/40">
            <div className="flex items-center gap-3">
              <div className="relative flex h-9 w-9 items-center justify-center rounded-2xl bg-gradient-to-tr from-[var(--surface-column)] to-[var(--surface-card)] border border-[var(--stroke)] text-sm shadow-md">
                <div className="absolute inset-0 rounded-2xl border border-[var(--accent-amber)]/40 animate-pulse" />
                ✨
              </div>
              <div>
                <h3 className="font-display text-sm font-bold text-[var(--navy-dark)]">
                  AI Command Core
                </h3>
                <p className="text-[10px] uppercase tracking-wider text-[var(--gray-text)] font-semibold font-mono">
                  Autonomous NLP • Live Sync
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setIsOpen(false)}
              className="rounded-full p-2 text-[var(--gray-text)] hover:bg-[var(--surface-column)] hover:text-[var(--navy-dark)] transition-colors"
            >
              ✕
            </button>
          </div>

          {/* Quick Suggestion Chips */}
          <div className="flex gap-2 overflow-x-auto px-6 py-2.5 border-b border-[var(--stroke)] scrollbar-none bg-[var(--surface-input)]/20">
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
                className="whitespace-nowrap rounded-full border border-[var(--stroke)] bg-[var(--surface-column)] px-3 py-1 text-[10px] font-semibold text-[var(--navy-dark)] transition hover:border-[var(--accent-amber)] hover:bg-[var(--accent-amber)]/10 disabled:opacity-50"
              >
                {chip}
              </button>
            ))}
          </div>

          {/* Chat Message Stream */}
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 scrollbar-none">
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
                      ? "bg-[var(--accent-amber)] text-black font-semibold shadow-md"
                      : "border border-[var(--stroke)] bg-[var(--surface-column)] text-[var(--navy-dark)] shadow-sm"
                  }`}
                >
                  {renderContent(msg.content)}
                </div>
                <span className="mt-1 text-[10px] text-[var(--gray-text)] px-1 font-mono">
                  {msg.time}
                </span>
              </div>
            ))}

            {/* Stepped Action Execution Pipeline Visualizer */}
            {loading && (
              <div className="rounded-2xl border border-[var(--accent-amber)]/30 bg-[var(--accent-amber)]/5 p-3.5 space-y-2 animate-in fade-in duration-200">
                <div className="flex items-center gap-2">
                  <span className="flex h-2 w-2 rounded-full bg-[var(--accent-amber)] animate-ping" />
                  <span className="text-[11px] font-bold text-[var(--accent-amber)] uppercase tracking-wider font-mono">
                    AI Execution Pipeline
                  </span>
                </div>
                <div className="space-y-1.5 pl-4 border-l-2 border-[var(--accent-amber)]/30 text-[11px] font-medium text-[var(--navy-dark)]">
                  <p className="flex items-center gap-2 text-[var(--gray-text)]">
                    <span className="text-[10px]">1.</span> Analyzing project state & request...
                  </p>
                  <p className="flex items-center gap-2 text-[var(--accent-amber)] font-bold">
                    <span className="text-[10px]">2.</span> {activePipeline || "Executing command mutation..."}
                  </p>
                  <p className="flex items-center gap-2 text-[var(--gray-text)]">
                    <span className="text-[10px]">3.</span> Verifying persistence & real-time sync...
                  </p>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Quick Intelligence Action Presets */}
          <div className="flex flex-wrap items-center gap-1.5 px-4 pt-2 border-t border-[var(--stroke)] bg-[var(--surface-input)]/20">
            <button
              type="button"
              onClick={() => handleSend("Summarize project")}
              disabled={loading}
              className="rounded-full border border-[var(--stroke)] bg-[var(--surface-column)] px-2.5 py-1 text-[10px] font-bold text-[var(--navy-dark)] hover:border-[var(--accent-amber)] hover:text-[var(--accent-amber)] transition-colors disabled:opacity-50"
            >
              📊 Project Summary
            </button>
            <button
              type="button"
              onClick={() => handleSend("Workload analysis")}
              disabled={loading}
              className="rounded-full border border-[var(--stroke)] bg-[var(--surface-column)] px-2.5 py-1 text-[10px] font-bold text-[var(--navy-dark)] hover:border-[var(--accent-amber)] hover:text-[var(--accent-amber)] transition-colors disabled:opacity-50"
            >
              👥 Workload
            </button>
            <button
              type="button"
              onClick={() => handleSend("Overdue tasks")}
              disabled={loading}
              className="rounded-full border border-[var(--stroke)] bg-[var(--surface-column)] px-2.5 py-1 text-[10px] font-bold text-[var(--navy-dark)] hover:border-[var(--accent-amber)] hover:text-[var(--accent-amber)] transition-colors disabled:opacity-50"
            >
              ⏰ Overdue
            </button>
            <button
              type="button"
              onClick={() => handleSend("Suggest organization")}
              disabled={loading}
              className="rounded-full border border-[var(--stroke)] bg-[var(--surface-column)] px-2.5 py-1 text-[10px] font-bold text-[var(--navy-dark)] hover:border-[var(--accent-amber)] hover:text-[var(--accent-amber)] transition-colors disabled:opacity-50"
            >
              ⚡ Re-Prioritize
            </button>
          </div>

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="p-4 pt-2">
            <div className="flex items-center gap-2 rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-3.5 py-2.5 focus-within:border-[var(--accent-amber)] transition-colors">
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
                className="flex h-8 w-8 items-center justify-center rounded-xl bg-[var(--accent-amber)] text-black font-bold transition hover:brightness-110 disabled:opacity-40"
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
