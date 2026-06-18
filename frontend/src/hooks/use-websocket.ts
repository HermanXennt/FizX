"use client";

import { useCallback, useEffect, useRef } from "react";
import { buildSocketUrl } from "@/lib/websocket";
import { useAuthStore } from "@/store/auth-store";

/** Generic JSON-over-WebSocket hook with auto-reconnect (capped exponential backoff). */
export function useWebSocket(path: string | null, onMessage: (data: unknown) => void) {
  const token = useAuthStore((s) => s.accessToken);
  const socketRef = useRef<WebSocket | null>(null);
  const onMessageRef = useRef(onMessage);
  const attemptRef = useRef(0);
  const closedByUserRef = useRef(false);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const send = useCallback((data: unknown) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(data));
    }
  }, []);

  useEffect(() => {
    if (!path || !token) return;
    closedByUserRef.current = false;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    const connect = () => {
      if (closedByUserRef.current) return;

      const socket = new WebSocket(buildSocketUrl(path, token));
      socketRef.current = socket;

      socket.onopen = () => {
        attemptRef.current = 0;
      };

      socket.onmessage = (event) => {
        try {
          onMessageRef.current(JSON.parse(event.data));
        } catch {
          // ignore malformed frames
        }
      };

      socket.onclose = (event) => {
        if (closedByUserRef.current || event.code === 4001 || event.code === 4003) return;
        const delay = Math.min(1000 * 2 ** attemptRef.current, 15000);
        attemptRef.current += 1;
        reconnectTimer = setTimeout(connect, delay);
      };
    };

    connect();

    return () => {
      closedByUserRef.current = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      socketRef.current?.close();
    };
  }, [path, token]);

  return { send };
}
