import type {
  HealthResponse,
  InsightResponse,
  SearchResponse,
  SuggestResponse,
} from "./types";

async function parseJson(res: Response) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok || (data && data.error)) {
    throw new Error((data && data.error) || res.statusText || "Request failed");
  }
  return data;
}

/** Soft-fail typeahead — empty results on error so the combobox stays quiet. */
export async function fetchSuggest(
  query: string,
  limit = 8
): Promise<SuggestResponse> {
  const q = (query || "").trim();
  const empty: SuggestResponse = {
    query: q,
    results: [],
    count: 0,
    source: "none",
    fast_tier: true,
    ai_process_result: false,
  };
  if (q.length < 2) return empty;
  try {
    const params = new URLSearchParams({
      q,
      limit: String(Math.max(1, Math.min(limit, 20))),
    });
    const res = await fetch(`/api/suggest?${params}`);
    const data = (await res.json().catch(() => ({}))) as SuggestResponse;
    if (!res.ok) {
      return {
        ...empty,
        source: "error",
        error: (data && (data as { error?: string }).error) || res.statusText,
      };
    }
    return {
      query: data.query ?? q,
      results: Array.isArray(data.results) ? data.results : [],
      count: typeof data.count === "number" ? data.count : (data.results || []).length,
      source: data.source || "empty",
      sources: data.sources,
      fast_tier: data.fast_tier ?? true,
      ai_process_result: false,
      target: data.target,
      error: data.error ?? null,
    };
  } catch (e) {
    return {
      ...empty,
      source: "error",
      error: e instanceof Error ? e.message : String(e),
    };
  }
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
