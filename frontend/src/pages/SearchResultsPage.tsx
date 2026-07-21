import { useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import SearchBar from "../components/search/SearchBar";
import FilterChips, { filterBusinesses } from "../components/search/FilterChips";
import BusinessCard from "../components/results/BusinessCard";
import AreaSummary from "../components/results/AreaSummary";
import ResultsMap from "../components/map/ResultsMap";
import { EmptyState, ErrorBanner, LoadingBlock } from "../components/common/States";
import { search } from "../api/client";
import { normalizeBusiness, summaryFromResponse } from "../lib/normalize";
import { appendTrace } from "../lib/trace";
import { getChatId, loadLastSearch, saveLastSearch } from "../state/session";
import type { BusinessCard as Card } from "../api/types";

type LocState = {
  query?: string;
  answer?: string;
  results?: Card[];
  chatId?: string;
};

export default function SearchResultsPage() {
  const loc = useLocation();
  const state = (loc.state || {}) as LocState;
  const cached = loadLastSearch();

  const initialResults = (state.results || (cached?.results as Card[]) || []) as Card[];
  const [query, setQuery] = useState(state.query || cached?.query || "");
  const [answer, setAnswer] = useState(state.answer || cached?.answer || "");
  const [results, setResults] = useState(initialResults);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [openOnly, setOpenOnly] = useState(false);
  const [price, setPrice] = useState<string | null>(null);
  const [category, setCategory] = useState("");

  const ui = useMemo(
    () => results.map((r, i) => normalizeBusiness(r, i)),
    [results]
  );

  const catOptions = useMemo(() => {
    const set = new Set<string>();
    ui.forEach((b) => {
      b.categories
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean)
        .forEach((c) => set.add(c));
    });
    return Array.from(set).slice(0, 12);
  }, [ui]);

  const filtered = filterBusinesses(ui, { openOnly, price, category });

  async function run() {
    const q = query.trim();
    if (!q) return;
    setLoading(true);
    setError("");
    try {
      const data = await search(q, getChatId() || state.chatId || cached?.chatId);
      appendTrace(q, data);
      const ans = summaryFromResponse(data.answer, data.structured_answer);
      setAnswer(ans);
      setResults(data.results || []);
      saveLastSearch({
        query: q,
        answer: ans,
        results: data.results,
        chatId: data.chat_id,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-[1280px] px-4 md:px-10 py-6 md:py-8">
      <div className="flex flex-col md:flex-row md:items-center gap-4 justify-between">
        <h1 className="text-2xl font-bold">Explore</h1>
        <SearchBar value={query} onChange={setQuery} onSubmit={run} loading={loading} />
      </div>

      <div className="mt-4">
        <FilterChips
          openOnly={openOnly}
          setOpenOnly={setOpenOnly}
          price={price}
          setPrice={setPrice}
          category={category}
          setCategory={setCategory}
          categories={catOptions}
        />
      </div>

      {error && (
        <div className="mt-4">
          <ErrorBanner message={error} onDismiss={() => setError("")} />
        </div>
      )}

      {loading && <LoadingBlock />}

      {!loading && answer && (
        <div className="mt-6">
          <AreaSummary text={answer} />
        </div>
      )}

      <div className="mt-6 grid lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 space-y-4">
          {!loading && filtered.length === 0 ? (
            <EmptyState
              title="No businesses to show"
              body="Try a new natural-language query or clear filters."
            />
          ) : (
            filtered.map((b) => <BusinessCard key={b.id} business={b} compact />)
          )}
        </div>
        <div className="lg:col-span-5 lg:sticky lg:top-24 h-[420px]">
          <ResultsMap items={filtered} />
        </div>
      </div>
    </div>
  );
}
