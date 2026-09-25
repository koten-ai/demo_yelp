import catalog from "../data/catalog.json";
import type {
  BusinessCard,
  HealthResponse,
  InsightResponse,
  ReviewItem,
  ReviewsResponse,
  SearchResponse,
  SuggestResponse,
} from "./types";

const BUSINESSES = catalog as BusinessCard[];

const STOP = new Set([
  "a", "an", "the", "for", "with", "and", "or", "to", "of", "in", "near", "on",
  "at", "me", "my", "best", "good", "find", "show", "what", "which", "are", "is",
  "i", "want", "looking", "places", "place", "some", "any", "about", "from", "by",
  "it", "this", "that", "tell", "should", "know", "before", "visiting", "now",
  "those", "them", "these", "spot", "spots", "please", "can", "you", "how",
]);

const AUTHORS: Array<[string, string]> = [
  ["Alex Morgan", "128"],
  ["Jordan Lee", "54"],
  ["Sam Patel", "312"],
  ["Riley Chen", "27"],
  ["Casey Nguyen", "89"],
];

const lastResultsByChat = new Map<string, BusinessCard[]>();

function hash(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (Math.imul(h, 31) + s.charCodeAt(i)) >>> 0;
  return h;
}

function tokens(query: string): string[] {
  return query
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((t) => t.length > 1 && !STOP.has(t));
}

function score(card: BusinessCard, words: string[]): number {
  if (!words.length) return 1;
  const name = (card.name || "").toLowerCase();
  const cats = (card.categories || "").toLowerCase();
  const city = `${card.city || ""} ${card.state || ""}`.toLowerCase();
  const address = (card.address || "").toLowerCase();
  const desc = (card.description || "").toLowerCase();
  let total = 0;
  for (const w of words) {
    if (name.includes(w)) total += 8;
    if (cats.includes(w)) total += 5;
    if (city.includes(w)) total += 6;
    if (address.includes(w)) total += 2;
    if (desc.includes(w)) total += 1;
  }
  return total;
}

function rank(query: string, pool: BusinessCard[], limit: number): BusinessCard[] {
  const words = tokens(query);
  const wantOpen = /\bopen\b/i.test(query);
  return pool
    .map((b) => ({ b, s: score(b, words) }))
    .filter((row) => (words.length ? row.s > 0 : true))
    .filter((row) => (wantOpen ? row.b.is_open !== "false" : true))
    .sort((a, b) => {
      if (b.s !== a.s) return b.s - a.s;
      const ra = Number(a.b.rating || 0);
      const rb = Number(b.b.rating || 0);
      if (rb !== ra) return rb - ra;
      return Number(b.b.review_count || 0) - Number(a.b.review_count || 0);
    })
    .slice(0, limit)
    .map((row) => row.b);
}

function summarize(query: string, results: BusinessCard[]): string {
  if (!results.length) {
    return `No places matched “${query}”. Try a category, a city, or a business name.`;
  }
  const lines = results.slice(0, 5).map((b) => {
    const cat = (b.categories || "").split(",")[0]?.trim() || "Local spot";
    const where = [b.city, b.state].filter(Boolean).join(", ");
    const rating = b.rating ? `${b.rating}★` : "unrated";
    const reviews = b.review_count ? `, ${Number(b.review_count).toLocaleString()} reviews` : "";
    const place = where ? ` in ${where}` : "";
    return `- **${b.name}** — ${cat}${place} (${rating}${reviews})`;
  });
  const noun = results.length === 1 ? "place" : "places";
  return [`**${results.length} ${noun}** match “${query}”.`, "", ...lines].join("\n");
}

function reviewsFor(card: BusinessCard): ReviewItem[] {
  const id = card.business_id || card.name || "biz";
  const h = hash(id);
  const cat = (card.categories || "this place").split(",")[0]?.trim() || "this place";
  const city = card.city || "town";
  const texts = [
    `Came for the ${cat.toLowerCase()} and left impressed. ${card.name} feels looked-after, and the staff were easy to talk to.`,
    `Solid visit in ${city}. ${card.name} matched what I hoped for, especially if you care about ${cat.toLowerCase()}.`,
    `Would come back. ${card.address ? `The spot on ${card.address} was easy to find, and the visit was consistent.` : "The visit was consistent from start to finish."}`,
  ];
  const base = Number(card.rating || 5);
  return texts.map((text, i) => {
    const author = AUTHORS[(h + i) % AUTHORS.length];
    const stars = Math.max(3, Math.min(5, Math.round(base) - (i === 2 && h % 3 === 0 ? 1 : 0)));
    return {
      review_id: `${id}-r${i}`,
      author: author[0],
      stars: String(stars),
      text,
      date: ["Mar 2024", "Nov 2023", "Jun 2024"][i],
      user_review_count: author[1],
    };
  });
}

