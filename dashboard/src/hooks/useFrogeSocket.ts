"use client";

/**
 * Reusable WebSocket hook for FROGÉ HQ.
 * Connects to /ws/events using a RELATIVE URL derived from the page origin
 * (ws:// or wss:// chosen automatically). No hardcoded host.
 */

import { useEffect, useRef, useState, useCallback } from "react";
import type { WsEnvelope } from "@/lib/types";

export type ConnectionStatus = "connecting" | "connected" | "disconnected";

interface Options {
  onEvent: (envelope: WsEnvelope) => void;
  path?: string;
}

function socketUrl(path: string): string {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}${path}`;
}

export function useFrogeSocket({ onEvent, path = "/ws/events" }: Options) {
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const wsRef = useRef<WebSocket | null>(null);
  const attemptRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;

  const scheduleReconnect = useCallback(() => {
    if (timerRef.current) return;
    const attempt = attemptRef.current++;
    const delay = Math.min(1000 * 2 ** attempt, 15000);
    timerRef.current = setTimeout(() => {
      timerRef.current = null;
      connectRef.current();
    }, delay);
  }, []);

  const connect = useCallback(() => {
    if (typeof window === "undefined") return;
    let ws: WebSocket;
    try {
      ws = new WebSocket(socketUrl(path));
    } catch {
      scheduleReconnect();
      return;
    }
    wsRef.current = ws;
    setStatus("connecting");

    ws.onopen = () => {
      attemptRef.current = 0;
      setStatus("connected");
    };
    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data) as WsEnvelope;
        if (data && data.event) onEventRef.current(data);
      } catch {
        /* ignore malformed frames */
      }
    };
    ws.onclose = () => {
      setStatus("disconnected");
      scheduleReconnect();
    };
    ws.onerror = () => {
      ws.close();
    };
  }, [path, scheduleReconnect]);

  const connectRef = useRef(connect);
  connectRef.current = connect;

  useEffect(() => {
    connect();
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((payload: unknown) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload));
    }
  }, []);

  return { status, send };
}
