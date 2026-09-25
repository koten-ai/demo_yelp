import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import BusinessCard from "../components/results/BusinessCard";
import { ErrorBanner } from "../components/common/States";
import { isAbortError, search } from "../api/client";
import { normalizeBusiness, summaryFromResponse } from "../lib/normalize";
import { renderSimpleMarkdown } from "../lib/simpleMarkdown";
import { clearSession, getChatId, saveLastSearch, setChatId } from "../state/session";
import type { BusinessCard as Card } from "../api/types";

type Turn = {
  role: "user" | "assistant" | "system";
  text: string;
  results?: Card[];
  /** Captured at send time — keeps historical turns stable if the toggle flips. */
  summarize?: boolean;
};

type ChatLocState = {
  /** Prefill composer (business detail “Ask AI about this place”). */
  seedQuery?: string;
  /** When true with seedQuery, send immediately. */
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
  /** On = short written summary plus cards. Off = matching places only. */
  const [includeSummary, setIncludeSummary] = useState(true);
  const abortRef = useRef<AbortController | null>(null);
  /** Bumped to ignore stale completions after New Search / superseded sends. */
  const requestGenRef = useRef(0);
  const seedAppliedRef = useRef(false);
  const includeSummaryRef = useRef(includeSummary);
  includeSummaryRef.current = includeSummary;

  const sendQuery = useCallback(async (raw: string) => {
    const q = raw.trim();
    if (!q) return;
    if (abortRef.current) return;

    const summarize = includeSummaryRef.current;

    setInput("");
    setTurns((t) => [...t, { role: "user", text: q }]);
    setLoading(true);
    setError("");

    const controller = new AbortController();
    abortRef.current = controller;
    const gen = ++requestGenRef.current;

    try {
      const data = await search(q, getChatId(), {
        summarize,
        signal: controller.signal,
      });
      if (gen !== requestGenRef.current) return;
      const results = Array.isArray(data.results) ? data.results : [];
      const answer = summarize
        ? summaryFromResponse(data.answer, data.structured_answer)
        : "";
      setChatId(data.chat_id);
      saveLastSearch({
        query: q,
        answer: answer || (summarize ? "" : `${results.length} place(s)`),
        results,
        chatId: data.chat_id,
      });
      setTurns((t) => [
        ...t,
        {
          role: "assistant",
          text: summarize ? answer || "(no summary)" : "",
          results,
          summarize,
        },
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

  useEffect(() => {
    if (!seedQuery || seedAppliedRef.current) return;
    seedAppliedRef.current = true;

    if (autoSend) {
      nav("/chat", {
        replace: true,
        state: { seedQuery, autoSend: false },
      });
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
    abortRef.current?.abort();
  }

  function newSearch() {
    requestGenRef.current += 1;
    abortRef.current?.abort();
    abortRef.current = null;
    clearSession();
    setTurns([]);
    setError("");
    setLoading(false);
  }

  const thinkingLabel = includeSummary ? "Thinking" : "Searching";
  const resultLimit = (t: Turn) =>
    t.summarize === false ? Math.min(t.results?.length ?? 0, 20) : 5;

  return (
    <div className="mx-auto max-w-3xl px-4 md:px-10 py-6 flex flex-col min-h-[calc(100vh-8rem)]">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold">How can I help you discover today?</h1>
          <p className="text-sm text-on-surface-variant">Multi-turn search over local places</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 sm:justify-end">
          <div
            className="inline-flex items-center gap-2 text-sm px-3 py-1.5 rounded-lg border border-outline-variant bg-surface-container-lowest select-none"
            title={
              includeSummary
                ? "Write a short summary with the results"
                : "Show matching places only"
            }
          >
            <span id="ai-summary-label" className="text-on-surface-variant whitespace-nowrap">
              AI summary
            </span>
            <button
              type="button"
              role="switch"
              aria-checked={includeSummary}
              aria-labelledby="ai-summary-label"
              disabled={loading}
              onClick={() => setIncludeSummary((v) => !v)}
              className={`relative h-6 w-11 shrink-0 rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:opacity-50 ${
                includeSummary ? "bg-primary" : "bg-outline-variant"
              }`}
            >
              <span
                aria-hidden
                className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                  includeSummary ? "translate-x-5" : "translate-x-0"
                }`}
              />
            </button>
          </div>
          <button
            type="button"
            onClick={newSearch}
            className="text-sm px-3 py-1.5 rounded-lg border border-outline-variant hover:bg-surface-container-low"
          >
            New Search
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onDismiss={() => setError("")} />
        </div>
      )}

      <div className="flex-1 space-y-6 overflow-y-auto pb-4">
        {turns.length === 0 && !loading && (
          <div className="glass rounded-2xl p-6 text-on-surface-variant text-sm">
            Try: “donuts in Tampa” then “which of those are coffee shops?”
            {!includeSummary && (
              <p className="mt-2 text-xs">
                AI summary is off — answers list matching businesses without a written summary.
              </p>
            )}
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
                  t.summarize === false ? (
                    <div className="text-xs font-medium text-on-surface-variant mb-1">
                      {(t.results?.length ?? 0) > 0
                        ? `${t.results!.length} place${t.results!.length === 1 ? "" : "s"}`
                        : "No matching places"}
                    </div>
                  ) : (
                    <div className="text-sm text-on-surface overflow-x-auto">
                      {renderSimpleMarkdown(t.text)}
                    </div>
                  )
                ) : (
                  <p className="text-sm whitespace-pre-wrap">{t.text}</p>
                )}
                {t.results && t.results.length > 0 && (
                  <div className={`space-y-2 ${t.summarize === false ? "mt-1" : "mt-3"}`}>
                    {t.results.slice(0, resultLimit(t)).map((r, idx) => (
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
          <div className="w-full" role="status" aria-live="polite" aria-label={thinkingLabel}>
            <div className="w-full max-w-full rounded-2xl border border-outline-variant/40 bg-surface-container-lowest px-4 py-3">
              <p className="text-sm text-on-surface-variant">
                <span className="thinking-dots">{thinkingLabel}</span>
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
