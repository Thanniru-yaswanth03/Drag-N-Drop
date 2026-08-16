"use client";

import { useEffect, useRef, useState, useCallback } from "react";

type UseWebSocketOptions = {
  projectId: string | null;
  username: string | null;
  onMessage?: (data: unknown) => void;
};

export function useWebSocket({ projectId, username, onMessage }: UseWebSocketOptions) {
  const [isConnected, setIsConnected] = useState(false);
  const [status, setStatus] = useState<"connected" | "connecting" | "disconnected">("disconnected");
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!projectId || !username) {
      return;
    }

    const envUrl = process.env.NEXT_PUBLIC_API_URL;
    let wsHost = typeof window !== "undefined" ? window.location.host : "";
    let wsProtocol = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:";

    if (envUrl) {
      const cleanEnv = envUrl.replace(/\/$/, "");
      if (cleanEnv.startsWith("https://")) {
        wsProtocol = "wss:";
        wsHost = cleanEnv.replace("https://", "");
      } else if (cleanEnv.startsWith("http://")) {
        wsProtocol = "ws:";
        wsHost = cleanEnv.replace("http://", "");
      }
    } else if (typeof window !== "undefined") {
      if ((window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") && window.location.protocol === "http:") {
        wsHost = "127.0.0.1:8008";
        wsProtocol = "ws:";
      }
 else if (window.location.port !== "8000") {
        wsHost = "drag-n-drop-28p3.onrender.com";
        wsProtocol = "wss:";
      }
    }

    const token = typeof localStorage !== "undefined" ? localStorage.getItem("pm_auth_token") : null;
    const tokenParam = token ? `?token=${encodeURIComponent(token)}` : "";
    const url = `${wsProtocol}//${wsHost}/ws/projects/${encodeURIComponent(projectId)}${tokenParam}`;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setStatus("connected");
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (onMessage) onMessage(payload);
        } catch {
          // Ignore invalid JSON
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        setStatus("disconnected");
      };

      ws.onerror = () => {
        setIsConnected(false);
        setStatus("disconnected");
      };
    } catch {
      // Ignore initial synchronous connection error
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [projectId, username, onMessage]);

  const send = useCallback((data: unknown) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return { isConnected, status, send };
}

