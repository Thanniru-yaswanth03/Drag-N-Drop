"use client";

import { useEffect, useState, memo } from "react";

export const SpatialBackground = memo(() => {
  const [mousePos, setMousePos] = useState<{ x: number; y: number }>({ x: 50, y: 50 });
  const [isPointerActive, setIsPointerActive] = useState(false);

  useEffect(() => {
    // Safely check window and matchMedia in browser / testing environments
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return;

    try {
      const mediaQuery = window.matchMedia("(pointer: fine)");
      if (!mediaQuery.matches) return;

      const handlePointerMove = (e: MouseEvent) => {
        const x = (e.clientX / window.innerWidth) * 100;
        const y = (e.clientY / window.innerHeight) * 100;
        setMousePos({ x, y });
        if (!isPointerActive) setIsPointerActive(true);
      };

      window.addEventListener("mousemove", handlePointerMove, { passive: true });
      return () => window.removeEventListener("mousemove", handlePointerMove);
    } catch {
      // Gracefully ignore media query errors
    }
  }, [isPointerActive]);

  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden" aria-hidden="true">
      {/* 1. Spatial Dot Matrix Grid */}
      <div className="absolute inset-0 spatial-grid-bg opacity-70" />

      {/* 2. Top-Right Electric Amber Atmospheric Glow */}
      <div className="absolute -top-32 -right-32 h-[550px] w-[550px] rounded-full bg-[radial-gradient(circle,_rgba(245,158,11,0.12)_0%,_rgba(245,158,11,0.02)_55%,_transparent_75%)] blur-3xl" />

      {/* 3. Bottom-Left Controlled Cyan Atmospheric Glow */}
      <div className="absolute -bottom-32 -left-32 h-[600px] w-[600px] rounded-full bg-[radial-gradient(circle,_rgba(6,182,212,0.1)_0%,_rgba(6,182,212,0.015)_55%,_transparent_75%)] blur-3xl" />

      {/* 4. Center Ambient Field for Subtle Depth Separation */}
      <div className="absolute left-1/2 top-1/3 h-[700px] w-[1000px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(ellipse,_rgba(255,255,255,0.02)_0%,_transparent_70%)] blur-2xl" />

      {/* 5. Interactive Cursor Spotlight */}
      {isPointerActive && (
        <div
          className="absolute h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-60 transition-opacity duration-500"
          style={{
            left: `${mousePos.x}%`,
            top: `${mousePos.y}%`,
            background:
              "radial-gradient(circle, rgba(245, 158, 11, 0.05) 0%, rgba(6, 182, 212, 0.03) 40%, transparent 70%)",
            filter: "blur(40px)",
            willChange: "left, top",
          }}
        />
      )}
    </div>
  );
});

SpatialBackground.displayName = "SpatialBackground";
