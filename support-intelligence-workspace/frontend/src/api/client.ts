export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(message: string, status: number, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

const BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ?? "";

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!res.ok) {
    let detail: unknown = null;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    const message = extractErrorMessage(detail, res.status);
    throw new ApiError(message, res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
};

function extractErrorMessage(detail: unknown, status: number): string {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (detail && typeof detail === "object") {
    const d = detail as Record<string, unknown>;
    if (typeof d.detail === "string" && d.detail.trim()) return d.detail;
    if (d.detail && typeof d.detail === "object") {
      const inner = d.detail as Record<string, unknown>;
      if (typeof inner.message === "string" && inner.message.trim()) {
        return inner.message;
      }
      if (typeof inner.code === "string" && typeof inner.message === "string") {
        return `${inner.code}: ${inner.message}`;
      }
    }
    if (typeof d.message === "string" && d.message.trim()) return d.message;
  }
  return `Request failed (${status})`;
}
