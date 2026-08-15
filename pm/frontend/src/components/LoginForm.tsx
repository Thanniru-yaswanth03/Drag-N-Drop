"use client";

import { useState, type FormEvent } from "react";
import { registerApi } from "@/lib/api";

type LoginFormProps = {
  onLogin: (username: string, password: string) => Promise<boolean> | boolean;
};

export const LoginForm = ({ onLogin }: LoginFormProps) => {
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

        const targetUser = regRes.user || cleanUser;
        localStorage.setItem("pm_auth_user", targetUser);
        const success = await onLogin(targetUser, password);
        if (!success && regRes.token) {
          // Registration already generated valid token, force reload to complete sign-in
          window.location.reload();
        }
        return;
      }

      const success = await onLogin(cleanUser, password);
      if (!success) {
        setError("Invalid username or password. (Hint: user / password)");
      }
    } catch {
      setError("An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleAutoFill = () => {
    setIsRegistering(false);
    setUsername("user");
    setPassword("password");
  };

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-4 py-12">
      {/* Background Radial Gradients */}
      <div className="pointer-events-none absolute left-0 top-0 h-[500px] w-[500px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(2,132,199,0.25)_0%,_rgba(2,132,199,0.02)_60%,_transparent_75%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[600px] w-[600px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(147,51,234,0.2)_0%,_rgba(147,51,234,0.02)_60%,_transparent_75%)]" />

      <main className="relative w-full max-w-md">
        <div className="rounded-[36px] border border-[var(--stroke)] bg-[var(--card-bg)] p-8 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.15)] backdrop-blur-2xl transition-all duration-300">
          <div className="text-center">
            <div className="mx-auto inline-flex items-center gap-2 rounded-full border border-[var(--stroke)] bg-[var(--surface)] px-4 py-1.5 text-xs font-bold uppercase tracking-[0.25em] text-[var(--navy-dark)] shadow-2xs">
              <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)] animate-pulse" />
              Drag N Drop • YASH 🐐
            </div>

            {/* Auth Mode Toggle Tabs */}
            <div className="mt-6 flex rounded-2xl bg-[var(--surface)] p-1 border border-[var(--stroke)]">
              <button
                type="button"
                onClick={() => { setIsRegistering(false); setError(null); }}
                className={`flex-1 rounded-xl py-2 text-xs font-bold transition ${
                  !isRegistering
                    ? "bg-[var(--card-bg)] text-[var(--navy-dark)] shadow-sm"
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
                    ? "bg-[var(--card-bg)] text-[var(--navy-dark)] shadow-sm"
                    : "text-[var(--gray-text)] hover:text-[var(--navy-dark)]"
                }`}
              >
                Create Account
              </button>
            </div>

            <h1 className="mt-4 font-display text-3xl sm:text-4xl font-extrabold text-[var(--navy-dark)] tracking-tight">
              {isRegistering ? "Register Account" : "Sign In"}
            </h1>
            <p className="mt-2 text-xs sm:text-sm font-medium leading-relaxed text-[var(--gray-text)]">
              {isRegistering
                ? "Create a new user account to manage your projects."
                : "Access your project management workspace."}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            {error && (
              <div
                role="alert"
                className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-xs font-semibold text-red-600 dark:text-red-400"
              >
                {error}
              </div>
            )}

            <div>
              <label
                htmlFor="username"
                className="block text-xs font-bold uppercase tracking-wider text-[var(--navy-dark)] mb-1.5"
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
                className="w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3.5 text-xs font-semibold text-[var(--navy-dark)] placeholder:text-[var(--gray-text)] outline-none transition focus:border-[var(--primary-blue)] focus:ring-2 focus:ring-[var(--primary-blue)]/20"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-xs font-bold uppercase tracking-wider text-[var(--navy-dark)] mb-1.5"
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
                className="w-full rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-4 py-3.5 text-xs font-semibold text-[var(--navy-dark)] placeholder:text-[var(--gray-text)] outline-none transition focus:border-[var(--primary-blue)] focus:ring-2 focus:ring-[var(--primary-blue)]/20"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="mt-6 w-full rounded-2xl bg-gradient-to-r from-[var(--secondary-purple)] to-[var(--primary-blue)] py-4 text-xs font-bold uppercase tracking-widest text-white shadow-xl transition hover:brightness-110 active:scale-[0.98] disabled:opacity-50"
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

          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={handleAutoFill}
              className="inline-flex items-center gap-1.5 rounded-full border border-[var(--stroke)] bg-[var(--surface)] px-4 py-2 text-xs font-medium text-[var(--gray-text)] transition hover:border-[var(--primary-blue)] hover:text-[var(--primary-blue)]"
            >
              <span>🔑</span> Demo credentials: <strong className="text-[var(--navy-dark)]">user / password</strong> (click to auto-fill)
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};
