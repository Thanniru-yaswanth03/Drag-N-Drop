"use client";

import { useState, type FormEvent } from "react";
import { registerApi } from "@/lib/api";

type LoginFormProps = {
  onLogin: (username: string, password: string) => Promise<boolean> | boolean;
  onRegisterSuccess?: (username: string) => void;
};

export const LoginForm = ({ onLogin, onRegisterSuccess }: LoginFormProps) => {
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const cleanUser = username.trim();
      if (!cleanUser || !password) {
        setError("Please provide both username and password.");
        setLoading(false);
        return;
      }

      if (isRegistering) {
        const regRes = await registerApi(cleanUser, password);
        if (!regRes.success) {
          setError(regRes.error || "Registration failed. Try a different username.");
          setLoading(false);
          return;
        }

        if (typeof localStorage !== "undefined") {
          if (regRes.token) {
            localStorage.setItem("pm_auth_token", regRes.token);
          }
        }

        if (onRegisterSuccess) {
          onRegisterSuccess(cleanUser);
        } else {
          const success = await onLogin(cleanUser, password);
          if (!success && regRes.token && typeof window !== "undefined") {
            window.location.reload();
          }
        }
        return;
      }

      const success = await onLogin(cleanUser, password);
      if (!success) {
        setError("Invalid username or password.");
      }
    } catch {
      setError("An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-4 py-12">
      {/* Background Radial Ambiance */}
      <div className="pointer-events-none absolute left-0 top-0 h-[550px] w-[550px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(245,158,11,0.14)_0%,_rgba(245,158,11,0.02)_60%,_transparent_75%)] blur-3xl" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[650px] w-[650px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(6,182,212,0.12)_0%,_rgba(6,182,212,0.02)_60%,_transparent_75%)] blur-3xl" />

      <main className="relative w-full max-w-md">
        <div className="rounded-[36px] glass-floating p-8 shadow-[var(--shadow-floating)] backdrop-blur-3xl transition-all duration-300">
          <div className="text-center">
            <div className="mx-auto inline-flex items-center gap-2 rounded-full border border-[var(--stroke)] bg-[var(--surface-input)] px-4 py-1.5 text-[10px] font-bold uppercase tracking-[0.25em] text-[var(--navy-dark)] shadow-2xs font-mono">
              <span className="h-2 w-2 rounded-full bg-[var(--accent-amber)] animate-pulse" />
              Spatial Command Center • YASH 🐐
            </div>

            {/* Auth Mode Toggle Tabs */}
            <div className="mt-6 flex rounded-2xl bg-[var(--surface-input)] p-1 border border-[var(--stroke)]">
              <button
                type="button"
                onClick={() => { setIsRegistering(false); setError(null); }}
                className={`flex-1 rounded-xl py-2 text-xs font-bold transition ${
                  !isRegistering
                    ? "bg-[var(--surface-column)] text-[var(--navy-dark)] shadow-sm border border-[var(--stroke)]"
                    : "text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => { setIsRegistering(true); setError(null); }}
                className={`flex-1 rounded-xl py-2 text-xs font-bold transition ${
                  isRegistering
                    ? "bg-[var(--surface-column)] text-[var(--navy-dark)] shadow-sm border border-[var(--stroke)]"
                    : "text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
                }`}
              >
                Create Account
              </button>
            </div>

            <h1 className="mt-5 font-display text-2xl sm:text-3xl font-extrabold text-[var(--navy-dark)] tracking-tight">
              {isRegistering ? "Register Account" : "Sign In"}
            </h1>
            <p className="mt-2 text-xs font-medium leading-relaxed text-[var(--gray-text)]">
              {isRegistering
                ? "Create a new user account to manage your spatial workspace."
                : "Access your spatial project command board."}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            {error && (
              <div
                role="alert"
                className="rounded-2xl border border-red-500/30 bg-red-500/10 p-3.5 text-xs font-semibold text-red-400"
              >
                {error}
              </div>
            )}

            <div>
              <label
                htmlFor="username"
                className="block text-[10px] font-bold uppercase tracking-wider text-[var(--navy-dark)] mb-1.5 font-mono"
              >
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="user"
                required
                className="w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-4 py-3 text-sm font-semibold text-[var(--navy-dark)] placeholder:text-[var(--gray-text)] outline-none transition focus:border-[var(--accent-amber)]"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-[10px] font-bold uppercase tracking-wider text-[var(--navy-dark)] mb-1.5 font-mono"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface-input)] px-4 py-3 text-sm font-semibold text-[var(--navy-dark)] placeholder:text-[var(--gray-text)] outline-none transition focus:border-[var(--accent-amber)]"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="mt-6 w-full rounded-2xl bg-[var(--accent-amber)] py-3.5 text-xs font-bold uppercase tracking-widest text-black shadow-xl transition hover:brightness-110 active:scale-[0.98] disabled:opacity-50"
            >
              {loading
                ? isRegistering
                  ? "Creating Account..."
                  : "Signing in..."
                : isRegistering
                ? "Create Account"
                : "Sign In"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
};
