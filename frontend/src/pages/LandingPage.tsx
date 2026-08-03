import { useState } from "react";
import { useNavigate } from "react-router-dom";
import SearchBar from "../components/search/SearchBar";
import TypingSuggestionChip from "../components/search/TypingSuggestionChip";
import BusinessCard from "../components/results/BusinessCard";
import { EmptyState, ErrorBanner, LoadingBlock } from "../components/common/States";
import { search } from "../api/client";
import { useSearchLoadingLabel } from "../lib/useCorpus";
import { normalizeBusiness, summaryFromResponse } from "../lib/normalize";
import { appendTrace } from "../lib/trace";
import { clearSession, loadLastSearch, saveLastSearch } from "../state/session";
import type { BusinessCard as Card, UiBusiness } from "../api/types";

export default function LandingPage() {
  const nav = useNavigate();
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  /** Last query that returned zero business cards — drives Ask AI failover CTA. */
  const [emptyQuery, setEmptyQuery] = useState("");
  const loadingLabel = useSearchLoadingLabel("Searching");
  const last = loadLastSearch();
  const recommended: UiBusiness[] =
    (last?.results as Card[] | undefined)
      ?.slice(0, 3)
      .map((c, i) => normalizeBusiness(c, i)) || [];

  function openSuggestion(card: Card) {
    const id = (card.business_id || card.name || "").trim();
    if (!id) return;
    nav(`/business/${encodeURIComponent(id)}`, { state: { business: card } });
  }

  function tryAskAi(query: string) {
    const trimmed = query.trim();
    if (!trimmed) return;
    nav("/chat", { state: { seedQuery: trimmed, autoSend: true } });
  }

  async function run() {
    const query = q.trim();
    if (!query) return;
    setLoading(true);
    setError("");
    setEmptyQuery("");
    try {
      // Home search is always a new discovery turn — never reuse a prior
      // chat_id/zeus session (those can carry poisoned tool-failure history).
      clearSession();
      const data = await search(query, null);
      appendTrace(query, data);
      const answer = summaryFromResponse(data.answer, data.structured_answer);
      saveLastSearch({
        query,
        answer,
        results: data.results,
        chatId: data.chat_id,
      });
      const results = data.results || [];
      // Empty card set → stay on home with Ask AI failover (skip empty Explore).
      if (results.length === 0) {
        setEmptyQuery(query);
        return;
      }
      nav("/search", {
        state: {
          query,
          answer,
          results,
          chatId: data.chat_id,
        },
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <section className="relative overflow-visible">
        <div className="pointer-events-none absolute inset-0 ai-gradient opacity-[0.08]" aria-hidden />
        <div className="relative mx-auto max-w-[1280px] px-4 md:px-10 py-16 md:py-24 text-center">
          <p className="inline-flex items-center gap-1 text-xs font-mono uppercase tracking-widest text-primary mb-4">
            <span className="material-symbols-outlined text-[16px]">auto_awesome</span>
            AI-Powered Discovery
          </p>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-on-surface max-w-3xl mx-auto">
            Find your next favorite spot with AI
          </h1>
          <p className="mt-4 text-on-surface-variant max-w-xl mx-auto">
            Natural language search over the yelp-demo knowledge graph via Zeus.
          </p>
          {/* z-40: suggest list above feature strip / mobile nav (z-30) */}
          <div className="relative z-40 mt-8 flex flex-col items-center gap-4 w-full">
            <div className="flex justify-center w-full">
              <SearchBar
                value={q}
                onChange={(v) => {
                  setQ(v);
                  if (emptyQuery) setEmptyQuery("");
                }}
                onSubmit={run}
                loading={loading}
                large
                enableSuggest
                onSelectSuggestion={openSuggestion}
                placeholder="Describe what you need, or attach an image..."
              />
            </div>
            {!loading && <TypingSuggestionChip onSelect={setQ} />}
            {loading && <LoadingBlock label={loadingLabel} />}
          </div>
          {error && (
            <div className="mt-6 max-w-xl mx-auto text-left">
              <ErrorBanner message={error} onDismiss={() => setError("")} />
            </div>
          )}
          {!loading && emptyQuery && (
            <div className="mt-6 max-w-xl mx-auto">
              <EmptyState
                title="No business found"
                body="Quick search didn’t match a place. Ask AI can dig deeper with conversational insight."
                action={
                  <button
                    type="button"
                    onClick={() => tryAskAi(emptyQuery)}
                    className="inline-flex items-center gap-2 rounded-xl ai-gradient px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:opacity-95 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                  >
                    <span className="material-symbols-outlined text-base" aria-hidden>
                      auto_awesome
                    </span>
                    No business found. Try Ask AI?
                  </button>
                }
              />
            </div>
          )}
        </div>
      </section>

      {recommended.length > 0 && (
        <section className="mx-auto max-w-[1280px] px-4 md:px-10 pb-16">
          <div className="flex items-center gap-2 mb-4">
            <span className="material-symbols-outlined text-primary">auto_awesome</span>
            <h2 className="text-xl font-bold">AI Recommended for You</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-4">
            {recommended.map((b) => (
              <BusinessCard key={b.id} business={b} />
            ))}
          </div>
        </section>
      )}

      <section className="border-t border-outline-variant/30 bg-surface-container-low/50">
        <div className="mx-auto max-w-[1280px] px-4 md:px-10 py-14 grid md:grid-cols-3 gap-8">
          {[
            ["Natural Language", "Describe the vibe, not just keywords."],
            ["Smart Summaries", "AI explains why each place fits."],
            ["Zeus-backed", "Real yelp-demo data through the agent loop."],
          ].map(([t, d]) => (
            <div key={t}>
              <h3 className="font-semibold text-on-surface">{t}</h3>
              <p className="mt-2 text-sm text-on-surface-variant">{d}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
