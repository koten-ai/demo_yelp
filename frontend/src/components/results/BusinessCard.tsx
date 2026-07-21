import { Link } from "react-router-dom";
import type { UiBusiness } from "../../api/types";

type Props = {
  business: UiBusiness;
  compact?: boolean;
};

function Stars({ rating }: { rating: number | null }) {
  if (rating == null) return null;
  return (
    <span className="inline-flex items-center gap-1 text-secondary font-semibold text-sm">
      <span className="material-symbols-outlined text-[16px]" style={{ fontVariationSettings: "'FILL' 1" }}>
        star
      </span>
      {rating.toFixed(1)}
    </span>
  );
}

export default function BusinessCard({ business, compact }: Props) {
  return (
    <Link
      to={`/business/${encodeURIComponent(business.id)}`}
      state={{ business: business.raw }}
      className="group block bg-surface-container-lowest rounded-2xl border border-outline-variant/40 card-shadow overflow-hidden hover:shadow-md transition-shadow"
    >
      {!compact && (
        <div className="aspect-[16/10] overflow-hidden bg-surface-container">
          <img
            src={business.image}
            alt=""
            className="w-full h-full object-cover group-hover:scale-[1.02] transition-transform"
          />
        </div>
      )}
      <div className={`p-4 ${compact ? "flex gap-3 items-start" : ""}`}>
        {compact && (
          <img
            src={business.image}
            alt=""
            className="w-16 h-16 rounded-xl object-cover shrink-0 bg-surface-container"
          />
        )}
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-semibold text-on-surface truncate">{business.title}</h3>
            <Stars rating={business.rating} />
          </div>
          <div className="mt-1 flex flex-wrap gap-x-2 gap-y-1 text-xs text-on-surface-variant font-mono">
            {business.categories && <span>{business.categories.split(",")[0]}</span>}
            {business.priceLabel && <span>· {business.priceLabel}</span>}
            {business.isOpen === true && (
              <span className="text-secondary">· Open</span>
            )}
            {business.isOpen === false && <span>· Closed</span>}
          </div>
          {business.location && (
            <p className="mt-1 text-sm text-on-surface-variant truncate">
              {business.location}
            </p>
          )}
          {business.description && (
            <p className="mt-2 text-sm text-on-surface line-clamp-2">
              {business.description}
            </p>
          )}
          {business.reviewCount && (
            <p className="mt-2 text-xs text-on-surface-variant">
              {business.reviewCount} reviews
            </p>
          )}
        </div>
      </div>
    </Link>
  );
}
