import type {
  HealthResponse,
  InsightResponse,
  ReviewsResponse,
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
  /** Abort in-flight search (Ask AI Stop). */
  signal?: AbortSignal;
};

/** True when fetch/search was cancelled via AbortController. */
export function isAbortError(e: unknown): boolean {
  if (!e || typeof e !== "object") return false;
  const name = (e as { name?: string }).name;
  return name === "AbortError";
}

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
    signal: options?.signal,
  });
  return parseJson(res) as Promise<SearchResponse>;
}

export async function fetchToolOrder(): Promise<{ v1: string[]; v2: string[] }> {
  const res = await fetch("/api/tool-order");
  return parseJson(res);
}

/**
 * Business card fetch via direct Zeus V2 find (no LLM). Does not take
 * discovery chat_id — backend never binds landing/results multi-turn history.
 */
export async function fetchBusiness(businessId: string) {
  const res = await fetch(`/api/business/${encodeURIComponent(businessId)}`);
  return parseJson(res);
}

/**
 * Individual reviews via direct Zeus V2 find (no LLM). Soft-fails empty.
 */
export async function fetchReviews(
  businessId: string,
  limit = 20
): Promise<ReviewsResponse> {
  const empty: ReviewsResponse = {
    business_id: businessId,
    reviews: [],
    count: 0,
    source: "none",
    ai_process_result: false,
  };
  try {
    const qs = new URLSearchParams({
      limit: String(Math.max(1, Math.min(limit, 50))),
    });
    const res = await fetch(
      `/api/business/${encodeURIComponent(businessId)}/reviews?${qs}`
    );
    const data = (await res.json().catch(() => ({}))) as ReviewsResponse;
    if (!res.ok) {
      return {
        ...empty,
        source: "error",
        error: (data && data.error) || res.statusText,
      };
    }
    return {
      business_id: data.business_id || businessId,
      reviews: Array.isArray(data.reviews) ? data.reviews : [],
      count:
        typeof data.count === "number"
          ? data.count
          : Array.isArray(data.reviews)
            ? data.reviews.length
            : 0,
      source: data.source || "empty",
      sources: data.sources,
      req_id: data.req_id,
      ai_process_result: false,
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

/**
 * AI review insight. Always an isolated Zeus session (no discovery chat_id).
 * Returned chat_id is ephemeral — do not write it into localStorage discovery session.
 * Review rows are also filled server-side via the verb path; prefer fetchReviews
 * for the Recent Reviews list so the UI does not wait on the agent.
 */
export async function fetchInsight(businessId: string): Promise<InsightResponse> {
  const res = await fetch(
    `/api/business/${encodeURIComponent(businessId)}/insight`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    }
  );
  return parseJson(res) as Promise<InsightResponse>;
}
