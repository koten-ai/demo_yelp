import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { ErrorBanner, LoadingBlock } from "../components/common/States";
import { fetchBusiness, fetchInsight } from "../api/client";
import { normalizeBusiness } from "../lib/normalize";
import { appendTrace } from "../lib/trace";
import { getChatId } from "../state/session";
import type { BusinessCard, InsightResponse, SearchResponse, UiBusiness } from "../api/types";

export default function BusinessDetailsPage() {
  const { id = "" } = useParams();
  const loc = useLocation();
  const seeded = (loc.state as { business?: BusinessCard } | null)?.business;

  const [biz, setBiz] = useState<UiBusiness | null>(
    seeded ? normalizeBusiness(seeded) : null
  );
  const [insight, setInsight] = useState<InsightResponse | null>(null);
  const [loading, setLoading] = useState(!seeded);
  const [insightLoading, setInsightLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!id) return;
      try {
        if (!seeded) {
          setLoading(true);
          const data = await fetchBusiness(id, getChatId());
          if (!cancelled && data.business) {
            setBiz(normalizeBusiness(data.business as BusinessCard));
          }
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (!cancelled) setLoading(false);
      }

      try {
        setInsightLoading(true);
        const ins = await fetchInsight(id, getChatId());
        if (!cancelled) {
          setInsight(ins);
          if (ins.trace && ins.answer) {
            appendTrace(`insight:${id}`, {
              query: `insight ${id}`,
              answer: ins.answer,
              trace: ins.trace,
              chat_id: ins.chat_id || "",
            } as SearchResponse);
          }
          if (!biz && ins.business) {
            setBiz(normalizeBusiness(ins.business));
          }
        }
      } catch (e) {
        if (!cancelled) {
          // insight is optional UX
          console.warn(e);
        }
      } finally {
        if (!cancelled) setInsightLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  if (loading) return <LoadingBlock label="Loading business…" />;

  return (
    <div className="mx-auto max-w-3xl px-4 md:px-10 py-6">
      <Link
        to="/search"
        className="inline-flex items-center gap-1 text-sm text-primary font-medium mb-4"
      >
        <span className="material-symbols-outlined text-[18px]">arrow_back</span>
        Back to search
      </Link>

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} />
        </div>
      )}

      {biz && (
        <div className="bg-surface-container-lowest rounded-2xl border border-outline-variant/40 overflow-hidden card-shadow">
          <div className="aspect-[21/9] bg-surface-container">
            <img src={biz.image} alt="" className="w-full h-full object-cover" />
          </div>
          <div className="p-6">
            {biz.categories && (
              <p className="text-xs font-mono uppercase tracking-wider text-secondary mb-2">
                {biz.categories}
              </p>
            )}
            <h1 className="text-3xl font-bold text-on-surface">{biz.title}</h1>
            <div className="mt-2 flex flex-wrap gap-3 text-sm text-on-surface-variant">
              {biz.rating != null && (
                <span className="text-secondary font-semibold flex items-center gap-1">
                  <span className="material-symbols-outlined text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>
                    star
                  </span>
                  {biz.rating.toFixed(1)}
                  {biz.reviewCount ? ` (${biz.reviewCount} reviews)` : ""}
                </span>
              )}
              {biz.priceLabel && <span>{biz.priceLabel}</span>}
              {biz.isOpen === true && <span className="text-secondary">Open</span>}
              {biz.location && <span>{biz.location}</span>}
            </div>
            {biz.description && (
              <p className="mt-4 text-on-surface leading-relaxed">{biz.description}</p>
            )}
          </div>
        </div>
      )}

      <section className="mt-6 glass rounded-2xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <span className="material-symbols-outlined text-primary">auto_awesome</span>
          <h2 className="font-bold text-primary">AI Review Summary</h2>
        </div>
        {insightLoading && <LoadingBlock label="Synthesizing reviews…" />}
        {!insightLoading && insight && (
          <div className="space-y-4">
            {insight.summary && (
              <p className="text-sm text-on-surface whitespace-pre-wrap line-clamp-6">
                {insight.summary}
              </p>
            )}
            <div className="grid md:grid-cols-3 gap-4">
              <InsightCol title="The Good" icon="thumb_up" items={insight.the_good} tone="good" />
              <InsightCol title="The Bad" icon="thumb_down" items={insight.the_bad} tone="bad" />
              <InsightCol title="Best For" icon="target" items={insight.best_for} tone="best" />
            </div>
            {insight.reviews?.length > 0 && (
              <div className="pt-4 border-t border-outline-variant/30">
                <h3 className="font-semibold mb-3">Recent Reviews</h3>
                <ul className="space-y-4">
                  {insight.reviews.map((r, i) => (
                    <li key={i} className="text-sm">
                      <div className="flex justify-between gap-2">
                        <span className="font-medium">{r.author}</span>
                        {r.stars && <span className="text-secondary">{r.stars}★</span>}
                      </div>
                      <p className="mt-1 text-on-surface-variant">{r.text}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
        {!insightLoading && !insight && (
          <p className="text-sm text-on-surface-variant">No insight available yet.</p>
        )}
      </section>
    </div>
  );
}

function InsightCol({
  title,
  icon,
  items,
  tone,
}: {
  title: string;
  icon: string;
  items: string[];
  tone: "good" | "bad" | "best";
}) {
  const color =
    tone === "good" ? "text-secondary" : tone === "bad" ? "text-error" : "text-primary";
  return (
    <div>
      <div className={`flex items-center gap-1 font-semibold text-sm ${color}`}>
        <span className="material-symbols-outlined text-[18px]">{icon}</span>
        {title}
      </div>
      <ul className="mt-2 space-y-1">
        {(items || []).length === 0 && (
          <li className="text-xs text-on-surface-variant">—</li>
        )}
        {(items || []).map((it, i) => (
          <li key={i} className="text-sm text-on-surface flex gap-1">
            <span className="material-symbols-outlined text-[14px] text-outline mt-0.5">
              check_circle
            </span>
            {it}
          </li>
        ))}
      </ul>
    </div>
  );
}
