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
  // Local AI-generated assets under frontend/public (and backend mount).
  if (s.startsWith("/business-images/")) return true;
  if (s.startsWith("/")) return /\.(png|jpe?g|gif|webp|svg)(\?|$)/i.test(s);
  return /^https?:\/\//i.test(s) && /\.(png|jpe?g|gif|webp|svg)(\?|$)/i.test(s);
}

function localGallery(businessId: string, card: BusinessCard): string[] {
  const fromCard = (card.images || [])
    .map((u) => (typeof u === "string" ? u.trim() : ""))
    .filter((u) => looksLikeImageUrl(u));
  if (fromCard.length) return fromCard;
  if (card.image && looksLikeImageUrl(card.image)) return [card.image];
  return [];
}

export function normalizeBusiness(card: BusinessCard, index = 0): UiBusiness {
  const rawId = (card.business_id || "").trim();
  // Zeus project rows use file::<hash> / n_* as graph node ids; SPA routes need
  // Yelp source keys (biz:…). Prefer business_id only when it is not a graph id.
  const isGraphId =
    rawId.startsWith("file::") ||
    rawId.startsWith("file:") ||
    rawId.startsWith("n_");
  const id =
    (rawId && !isGraphId ? rawId : "") ||
    `${card.name || "biz"}-${index}`.toLowerCase().replace(/\s+/g, "-");
  const ratingRaw = card.rating ? Number(card.rating) : NaN;
  const lat = card.latitude ? Number(card.latitude) : NaN;
  const lon = card.longitude ? Number(card.longitude) : NaN;
  let isOpen: boolean | null = null;
  if (card.is_open === "true") isOpen = true;
  if (card.is_open === "false") isOpen = false;
  const gallery = localGallery(id, card);
  const primary =
    (card.image && looksLikeImageUrl(card.image) && card.image) ||
    gallery[0] ||
    "";
  const image = primary || PLACEHOLDER;

  return {
    id,
    title: card.name || "Unknown",
    description: card.description || "",
    image,
    images: gallery.length ? gallery : primary ? [primary] : [],
    rating: Number.isFinite(ratingRaw) ? ratingRaw : null,
    reviewCount: card.review_count || "",
    categories: card.categories || "",
    priceLabel: card.price || "",
    isOpen,
    hoursToday: (card.hours_today || "").trim(),
    location:
      card.location ||
      [card.address, card.city, card.state].filter(Boolean).join(", "),
    address: (card.address || "").trim(),
    city: (card.city || "").trim(),
    state: (card.state || "").trim(),
    url: (card.url || "").trim(),
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
  if (typeof answer === "string") {
    const t = answer.trim();
    if (!t || t === "(model returned no content)") return "";
    const peeled = peelLayerASummary(t);
    if (peeled) return peeled;
    return answer;
  }
  if (answer && typeof answer === "object") {
    const obj = answer as Record<string, unknown>;
    if (typeof obj.summary === "string" && obj.summary.trim()) {
      // Object-shaped Layer A / pipeline envelope — never JSON.stringify whole bag.
      if (
        "policy_action" in obj ||
        "query_decomposition" in obj ||
        "jail_break_attempt" in obj
      ) {
        return obj.summary.trim();
      }
    }
    try {
      return JSON.stringify(answer);
    } catch {
      return "";
    }
  }
  return "";
}

/** Detect/peel Layer A terminate dumps the model sometimes echoes into the answer. */
function peelLayerASummary(text: string): string | null {
  let body = text.trim();
  const fence = body.match(/^```(?:json|yaml|yml|markdown|md)?\s*\n([\s\S]*?)\n```\s*$/i);
  if (fence) body = fence[1].trim();
  else if (body.startsWith("```")) {
    const lines = body.split("\n");
    if (lines[0]?.startsWith("```")) lines.shift();
    if (lines[lines.length - 1]?.trim() === "```") lines.pop();
    body = lines.join("\n").trim();
  }

  const metaKeys = [
    "confidence",
    "query_decomposition",
    "decomposition",
    "policy_action",
    "subject_confidence",
    "jail_break_attempt",
    "wish_i_knew",
    "business_rules_triggers",
  ];
  const hasSummary = /^summary\s*:/m.test(body) || (body.startsWith("{") && body.includes('"summary"'));
  if (!hasSummary) return null;
  const metaHits = metaKeys.filter((k) =>
    body.startsWith("{") ? body.includes(`"${k}"`) : new RegExp(`^${k}\\s*:`, "m").test(body),
  ).length;
  if (metaHits < 2) return null;

  if (body.startsWith("{")) {
    try {
      const obj = JSON.parse(body) as Record<string, unknown>;
      if (typeof obj.summary === "string" && obj.summary.trim()) return obj.summary.trim();
    } catch {
      /* fall through */
    }
  }

  // summary: "....escaped...."  (single physical line; \n inside quotes)
  const quoted = body.match(/^summary\s*:\s*("(?:\\.|[^"\\])*")\s*$/m);
  if (quoted) {
    try {
      const val = JSON.parse(quoted[1]) as string;
      if (typeof val === "string" && val.trim()) return val.trim();
    } catch {
      const raw = quoted[1].slice(1, -1);
      return raw
        .replace(/\\n/g, "\n")
        .replace(/\\t/g, "\t")
        .replace(/\\"/g, '"')
        .replace(/\\\\/g, "\\")
        .trim();
    }
  }

  const unquoted = body.match(/^summary\s*:\s*(.+?)\s*$/m);
  if (unquoted) {
    const val = unquoted[1].trim().replace(/^["']|["']$/g, "");
    if (val && !val.startsWith("{")) return val.replace(/\\n/g, "\n").trim();
  }
  return null;
}
