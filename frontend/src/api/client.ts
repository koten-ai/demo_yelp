import type { HealthResponse, InsightResponse, SearchResponse } from "./types";

async function parseJson(res: Response) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok || (data && data.error)) {
    throw new Error((data && data.error) || res.statusText || "Request failed");
  }
  return data;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch("/api/health");
  return parseJson(res) as Promise<HealthResponse>;
}

export type SearchOptions = {
  /** Hub-style insight after Zeus tools. Ask AI = true; landing/results = false. */
  aiProcessResult?: boolean;
};

export async function search(
  query: string,
  chatId?: string | null,
  options?: SearchOptions
): Promise<SearchResponse> {
  const res = await fetch("/api/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      chat_id: chatId || undefined,
      // Default cheap path for search UI; Ask AI opts into insight.
      ai_process_result: options?.aiProcessResult ?? false,
    }),
  });
  return parseJson(res) as Promise<SearchResponse>;
}

export async function fetchToolOrder(): Promise<{ v1: string[]; v2: string[] }> {
  const res = await fetch("/api/tool-order");
  return parseJson(res);
}

export async function fetchBusiness(
  businessId: string,
  chatId?: string | null
) {
  const q = chatId ? `?chat_id=${encodeURIComponent(chatId)}` : "";
  const res = await fetch(`/api/business/${encodeURIComponent(businessId)}${q}`);
  return parseJson(res);
}

export async function fetchInsight(
  businessId: string,
  chatId?: string | null
): Promise<InsightResponse> {
  const res = await fetch(
    `/api/business/${encodeURIComponent(businessId)}/insight`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: chatId || undefined }),
    }
  );
  return parseJson(res) as Promise<InsightResponse>;
}