function insightFor(card: BusinessCard): InsightResponse {
  const cats = (card.categories || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  const primary = cats[0] || "Local business";
  const where = [card.city, card.state].filter(Boolean).join(", ");
  const reviews = reviewsFor(card);
  return {
    business_id: card.business_id || "",
    business: card,
    summary: `${card.name} is a ${primary.toLowerCase()} stop${where ? ` in ${where}` : ""}. It holds a ${card.rating || "strong"} rating across ${card.review_count || "local"} reviews.`,
    the_good: [
      card.rating
        ? `${card.rating}-star rating from ${card.review_count || "local"} reviews`
        : "Well regarded locally",
      `Known for ${primary.toLowerCase()}`,
      where ? `Based in ${where}` : "Convenient local stop",
    ],
    the_bad: [
      "Hours can change — confirm before you visit",
      cats.length > 3
        ? "A broad set of offerings, so call ahead for what you need"
        : "Popular times can mean a short wait",
    ],
    best_for: cats.slice(0, 3).length ? cats.slice(0, 3) : ["A local visit"],
    reviews,
  };
}

function findBusiness(businessId: string): BusinessCard | undefined {
  const id = decodeURIComponent(businessId || "").trim();
  return BUSINESSES.find((b) => b.business_id === id);
}

function delay(ms: number, signal?: AbortSignal): Promise<void> {
  if (signal?.aborted) {
    return Promise.reject(new DOMException("Aborted", "AbortError"));
  }
  return new Promise((resolve, reject) => {
    const t = window.setTimeout(() => {
      signal?.removeEventListener("abort", onAbort);
      resolve();
    }, ms);
    const onAbort = () => {
      window.clearTimeout(t);
      reject(new DOMException("Aborted", "AbortError"));
    };
    signal?.addEventListener("abort", onAbort, { once: true });
  });
}

/** True when a search was cancelled via AbortController. */
export function isAbortError(e: unknown): boolean {
  if (!e || typeof e !== "object") return false;
  return (e as { name?: string }).name === "AbortError";
}

export async function fetchHealth(): Promise<HealthResponse> {
  return {
    ok: true,
    app_version: "0.1.0",
    business_count: BUSINESSES.length,
    corpus_label: "businesses",
    corpus_source: "sample",
  };
}

/** Soft-fail typeahead — empty results on a short query. */
export async function fetchSuggest(query: string, limit = 8): Promise<SuggestResponse> {
  const q = (query || "").trim();
  const empty: SuggestResponse = { query: q, results: [], count: 0, source: "sample" };
  if (q.length < 2) return empty;
  await delay(120);
  const results = rank(q, BUSINESSES, Math.max(1, Math.min(limit, 20)));
  return {
    query: q,
    results,
    count: results.length,
    source: results.length ? "sample" : "empty",
    error: null,
  };
}

export type SearchOptions = {
  /** When true, include a short written summary with the cards. */
  summarize?: boolean;
  signal?: AbortSignal;
};

export async function search(
  query: string,
  chatId?: string | null,
  options?: SearchOptions
): Promise<SearchResponse> {
  const q = query.trim();
  await delay(420, options?.signal);
  const refine =
    Boolean(chatId) &&
    lastResultsByChat.has(chatId || "") &&
    /\b(which|those|them|these|narrow|only)\b/i.test(q);
  const pool = refine ? lastResultsByChat.get(chatId || "") || BUSINESSES : BUSINESSES;
  let results = rank(q, pool, 12);
  if (refine && results.length === 0) results = rank(q, BUSINESSES, 12);
  const id = chatId || `local-${Date.now().toString(36)}`;
  lastResultsByChat.set(id, results);
  const summarizeOn = options?.summarize ?? true;
  return {
    chat_id: id,
    query: q,
    answer: summarizeOn ? summarize(q, results) : "",
    structured_answer: null,
    results,
  };
}

export async function fetchBusiness(businessId: string) {
  await delay(180);
  const business = findBusiness(businessId);
  if (!business) throw new Error("Business not found");
  return { business };
}

export async function fetchReviews(businessId: string, limit = 20): Promise<ReviewsResponse> {
  const empty: ReviewsResponse = {
    business_id: businessId,
    reviews: [],
    count: 0,
    source: "sample",
  };
  try {
    await delay(160);
    const business = findBusiness(businessId);
    if (!business) return { ...empty, source: "empty" };
    const reviews = reviewsFor(business).slice(0, Math.max(1, Math.min(limit, 50)));
    return {
      business_id: business.business_id || businessId,
      reviews,
      count: reviews.length,
      source: "sample",
      error: null,
    };
  } catch (e) {
    return {
      ...empty,
      source: "error",
      error: e instanceof Error ? e.message : String(e),
    };
  }
}

export async function fetchInsight(businessId: string): Promise<InsightResponse> {
  await delay(280);
  const business = findBusiness(businessId);
  if (!business) {
    return {
      business_id: businessId,
      summary: "",
      the_good: [],
      the_bad: [],
      best_for: [],
      reviews: [],
      error: "Business not found",
    };
  }
  return insightFor(business);
}
