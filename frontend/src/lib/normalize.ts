import type { BusinessCard, UiBusiness } from "../api/types";

const PLACEHOLDER =
  "data:image/svg+xml," +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="640" height="400" viewBox="0 0 640 400">
      <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#4f46e5"/><stop offset="100%" stop-color="#14b8a6"/>
      </linearGradient></defs>
      <rect width="640" height="400" fill="url(#g)" opacity="0.25"/>
      <rect width="640" height="400" fill="#e5eeff"/>
      <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle"
        fill="#3525cd" font-family="Inter,sans-serif" font-size="28" font-weight="700">LocalAI</text>
    </svg>`
  );

function looksLikeImageUrl(s: string): boolean {
  if (!s) return false;
  if (s.startsWith("data:image")) return true;
  return /^https?:\/\//i.test(s) && /\.(png|jpe?g|gif|webp|svg)(\?|$)/i.test(s);
}

export function normalizeBusiness(card: BusinessCard, index = 0): UiBusiness {
  const id =
    (card.business_id || "").trim() ||
    `${card.name || "biz"}-${index}`.toLowerCase().replace(/\s+/g, "-");
  const ratingRaw = card.rating ? Number(card.rating) : NaN;
  const lat = card.latitude ? Number(card.latitude) : NaN;
  const lon = card.longitude ? Number(card.longitude) : NaN;
  let isOpen: boolean | null = null;
  if (card.is_open === "true") isOpen = true;
  if (card.is_open === "false") isOpen = false;
  const image =
    card.image && looksLikeImageUrl(card.image) ? card.image : PLACEHOLDER;

  return {
    id,
    title: card.name || "Unknown",
    description: card.description || "",
    image,
    rating: Number.isFinite(ratingRaw) ? ratingRaw : null,
    reviewCount: card.review_count || "",
    categories: card.categories || "",
    priceLabel: card.price || "",
    isOpen,
    location:
      card.location ||
      [card.address, card.city, card.state].filter(Boolean).join(", "),
    latitude: Number.isFinite(lat) ? lat : null,
    longitude: Number.isFinite(lon) ? lon : null,
    raw: card,
  };
}

export function summaryFromResponse(answer: unknown, structured: unknown): string {
  if (structured && typeof structured === "object") {
    const s = structured as Record<string, unknown>;
    const tip = typeof s.tip === "string" ? s.tip : "";
    const ctx = typeof s.context === "string" ? s.context : "";
    if (ctx) return ctx;
    if (tip) return tip;
  }
  if (typeof answer === "string") return answer;
  if (answer && typeof answer === "object") {
    try {
      return JSON.stringify(answer);
    } catch {
      return "";
    }
  }
  return "";
}
