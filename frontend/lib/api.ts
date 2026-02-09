// In dev, use "" so fetch("/api/...") hits same origin and Next.js rewrites to backend (no CORS issues).
// When NEXT_PUBLIC_API_URL is set (e.g. production), use it.
const API_URL =
  process.env.NEXT_PUBLIC_API_URL !== undefined && process.env.NEXT_PUBLIC_API_URL !== ""
    ? process.env.NEXT_PUBLIC_API_URL
    : process.env.NODE_ENV === "development"
      ? ""
      : "http://localhost:8000";

/** Timeout for list/initial loads so dropdown doesn't hang forever if backend is unreachable */
const LIST_FETCH_TIMEOUT_MS = 15000;

export type Stock = { isin: string; name: string; symbol: string | null };
export type Session = { id: number; isin: string; title: string | null; created_at: string | null };

const USER_FACING_NETWORK_ERROR = "Could not reach the server. Please try again later.";

async function fetchWithTimeout(url: string, ms: number = LIST_FETCH_TIMEOUT_MS): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), ms);
  try {
    const r = await fetch(url, { signal: controller.signal }).catch((e) => {
      const baseUrl = url.split("/api")[0];
      if (e?.name === "AbortError") {
        console.warn("Request timed out. Is the backend running at", baseUrl + "? Ensure the backend is running (e.g. uv run uvicorn main:app --reload in backend/) and NEXT_PUBLIC_API_URL points to it.");
        throw new Error(USER_FACING_NETWORK_ERROR);
      }
      if (e instanceof TypeError && e.message === "Failed to fetch") {
        console.warn("Network error: backend unreachable at", baseUrl + ". Ensure the backend is running (e.g. uv run uvicorn main:app --reload in backend/) and NEXT_PUBLIC_API_URL points to it.");
        throw new Error(USER_FACING_NETWORK_ERROR);
      }
      throw e;
    });
    return r;
  } finally {
    clearTimeout(id);
  }
}

export async function fetchStocks(): Promise<Stock[]> {
  const r = await fetchWithTimeout(`${API_URL}/api/stocks`);
  if (!r.ok) throw new Error(await getErrorDetail(r));
  const data = await r.json();
  if (!Array.isArray(data)) throw new Error("Stocks response was not an array.");
  return data;
}

const DATA_UNAVAILABLE_MESSAGE =
  "Data temporarily unavailable. Some metrics or series could not be loaded. Please try again later.";

const PROVIDER_PHRASES = ["rate limit", "api key", "alphavantage", "premium"];

function sanitizeErrorDetail(detail: string): string {
  const lower = detail.toLowerCase();
  if (PROVIDER_PHRASES.some((p) => lower.includes(p))) return DATA_UNAVAILABLE_MESSAGE;
  return detail;
}

async function getErrorDetail(r: Response): Promise<string> {
  try {
    const body = await r.json();
    if (body && typeof body.detail === "string") return sanitizeErrorDetail(body.detail);
    if (body && Array.isArray(body.detail)) {
      const joined = body.detail.map((x: unknown) => String(x)).join(" ");
      return sanitizeErrorDetail(joined);
    }
  } catch {
    // ignore
  }
  return r.statusText || "Request failed";
}

async function fetchWithError(url: string): Promise<Response> {
  const r = await fetch(url).catch((e) => {
    if (e instanceof TypeError && e.message === "Failed to fetch")
      throw new Error("Network error: server unreachable. Check backend is running and URL.");
    throw e;
  });
  return r;
}

export type SeriesPoint = { time: string; open?: number; high?: number; low?: number; close?: number; volume?: number };
export type ForecastPoint = { time: string; close: number };
export type TrendPoint = { time: string; value: number };

export type SeriesResponse = {
  series: SeriesPoint[];
  forecast?: ForecastPoint[];
  trend_line?: TrendPoint[];
  upper_band?: TrendPoint[];
  lower_band?: TrendPoint[];
  forecast_stats?: { slope?: number; intercept?: number; std?: number; last_date?: string };
};

export async function fetchSeries(isin: string, interval: string, includeForecast = false): Promise<SeriesResponse> {
  const params = new URLSearchParams({ interval });
  if (includeForecast) params.set("include_forecast", "true");
  const r = await fetchWithError(`${API_URL}/api/stocks/${encodeURIComponent(isin)}/series?${params}`);
  if (!r.ok) throw new Error(await getErrorDetail(r));
  return r.json();
}

export async function fetchMetrics(isin: string): Promise<Record<string, unknown>> {
  const r = await fetchWithError(`${API_URL}/api/stocks/${encodeURIComponent(isin)}/metrics`);
  if (!r.ok) throw new Error(await getErrorDetail(r));
  return r.json();
}

export async function fetchSessions(): Promise<Session[]> {
  const r = await fetchWithTimeout(`${API_URL}/api/sessions`, LIST_FETCH_TIMEOUT_MS);
  if (!r.ok) throw new Error(await getErrorDetail(r));
  const data = await r.json();
  if (!Array.isArray(data)) return [];
  return data;
}

export async function fetchSession(sessionId: number) {
  const r = await fetchWithError(`${API_URL}/api/sessions/${sessionId}`);
  if (!r.ok) throw new Error(await getErrorDetail(r));
  return r.json();
}

export function adviceStreamUrl(isin: string): string {
  return `${API_URL}/api/stocks/${encodeURIComponent(isin)}/advice`;
}

export async function sendChatMessage(sessionId: number, message: string): Promise<Response> {
  return fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
}
