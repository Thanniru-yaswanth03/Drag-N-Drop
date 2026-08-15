"use client";

import { useEffect, useState } from "react";

export const ThemeToggle = () => {
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof window === "undefined") return "light";
    const saved = localStorage.getItem("pm_theme") as "light" | "dark" | null;
    if (saved) return saved;
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) return "dark";
    return "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    localStorage.setItem("pm_theme", nextTheme);
    document.documentElement.setAttribute("data-theme", nextTheme);
  };

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="flex items-center gap-2 rounded-full border border-[var(--stroke)] bg-[var(--surface-strong)] px-3.5 py-1.5 text-xs font-semibold uppercase tracking-wider text-[var(--navy-dark)] shadow-sm transition hover:scale-105 active:scale-95"
      aria-label="Toggle theme"
    >
      {theme === "light" ? (
        <>
          <span className="text-amber-500">☀️</span> Light
        </>
      ) : (
        <>
          <span className="text-indigo-400">🌙</span> Dark
        </>
      )}
    </button>
  );
};
