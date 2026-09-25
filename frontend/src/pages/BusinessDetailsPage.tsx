import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { ErrorBanner, LoadingBlock } from "../components/common/States";
import PhotoCarouselModal from "../components/gallery/PhotoCarouselModal";
import ResultsMap from "../components/map/ResultsMap";
import { fetchBusiness, fetchInsight, fetchReviews } from "../api/client";
import { normalizeBusiness } from "../lib/normalize";
import type {
  BusinessCard,
  InsightResponse,
  ReviewItem,
  UiBusiness,
} from "../api/types";

const REVIEWS_PAGE = 3;

export default function BusinessDetailsPage() {
  const { id = "" } = useParams();
  const loc = useLocation();
  const seeded = (loc.state as { business?: BusinessCard } | null)?.business;

  const [biz, setBiz] = useState<UiBusiness | null>(
    seeded ? normalizeBusiness(seeded) : null
  );
  const [insight, setInsight] = useState<InsightResponse | null>(null);
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(!seeded);
  const [insightLoading, setInsightLoading] = useState(true);
  const [reviewsLoading, setReviewsLoading] = useState(true);
  const [error, setError] = useState("");
  /** Modal carousel index only — hero grid tiles stay fixed at 0/1/2. */
  const [galleryIndex, setGalleryIndex] = useState(0);
  const [galleryOpen, setGalleryOpen] = useState(false);
  const [reviewsShown, setReviewsShown] = useState(REVIEWS_PAGE);
  const [favorited, setFavorited] = useState(false);
  const [shareHint, setShareHint] = useState("");

  useEffect(() => {
    let cancelled = false;
    setGalleryIndex(0);
    setReviewsShown(REVIEWS_PAGE);
    setInsight(null);
    setReviews([]);

    async function load() {
      if (!id) return;

      const businessP = (async () => {
        if (seeded) return;
        setLoading(true);
        try {
          const data = await fetchBusiness(id);
          if (!cancelled && data.business) {
            setBiz(normalizeBusiness(data.business as BusinessCard));
          }
        } catch (e) {
          if (!cancelled) setError(e instanceof Error ? e.message : String(e));
        } finally {
          if (!cancelled) setLoading(false);
        }
      })();

      const reviewsP = (async () => {
        try {
          setReviewsLoading(true);
          const rev = await fetchReviews(id, 20);
          if (!cancelled) {
            setReviews(Array.isArray(rev.reviews) ? rev.reviews : []);
          }
        } catch (e) {
          if (!cancelled) console.warn(e);
        } finally {
          if (!cancelled) setReviewsLoading(false);
        }
      })();

      await Promise.all([businessP, reviewsP]);

      try {
        setInsightLoading(true);
        const ins = await fetchInsight(id);
        if (!cancelled) {
          setInsight(ins);
          if (ins.business) {
            setBiz((prev) => prev || normalizeBusiness(ins.business as BusinessCard));
          }
          if (Array.isArray(ins.reviews) && ins.reviews.length > 0) {
            setReviews((prev) => (prev.length ? prev : ins.reviews));
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

  const gallery = useMemo(() => {
    if (!biz) return [] as string[];
    const imgs = biz.images.length ? biz.images : biz.image ? [biz.image] : [];
    return imgs;
  }, [biz]);

  const categoryBadge = useMemo(() => {
    if (!biz?.categories) return "";
    return biz.categories.split(",")[0]?.trim() || "";
  }, [biz]);

  async function onShare() {
    const url = window.location.href;
    const title = biz?.title || "Business";
    try {
      if (navigator.share) {
        await navigator.share({ title, url });
        return;
      }
    } catch {
      /* user cancelled or share failed — fall through to clipboard */
    }
    try {
      await navigator.clipboard.writeText(url);
      setShareHint("Link copied");
      window.setTimeout(() => setShareHint(""), 2000);
    } catch {
      setShareHint("Could not copy link");
      window.setTimeout(() => setShareHint(""), 2000);
    }
  }

  function openGalleryAt(i: number) {
    if (!gallery.length) return;
    const n = gallery.length;
    setGalleryIndex(((i % n) + n) % n);
    setGalleryOpen(true);
  }

  if (loading) return <LoadingBlock label="Loading business…" />;

  const visibleReviews = reviews.slice(0, reviewsShown);
  const hasMoreReviews = reviews.length > reviewsShown;
  const reviewSynthLabel = biz?.reviewCount
    ? `SYNTHESIZED FROM ${biz.reviewCount} REVIEWS`
    : "SYNTHESIZED FROM REVIEWS";

  const openLabel =
    biz?.isOpen === true
      ? biz.hoursToday
        ? `Open until ${biz.hoursToday}`
        : "Open now"
      : biz?.isOpen === false
        ? "Closed"
        : biz?.hoursToday || "";

  const websiteHost = displayWebsite(biz?.url || "");

  return (
    <div className="pb-24">
      {/* Contextual header — Stitch business details (nav suppressed) */}
      <header className="sticky top-16 z-20 bg-surface/70 backdrop-blur-xl border-b border-white/20 shadow-sm">
        <div className="mx-auto flex max-w-[1280px] items-center justify-between px-4 py-4 md:px-10">
          <Link
            to="/search"
            className="flex items-center gap-2 text-on-surface-variant transition-colors hover:text-primary"
          >
            <span className="material-symbols-outlined">arrow_back</span>
            <span className="font-mono text-xs uppercase tracking-wider">Back to search</span>
          </Link>
          <div className="flex items-center gap-2 sm:gap-4">
            {shareHint && (
              <span className="text-xs font-mono text-secondary" role="status">
                {shareHint}
              </span>
            )}
            <button
              type="button"
              onClick={() => void onShare()}
              className="text-on-surface-variant transition-colors hover:text-primary p-1"
              aria-label="Share"
            >
              <span className="material-symbols-outlined">share</span>
            </button>
            <button
              type="button"
              onClick={() => setFavorited((v) => !v)}
              className="text-on-surface-variant transition-colors hover:text-primary p-1"
              aria-label={favorited ? "Unfavorite" : "Favorite"}
              aria-pressed={favorited}
            >
              <span
                className="material-symbols-outlined"
                style={favorited ? { fontVariationSettings: "'FILL' 1" } : undefined}
              >
                {favorited ? "favorite" : "favorite_border"}
              </span>
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1280px] pb-8">
        {error && (
          <div className="px-4 md:px-10 mt-4">
            <ErrorBanner message={error} />
          </div>
        )}

        {/* Hero gallery */}
        {biz && (
          <section
            className={`mt-4 grid w-full gap-2 overflow-hidden rounded-3xl px-2 md:px-10 ${
              gallery.length >= 3
                ? "grid-cols-1 md:grid-cols-4 md:grid-rows-2 h-auto md:h-[614px]"
                : gallery.length === 2
                  ? "grid-cols-1 md:grid-cols-2 h-auto md:h-[420px]"
                  : "grid-cols-1 h-[280px] md:h-[420px]"
            }`}
          >
            <button
              type="button"
              onClick={() => openGalleryAt(0)}
              className={`relative overflow-hidden rounded-xl group text-left ${
                gallery.length >= 3
                  ? "md:col-span-2 md:row-span-2 md:rounded-l-3xl min-h-[240px] md:min-h-0"
                  : "min-h-[240px] md:min-h-0 md:rounded-l-3xl"
              }`}
              aria-label="Open photo gallery"
            >
              <img
                src={gallery[0] || biz.image}
                alt=""
                className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
              />
              <div className="pointer-events-none absolute inset-0 flex items-end bg-gradient-to-t from-black/40 to-transparent p-6 md:p-8">
                {categoryBadge && (
                  <span className="rounded-full bg-white/90 px-3 py-1 font-mono text-xs uppercase tracking-wider text-primary shadow-sm backdrop-blur">
                    {categoryBadge}
                  </span>
                )}
              </div>
            </button>

            {gallery.length >= 2 && (
              <div
                className={`relative hidden overflow-hidden rounded-xl group md:block ${
                  gallery.length === 2 ? "md:rounded-r-3xl" : ""
                }`}
              >
                <button
                  type="button"
                  className="h-full w-full"
                  onClick={() => openGalleryAt(1 % gallery.length)}
                  aria-label="Open photo 2"
                >
                  <img
                    src={gallery[1] || gallery[0]}
                    alt=""
                    className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
                  />
                </button>
              </div>
            )}

            {gallery.length >= 3 && (
              <div className="relative hidden overflow-hidden rounded-r-3xl group md:block">
                <button
                  type="button"
                  className="h-full w-full"
                  onClick={() => openGalleryAt(2)}
                  aria-label={`View all ${gallery.length} photos`}
                >
                  <img
                    src={gallery[2] || gallery[0]}
                    alt=""
                    className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 backdrop-blur-sm transition-opacity duration-300 group-hover:opacity-100">
                    <span className="flex items-center gap-2 rounded-full bg-white px-4 py-2 font-mono text-xs uppercase tracking-wider text-primary shadow-l2">
                      <span
                        className="material-symbols-outlined text-[18px]"
                        style={{ fontVariationSettings: "'FILL' 1" }}
                      >
                        grid_view
                      </span>
                      View all {gallery.length} photos
                    </span>
                  </div>
                </button>
              </div>
            )}

            {/* Mobile multi-thumb strip — tap opens carousel at that index */}
            {gallery.length > 1 && (
              <div className="flex gap-2 overflow-x-auto pb-1 md:hidden col-span-full">
                {gallery.map((src, i) => (
                  <button
                    key={`${src}-${i}`}
                    type="button"
                    onClick={() => openGalleryAt(i)}
                    className={`h-16 w-20 shrink-0 overflow-hidden rounded-lg ring-2 ${
                      galleryOpen && i === galleryIndex
                        ? "ring-primary"
                        : "ring-transparent"
                    }`}
                    aria-label={`Open photo ${i + 1}`}
                  >
                    <img src={src} alt="" className="h-full w-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </section>
        )}

        {/* Main content grid */}
        <div className="mt-8 grid grid-cols-1 gap-6 px-4 md:mt-12 md:grid-cols-12 md:gap-6 md:px-10">
          {/* Left: primary info + AI + reviews */}
          <div className="space-y-12 md:col-span-8">
            {biz && (
              <div>
                <h1 className="text-3xl font-bold tracking-tight text-on-surface md:text-5xl md:leading-tight">
                  {biz.title}
                </h1>
                <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-2 text-on-surface-variant">
                  {biz.rating != null && (
                    <span className="flex items-center font-bold text-secondary">
                      <span
                        className="material-symbols-outlined mr-1 text-[20px] text-secondary"
                        style={{ fontVariationSettings: "'FILL' 1" }}
                      >
                        star
                      </span>
                      {biz.rating.toFixed(1)}
                      {biz.reviewCount ? ` (${formatReviewCount(biz.reviewCount)} reviews)` : ""}
                    </span>
                  )}
                  {biz.priceLabel && (
                    <>
                      <span aria-hidden>•</span>
                      <span>{biz.priceLabel}</span>
                    </>
                  )}
                  {openLabel && (
                    <>
                      <span aria-hidden>•</span>
                      <span>{openLabel}</span>
                    </>
                  )}
                  {biz.location && (
                    <>
                      <span aria-hidden>•</span>
                      <span className="font-medium text-primary">{biz.location}</span>
                    </>
                  )}
                </div>
                {biz.description && (
                  <p className="mt-4 max-w-3xl text-on-surface leading-relaxed">{biz.description}</p>
                )}
              </div>
            )}

            {/* AI Review Summary bento */}
            <section className="relative rounded-2xl bg-gradient-to-br from-secondary-container to-primary-container p-px shadow-l2">
              <div className="glass relative h-full overflow-hidden rounded-2xl p-6 md:p-8">
                <div
                  className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-primary/10 blur-3xl"
                  aria-hidden
                />
                <div
                  className="pointer-events-none absolute -bottom-20 -left-20 h-48 w-48 rounded-full bg-secondary/10 blur-3xl"
                  aria-hidden
                />

                <div className="relative z-10 mb-6 flex items-center gap-3">
                  <div className="ai-gradient-bg ai-glow flex h-10 w-10 items-center justify-center rounded-full">
                    <span className="material-symbols-outlined text-white">auto_awesome</span>
                  </div>
                  <div>
                    <h2 className="ai-gradient-text text-xl font-semibold">AI Review Summary</h2>
                    <p className="mt-1 font-mono text-[12px] uppercase tracking-wider text-on-surface-variant">
                      {reviewSynthLabel}
                    </p>
                  </div>
                </div>

                {insightLoading && (
                  <div className="relative z-10">
                    <LoadingBlock label="Synthesizing reviews…" />
                  </div>
                )}

                {!insightLoading && insight && (
                  <div className="relative z-10 space-y-6">
                    {insight.summary && !hasStructuredInsight(insight) && (
                      <p className="text-sm text-on-surface whitespace-pre-wrap line-clamp-8">
                        {insight.summary}
                      </p>
                    )}
                    <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
                      <InsightPanel
                        title="The Good"
                        icon="thumb_up"
                        tone="good"
                        items={insight.the_good}
                      />
                      <InsightPanel
                        title="The Bad"
                        icon="thumb_down"
                        tone="bad"
                        items={insight.the_bad}
                      />
                      <BestForPanel items={insight.best_for} />
                    </div>
                  </div>
                )}

                {!insightLoading && !insight && (
                  <p className="relative z-10 text-sm text-on-surface-variant">
                    No insight available yet.
                  </p>
                )}
              </div>
            </section>

            <hr className="border-outline-variant/30" />

            {/* Recent Reviews */}
            <section>
              <div className="mb-6 flex items-center justify-between gap-4">
                <h2 className="text-2xl font-bold tracking-tight text-on-surface md:text-[32px] md:leading-tight">
                  Recent Reviews
                </h2>
                {reviews.length > 0 && (
                  <span className="shrink-0 rounded-lg px-4 py-2 font-mono text-xs uppercase tracking-wider text-primary">
                    Sort by: Relevant
                  </span>
                )}
              </div>

              {reviewsLoading && <LoadingBlock label="Loading reviews…" />}

              {!reviewsLoading && reviews.length === 0 && (
                <p className="text-sm text-on-surface-variant">
                  No individual reviews returned for this place yet.
                </p>
              )}

              <div className="space-y-8">
                {visibleReviews.map((r, i) => (
                  <ReviewRow key={r.review_id || r.user_id || `${r.author}-${i}`} review={r} />
                ))}
              </div>

              {hasMoreReviews && (
                <button
                  type="button"
                  onClick={() => setReviewsShown((n) => n + REVIEWS_PAGE)}
                  className="mt-6 w-full rounded-xl border-2 border-primary/20 py-4 text-xl font-semibold text-primary transition-colors hover:bg-surface-container"
                >
                  Load More Reviews
                </button>
              )}
            </section>
          </div>

          {/* Right: sticky actions + details */}
          <div className="md:col-span-4">
            <div className="sticky top-36 space-y-6">

              <div className="overflow-hidden rounded-2xl border border-outline-variant/20 bg-white shadow-l1">
                <div className="h-48 w-full bg-surface-container-high">
                  {biz && biz.latitude != null && biz.longitude != null ? (
                    <ResultsMap items={[biz]} compact />
                  ) : (
                    <div className="flex h-full items-center justify-center gap-2 p-4 text-center text-sm text-on-surface-variant">
                      <span className="material-symbols-outlined">map</span>
                      Map unavailable — no coordinates
                    </div>
                  )}
                </div>
                <div className="space-y-5 p-6">
                  {(biz?.address || biz?.location) && (
                    <div className="flex items-start gap-4">
                      <span className="material-symbols-outlined mt-1 text-outline">location_on</span>
                      <div>
                        {biz.address ? (
                          <>
                            <p className="text-on-surface">{biz.address}</p>
                            {(biz.city || biz.state) && (
                              <p className="text-sm text-on-surface-variant">
                                {[biz.city, biz.state].filter(Boolean).join(", ")}
                              </p>
                            )}
                          </>
                        ) : (
                          <p className="text-on-surface">{biz.location}</p>
                        )}
                      </div>
                    </div>
                  )}

                  {(biz?.isOpen != null || biz?.hoursToday) && (
                    <div className="flex items-center gap-4">
                      <span className="material-symbols-outlined text-outline">schedule</span>
                      <div className="flex flex-1 items-center justify-between gap-2">
                        <p className="text-on-surface">
                          {biz.isOpen === true
                            ? "Open Now"
                            : biz.isOpen === false
                              ? "Closed"
                              : "Hours"}
                        </p>
                        {biz.hoursToday && (
                          <p className="text-sm text-on-surface-variant">
                            {biz.isOpen === true ? `Closes ${biz.hoursToday}` : biz.hoursToday}
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {websiteHost && biz?.url && (
                    <div className="flex items-center gap-4">
                      <span className="material-symbols-outlined text-outline">language</span>
                      <a
                        href={biz.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-on-surface transition-colors hover:text-primary"
                      >
                        {websiteHost}
                      </a>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <PhotoCarouselModal
        images={gallery}
        index={galleryIndex}
        title={biz?.title}
        open={galleryOpen}
        onClose={() => setGalleryOpen(false)}
        onIndexChange={setGalleryIndex}
      />
    </div>
  );
}

function hasStructuredInsight(insight: InsightResponse): boolean {
  return (
    (insight.the_good?.length || 0) +
      (insight.the_bad?.length || 0) +
      (insight.best_for?.length || 0) >
    0
  );
}

function formatReviewCount(raw: string): string {
  const n = Number(String(raw).replace(/,/g, ""));
  if (!Number.isFinite(n)) return raw;
  return n.toLocaleString();
}

function displayWebsite(url: string): string {
  if (!url) return "";
  try {
    const u = new URL(url.startsWith("http") ? url : `https://${url}`);
    return u.hostname.replace(/^www\./, "");
  } catch {
    return url.replace(/^https?:\/\//, "").replace(/^www\./, "").split("/")[0] || url;
  }
}

const MAX_INSIGHT_ITEMS_PER_COLUMN = 3;

function InsightPanel({
  title,
  icon,
  tone,
  items,
}: {
  title: string;
  icon: string;
  tone: "good" | "bad";
  items: string[];
}) {
  const heading =
    tone === "good" ? "text-secondary" : "text-tertiary";
  const bulletIcon = tone === "good" ? "check_circle" : "warning";
  const bulletColor = tone === "good" ? "text-secondary" : "text-tertiary";
  const visible = (items || []).slice(0, MAX_INSIGHT_ITEMS_PER_COLUMN);

  return (
    <div className="rounded-xl border border-white/40 bg-white/60 p-5">
      <h3
        className={`mb-3 flex items-center gap-2 font-mono text-xs font-bold uppercase tracking-wider ${heading}`}
      >
        <span className="material-symbols-outlined text-sm">{icon}</span>
        {title}
      </h3>
      <ul className="space-y-3 text-sm text-on-surface">
        {visible.length === 0 && (
          <li className="text-on-surface-variant">—</li>
        )}
        {visible.map((it, i) => (
          <li key={i} className="flex items-start gap-2">
            <span className={`material-symbols-outlined mt-0.5 text-base ${bulletColor}`}>
              {bulletIcon}
            </span>
            <span>{it}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function BestForPanel({ items }: { items: string[] }) {
  const visible = (items || []).slice(0, MAX_INSIGHT_ITEMS_PER_COLUMN);
  return (
    <div className="rounded-xl border border-white/40 bg-white/60 p-5 md:col-span-1">
      <h3 className="mb-3 flex items-center gap-2 font-mono text-xs font-bold uppercase tracking-wider text-primary">
        <span className="material-symbols-outlined text-sm">target</span>
        Best For
      </h3>
      <div className="mt-2 flex flex-wrap gap-2">
        {visible.length === 0 && (
          <span className="text-sm text-on-surface-variant">—</span>
        )}
        {visible.map((it, i) => (
          <span
            key={i}
            className="rounded-lg border border-primary/10 bg-surface-container px-3 py-1.5 font-mono text-xs uppercase tracking-wider text-primary"
          >
            {it}
          </span>
        ))}
      </div>
    </div>
  );
}

function ReviewRow({
  review,
}: {
  review: {
    author: string;
    stars: string;
    text: string;
    date: string;
    user_review_count?: string;
    yelping_since?: string;
  };
}) {
  const initials = initialsFrom(review.author);
  const stars = parseStars(review.stars);
  const reviewCountLabel = formatUserReviewCount(review.user_review_count);
  const meta = [reviewCountLabel, review.date].filter(Boolean).join(" · ");

  return (
    <div className="border-b border-outline-variant/30 pb-8 last:border-0">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-container-high text-lg font-semibold text-primary">
            {initials}
          </div>
          <div>
            <h4 className="text-lg font-semibold text-on-surface">{review.author || "Reviewer"}</h4>
            {meta && <p className="text-sm text-on-surface-variant">{meta}</p>}
          </div>
        </div>
        {stars != null && <StarRow value={stars} />}
      </div>
      <p className="leading-relaxed text-on-surface">{review.text}</p>
    </div>
  );
}

function formatUserReviewCount(raw?: string): string {
  if (!raw) return "";
  const n = Number(String(raw).replace(/[^\d.]/g, ""));
  if (!Number.isFinite(n) || n <= 0) return "";
  const rounded = Math.round(n);
  return `${rounded.toLocaleString()} review${rounded === 1 ? "" : "s"}`;
}

function StarRow({ value }: { value: number }) {
  const full = Math.round(Math.min(5, Math.max(0, value)));
  return (
    <div className="flex shrink-0 text-secondary" aria-label={`${value} stars`}>
      {Array.from({ length: 5 }, (_, i) => (
        <span
          key={i}
          className={`material-symbols-outlined text-[20px] ${
            i < full ? "text-secondary" : "text-outline-variant"
          }`}
          style={i < full ? { fontVariationSettings: "'FILL' 1" } : undefined}
        >
          star
        </span>
      ))}
    </div>
  );
}

function parseStars(raw: string): number | null {
  if (!raw) return null;
  const n = Number(String(raw).replace(/[^\d.]/g, ""));
  return Number.isFinite(n) ? n : null;
}

function initialsFrom(name: string): string {
  const parts = (name || "").trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}
