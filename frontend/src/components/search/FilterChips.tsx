import type { UiBusiness } from "../../api/types";

type Props = {
  openOnly: boolean;
  setOpenOnly: (v: boolean) => void;
  price: string | null;
  setPrice: (v: string | null) => void;
  category: string;
  setCategory: (v: string) => void;
  categories: string[];
};

export function filterBusinesses(
  items: UiBusiness[],
  opts: { openOnly: boolean; price: string | null; category: string }
) {
  return items.filter((b) => {
    if (opts.openOnly && b.isOpen === false) return false;
    if (opts.price && b.priceLabel !== opts.price) return false;
    if (
      opts.category &&
      !b.categories.toLowerCase().includes(opts.category.toLowerCase())
    )
      return false;
    return true;
  });
}

export default function FilterChips(props: Props) {
  const prices = ["$", "$$", "$$$", "$$$$"];
  return (
    <div className="flex flex-wrap gap-2 items-center">
      <button
        type="button"
        onClick={() => props.setOpenOnly(!props.openOnly)}
        className={`px-3 py-1.5 rounded-full text-sm border ${
          props.openOnly
            ? "bg-secondary text-on-secondary border-secondary"
            : "bg-surface-container-lowest border-outline-variant text-on-surface"
        }`}
      >
        Open Now
      </button>
      {prices.map((p) => (
        <button
          key={p}
          type="button"
          onClick={() => props.setPrice(props.price === p ? null : p)}
          className={`px-3 py-1.5 rounded-full text-sm border font-mono ${
            props.price === p
              ? "bg-primary text-on-primary border-primary"
              : "bg-surface-container-lowest border-outline-variant"
          }`}
        >
          {p}
        </button>
      ))}
      {props.categories.slice(0, 6).map((c) => (
        <button
          key={c}
          type="button"
          onClick={() =>
            props.setCategory(props.category === c ? "" : c)
          }
          className={`px-3 py-1.5 rounded-full text-sm border ${
            props.category === c
              ? "bg-primary-container text-on-primary border-primary-container"
              : "bg-surface-container-low border-outline-variant/50 text-on-surface-variant"
          }`}
        >
          {c}
        </button>
      ))}
    </div>
  );
}
