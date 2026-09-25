import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import { fetchSuggest } from "../../api/client";
import type { BusinessCard, SuggestResponse } from "../../api/types";

const DEBOUNCE_MS = 280;
const MIN_Q = 2;

type Props = {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  loading?: boolean;
  placeholder?: string;
  large?: boolean;
  /** Optional typeahead against the local catalog. */
  enableSuggest?: boolean;
  /** Click / Enter on a highlighted suggestion row */
  onSelectSuggestion?: (card: BusinessCard) => void;
};

export default function SearchBar({
  value,
  onChange,
  onSubmit,
  loading,
  placeholder = "Find coffee, dinner, parks…",
  large,
  enableSuggest = false,
  onSelectSuggestion,
}: Props) {
  const listId = useId();
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const seqRef = useRef(0);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [suggestLoading, setSuggestLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<BusinessCard[]>([]);

  useEffect(() => {
    if (!enableSuggest) {
      setSuggestions([]);
      setOpen(false);
      setActive(-1);
      return;
    }
    const q = value.trim();
    if (q.length < MIN_Q || loading) {
      setSuggestions([]);
      setOpen(false);
      setActive(-1);
      setSuggestLoading(false);
      return;
    }

    const seq = ++seqRef.current;
    setSuggestLoading(true);
    const t = window.setTimeout(() => {
      void fetchSuggest(q, 8)
        .then((data: SuggestResponse) => {
          if (seq !== seqRef.current) return;
          const rows = Array.isArray(data.results) ? data.results : [];
          setSuggestions(rows);
          setOpen(rows.length > 0);
          setActive(rows.length ? 0 : -1);
        })
        .catch(() => {
          if (seq !== seqRef.current) return;
          setSuggestions([]);
          setOpen(false);
          setActive(-1);
        })
        .finally(() => {
          if (seq === seqRef.current) setSuggestLoading(false);
        });
    }, DEBOUNCE_MS);

    return () => {
      window.clearTimeout(t);
    };
  }, [value, enableSuggest, loading]);

  useEffect(() => {
    if (!enableSuggest) return;
    function onDoc(e: MouseEvent) {
      if (!wrapRef.current?.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [enableSuggest]);

  function pick(card: BusinessCard) {
    setOpen(false);
    setActive(-1);
    onSelectSuggestion?.(card);
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (!enableSuggest || !open || suggestions.length === 0) {
      if (e.key === "Escape") setOpen(false);
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => (i + 1) % suggestions.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => (i <= 0 ? suggestions.length - 1 : i - 1));
    } else if (e.key === "Escape") {
      e.preventDefault();
      setOpen(false);
      setActive(-1);
    } else if (e.key === "Enter" && active >= 0 && suggestions[active]) {
      e.preventDefault();
      pick(suggestions[active]);
    }
  }

  const showList = enableSuggest && open && suggestions.length > 0 && !loading;

  return (
    <div ref={wrapRef} className={`relative w-full ${large ? "max-w-3xl" : "max-w-2xl"}`}>
      <form
        className="relative w-full"
        onSubmit={(e) => {
          e.preventDefault();
          if (loading) return;
          // Enter without active option → full AI search
          setOpen(false);
          onSubmit();
        }}
      >
        <label className="sr-only" htmlFor="localai-search">
          Search
        </label>
        <input
          id="localai-search"
          role="combobox"
          aria-expanded={showList}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={
            showList && active >= 0 ? `${listId}-opt-${active}` : undefined
          }
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => {
            if (enableSuggest && suggestions.length > 0) setOpen(true);
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={loading}
          className={`w-full rounded-2xl bg-surface-container-lowest border border-outline-variant/40 card-shadow
            pl-5 pr-16 text-on-surface placeholder:text-on-surface-variant/70
            focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
            ${large ? "h-14 text-base" : "h-12 text-sm"}`}
          autoComplete="off"
        />
        <button
          type="submit"
          disabled={loading || !value.trim()}
          aria-label="Search"
          className="absolute right-2 top-1/2 -translate-y-1/2 h-10 w-10 rounded-xl ai-gradient text-white
            flex items-center justify-center disabled:opacity-50 shadow-md"
        >
          {loading ? (
            <span className="material-symbols-outlined animate-spin text-[20px]">progress_activity</span>
          ) : (
            <span className="material-symbols-outlined text-[20px]">search</span>
          )}
        </button>
      </form>

      {showList && (
        <ul
          id={listId}
          role="listbox"
          className="absolute left-0 right-0 top-full z-50 mt-2 w-full max-h-80 overflow-auto rounded-2xl border border-outline-variant/40
            bg-surface-container-lowest card-shadow text-left"
        >
          {suggestions.map((s, i) => {
            const title = s.name || s.business_id || "Business";
            const meta =
              s.subtitle ||
              [s.rating ? `★${s.rating}` : "", s.city || s.location || "", s.categories]
                .filter(Boolean)
                .join(" · ");
            const selected = i === active;
            return (
              <li key={(s.business_id || s.name || "row") + i} role="presentation">
                <button
                  type="button"
                  id={`${listId}-opt-${i}`}
                  role="option"
                  aria-selected={selected}
                  className={`w-full px-4 py-3 text-left flex flex-col gap-0.5 border-b border-outline-variant/20 last:border-0
                    ${selected ? "bg-primary/10" : "hover:bg-surface-container-low"}`}
                  onMouseEnter={() => setActive(i)}
                  onMouseDown={(e) => {
                    // prevent input blur before click
                    e.preventDefault();
                    pick(s);
                  }}
                >
                  <span className="font-semibold text-on-surface truncate">{title}</span>
                  {meta && (
                    <span className="text-xs text-on-surface-variant font-mono truncate">{meta}</span>
                  )}
                </button>
              </li>
            );
          })}
          {suggestLoading && (
            <li className="px-4 py-2 text-xs text-on-surface-variant font-mono">Updating…</li>
          )}
        </ul>
      )}
    </div>
  );
}
