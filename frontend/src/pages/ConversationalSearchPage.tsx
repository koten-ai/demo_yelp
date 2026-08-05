import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import BusinessCard from "../components/results/BusinessCard";
import { ErrorBanner } from "../components/common/States";
import { isAbortError, search } from "../api/client";
import { normalizeBusiness, summaryFromResponse } from "../lib/normalize";
import { renderSimpleMarkdown } from "../lib/simpleMarkdown";
import { appendTrace } from "../lib/trace";
import { clearSession, getChatId, saveLastSearch, setChatId } from "../state/session";
import type { BusinessCard as Card } from "../api/types";

type Turn = {
  role: "user" | "assistant" | "system";
  text: string;
  results?: Card[];
};

type ChatLocState = {
  /** Prefill composer (business detail “Ask AI about this place”). */
  seedQuery?: string;
  /** When true with seedQuery, send immediately (empty Explore failover). */
  autoSend?: boolean;
  fromBusinessId?: string;
};

const CANCELLED_MESSAGE = "You stopped this search.";

export default function ConversationalSearchPage() {
  const loc = useLocation();
  const nav = useNavigate();
  const locState = (loc.state as ChatLocState | null) || null;
  const seedQuery = locState?.seedQuery?.trim() || "";
  const autoSend = Boolean(locState?.autoSend && seedQuery);
  const [input, setInput] = useState(autoSend ? "" : seedQuery);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const abortRef = useRef<AbortController | null>(null);
  /** Bumped to ignore stale completions after New Search / superseded sends. */
  const requestGenRef = useRef(0);
  const seedAppliedRef = useRef(false);

  const sendQuery = useCallback(async (raw: string) => {
    const q = raw.trim();
    if (!q) return;
    // Avoid overlapping sends (auto-send + manual, or double effect).
    if (abortRef.current) return;

    setInput("");
    setTurns((t) => [...t, { role: "user", text: q }]);
    setLoading(true);
    setError("");

    const controller = new AbortController();
    abortRef.current = controller;
    const gen = ++requestGenRef.current;

    try {
      const data = await search(q, getChatId(), {
        aiProcessResult: true,
        signal: controller.signal,
      });
      if (gen !== requestGenRef.current) return;
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
      if (gen !== requestGenRef.current) return;
      if (isAbortError(e) || controller.signal.aborted) {
        setTurns((t) => [...t, { role: "system", text: CANCELLED_MESSAGE }]);
        return;
      }
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      if (gen === requestGenRef.current) {
        abortRef.current = null;
        setLoading(false);
      }
    }
  }, []);

  // Prefill from business-detail, or auto-send from empty Explore failover.
  useEffect(() => {
    if (!seedQuery || seedAppliedRef.current) return;
    seedAppliedRef.current = true;

    if (autoSend) {
      // Drop autoSend from history so back/remount does not re-fire.
      nav("/chat", { replace: true, state: { seedQuery, autoSend: false } });
      void sendQuery(seedQuery);
      return;
    }

    setInput(seedQuery);
  }, [seedQuery, autoSend, nav, sendQuery]);

  async function send() {
    if (loading) return;
    await sendQuery(input);
  }

  function stopSearch() {
    if (!loading) return;
    // Keep requestGen so the in-flight catch can append the cancelled chat turn.
    abortRef.current?.abort();
  }

  function newSearch() {
    // Invalidate in-flight work so abort does not add a cancelled turn after clear.
    requestGenRef.current += 1;
    abortRef.current?.abort();
    abortRef.current = null;
    clearSession();
    setTurns([]);
    setError("");
    setLoading(false);
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
        {turns.length === 0 && !loading && (
          <div className="glass rounded-2xl p-6 text-on-surface-variant text-sm">
            Try: “quiet coffee shops open now” then “which are good for laptop work?”
          </div>
        )}
        {turns.map((t, i) =>
          t.role === "system" ? (
            <div key={i} className="flex justify-center" role="status">
              <div className="inline-flex items-center gap-2 rounded-full border border-outline-variant/50 bg-surface-container-low px-3 py-1.5 text-xs text-on-surface-variant">
                <span className="material-symbols-outlined text-base" aria-hidden>
                  stop_circle
                </span>
                <span>{t.text}</span>
              </div>
            </div>
          ) : (
            <div key={i} className={t.role === "user" ? "flex justify-end" : "w-full"}>
              <div
                className={`rounded-2xl px-4 py-3 ${
                  t.role === "user"
                    ? "max-w-[90%] bg-primary text-on-primary"
                    : "w-full max-w-full bg-surface-container-lowest border border-outline-variant/40"
                }`}
              >
                {t.role === "assistant" ? (
                  <div className="text-sm text-on-surface overflow-x-auto">
                    {renderSimpleMarkdown(t.text)}
                  </div>
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
          )
        )}
        {loading && (
          <div className="w-full" role="status" aria-live="polite" aria-label="Thinking with Zeus">
            <div className="w-full max-w-full rounded-2xl border border-outline-variant/40 bg-surface-container-lowest px-4 py-3">
              <p className="text-sm text-on-surface-variant">
                <span className="thinking-dots">Thinking with Zeus</span>
              </p>
            </div>
          </div>
        )}
      </div>

      <form
        className="sticky bottom-16 md:bottom-4 mt-auto flex gap-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (loading) {
            stopSearch();
            return;
          }
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
        {loading ? (
          <button
            type="button"
            onClick={stopSearch}
            className="h-12 px-5 rounded-xl border border-error/40 bg-error-container text-error font-semibold inline-flex items-center gap-1.5"
            aria-label="Stop search"
          >
            <span className="material-symbols-outlined text-base" aria-hidden>
              stop
            </span>
          </button>
        ) : (
          <button
            type="submit"
            disabled={!input.trim()}
            className="h-12 px-5 rounded-xl ai-gradient text-white font-semibold disabled:opacity-50"
          >
            Send
          </button>
        )}
      </form>
    </div>
  );
}
