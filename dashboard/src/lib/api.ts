/**
 * API client for the FROGÉ HQ backend.
 * All URLs are RELATIVE. No hardcoded localhost anywhere.
 */

export interface AuthConfig {
  auth_required: boolean;
  signup_enabled?: boolean;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  email: string;
  account?: { email: string; name: string; role: string };
}

const TOKEN_KEY = "froge_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(path, { ...init, headers });
  if (res.status === 401) {
    setToken(null);
    throw new ApiError(401, "unauthorized");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* non-json error body */
    }
    throw new ApiError(res.status, String(detail));
  }
  return (await res.json()) as T;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export const api = {
  authConfig: () => request<AuthConfig>("/api/auth/config"),
  login: (email: string, password: string) =>
    request<AuthToken>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  signup: (email: string, password: string, name = "") =>
    request<AuthToken>("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    }),

  employees: () => request<any[]>("/api/employees"),
  approvals: (state?: string) =>
    request<any[]>(`/api/approvals${state ? `?state=${state}` : ""}`),
  resolveApproval: (id: string, state: "APPROVED" | "DENIED") =>
    request<any>(`/api/approvals/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify({ state, resolver: "user" }),
    }),
  createMission: (goal: string) =>
    request<any>("/api/missions", {
      method: "POST",
      body: JSON.stringify({ goal }),
    }),
  callBoardroom: (topic: string, participants?: string[]) =>
    request<any>("/api/boardroom", {
      method: "POST",
      body: JSON.stringify({ topic, participants }),
    }),
  monitoring: () => request<any>("/api/monitoring"),
};
