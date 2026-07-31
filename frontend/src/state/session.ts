/** Discovery multi-turn chat id (landing / Explore / Ask AI). Not detail/insight. */
const CHAT_KEY = "localai.chat_id";
const LAST_RESULTS_KEY = "localai.last_results";
const LAST_ANSWER_KEY = "localai.last_answer";
const LAST_QUERY_KEY = "localai.last_query";

export function getChatId(): string | null {
  return localStorage.getItem(CHAT_KEY);
}

export function setChatId(id: string | null) {
  if (!id) localStorage.removeItem(CHAT_KEY);
  else localStorage.setItem(CHAT_KEY, id);
}

/** Drop discovery chat + last search cache (new search intent / isolation). */
export function clearSession() {
  localStorage.removeItem(CHAT_KEY);
  localStorage.removeItem(LAST_RESULTS_KEY);
  localStorage.removeItem(LAST_ANSWER_KEY);
  localStorage.removeItem(LAST_QUERY_KEY);
}

export function saveLastSearch(payload: {
  query: string;
  answer: string;
  results: unknown[];
  chatId: string;
}) {
  setChatId(payload.chatId);
  localStorage.setItem(LAST_QUERY_KEY, payload.query);
  localStorage.setItem(LAST_ANSWER_KEY, payload.answer);
  localStorage.setItem(LAST_RESULTS_KEY, JSON.stringify(payload.results));
}

export function loadLastSearch(): {
  query: string;
  answer: string;
  results: unknown[];
  chatId: string | null;
} | null {
  const resultsRaw = localStorage.getItem(LAST_RESULTS_KEY);
  if (!resultsRaw) return null;
  try {
    return {
      query: localStorage.getItem(LAST_QUERY_KEY) || "",
      answer: localStorage.getItem(LAST_ANSWER_KEY) || "",
      results: JSON.parse(resultsRaw),
      chatId: getChatId(),
    };
  } catch {
    return null;
  }
}
