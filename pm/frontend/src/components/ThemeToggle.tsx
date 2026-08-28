"use client";

import { useEffect, useState } from "react";

export const ThemeToggle = () => {
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof window === "undefined") return "dark";
    const saved = localStorage.getItem("pm_theme") as "light" | "dark" | null;
    if (saved) return saved;
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches) return "light";
    return "dark";
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
      className="flex items-center gap-1.5 rounded-full border border-[var(--stroke)] bg-[var(--surface-input)] px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-[var(--navy-dark)] shadow-2xs transition hover:border-[var(--accent-amber)] hover:bg-[var(--surface-column)] active:scale-95"
      aria-label="Toggle theme"
    >
      {theme === "light" ? (
        <>
          <span className="text-amber-500">☀️</span> Light
        </>
      ) : (
        <>
          <span className="text-amber-400">🌙</span> Dark
        </>
      )}
    </button>
  );
};
