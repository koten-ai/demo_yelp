import { useState } from "react";
import BusinessCard from "../components/results/BusinessCard";
import { ErrorBanner, LoadingBlock } from "../components/common/States";
import { search } from "../api/client";
import { useSearchLoadingLabel } from "../lib/useCorpus";
import { normalizeBusiness, summaryFromResponse } from "../lib/normalize";
import { renderSimpleMarkdown } from "../lib/simpleMarkdown";
import { appendTrace } from "../lib/trace";
import { clearSession, getChatId, saveLastSearch, setChatId } from "../state/session";
import type { BusinessCard as Card } from "../api/types";

type Turn = {
  role: "user" | "assistant";
  text: string;
  results?: Card[];
};

export default function ConversationalSearchPage() {
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const loadingLabel = useSearchLoadingLabel("Querying");

  async function send() {
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    setTurns((t) => [...t, { role: "user", text: q }]);
    setLoading(true);
    setError("");
    try {
      const data = await search(q, getChatId(), { aiProcessResult: true });
      appendTrace(q, data);
      const answer = summaryFromResponse(data.answer, data.structured_answer);
      setChatId(data.chat_id);
      saveLastSearch({
        query: q,
        answer,
        results: data.results,
        chatId: data.chat_id,
      });
      setTurns((t) => [
        ...t,
        { role: "assistant", text: answer || "(no summary)", results: data.results },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  function newSearch() {
    clearSession();
    setTurns([]);
    setError("");
  }

  return (
    <div className="mx-auto max-w-3xl px-4 md:px-10 py-6 flex flex-col min-h-[calc(100vh-8rem)]">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold">How can I help you discover today?</h1>
          <p className="text-sm text-on-surface-variant">Multi-turn search over yelp-demo</p>
        </div>
        <button
          type="button"
          onClick={newSearch}
          className="text-sm px-3 py-1.5 rounded-lg border border-outline-variant hover:bg-surface-container-low"
        >
          New Search
        </button>
      </div>

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onDismiss={() => setError("")} />
        </div>
      )}

      <div className="flex-1 space-y-6 overflow-y-auto pb-4">
        {turns.length === 0 && (
          <div className="glass rounded-2xl p-6 text-on-surface-variant text-sm">
            Try: “quiet coffee shops open now” then “which are good for laptop work?”
          </div>
        )}
        {turns.map((t, i) => (
          <div key={i} className={t.role === "user" ? "flex justify-end" : ""}>
            <div
              className={`max-w-[90%] rounded-2xl px-4 py-3 ${
                t.role === "user"
                  ? "bg-primary text-on-primary"
                  : "bg-surface-container-lowest border border-outline-variant/40"
              }`}
            >
              {t.role === "assistant" ? (
                <div className="text-sm">{renderSimpleMarkdown(t.text)}</div>
              ) : (
                <p className="text-sm whitespace-pre-wrap">{t.text}</p>
              )}
              {t.results && t.results.length > 0 && (
                <div className="mt-3 space-y-2">
                  {t.results.slice(0, 5).map((r, idx) => (
                    <BusinessCard
                      key={(r.business_id || r.name) + idx}
                      business={normalizeBusiness(r, idx)}
                      compact
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && <LoadingBlock label={loadingLabel} />}
      </div>

      <form
        className="sticky bottom-16 md:bottom-4 mt-auto flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <label className="sr-only" htmlFor="chat-input">
          Message
        </label>
        <input
          id="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
          placeholder="Ask about local places…"
          className="flex-1 h-12 rounded-xl border border-outline-variant px-4 bg-surface-container-lowest focus:outline-none focus:ring-2 focus:ring-primary"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="h-12 px-5 rounded-xl ai-gradient text-white font-semibold disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
