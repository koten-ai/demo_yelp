import { useCallback, useEffect, useId, useRef } from "react";

type Props = {
  images: string[];
  index: number;
  title?: string;
  open: boolean;
  onClose: () => void;
  onIndexChange: (index: number) => void;
};

/**
 * Full-screen photo carousel modal with prev/next controls and a bottom
 * thumbnail strip so users can jump to nearby images.
 */
export default function PhotoCarouselModal({
  images,
  index,
  title,
  open,
  onClose,
  onIndexChange,
}: Props) {
  const labelId = useId();
  const thumbRowRef = useRef<HTMLDivElement>(null);
  const count = images.length;
  const safeIndex = count > 0 ? ((index % count) + count) % count : 0;
  const current = count > 0 ? images[safeIndex] : "";

  const go = useCallback(
    (delta: number) => {
      if (count <= 1) return;
      onIndexChange(((safeIndex + delta) % count + count) % count);
    },
    [count, onIndexChange, safeIndex]
  );

  // Keyboard: Esc close, arrows navigate
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        go(-1);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        go(1);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose, go]);

  // Lock body scroll while open
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  // Keep active thumbnail in view
  useEffect(() => {
    if (!open || !thumbRowRef.current) return;
    const el = thumbRowRef.current.querySelector<HTMLElement>(
      `[data-thumb-index="${safeIndex}"]`
    );
    el?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
  }, [open, safeIndex]);

  if (!open || count === 0) return null;

  return (
    <div
      className="fixed inset-0 z-[60] flex flex-col bg-black/90 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby={labelId}
      onClick={onClose}
    >
      {/* Header */}
      <div
        className="flex shrink-0 items-center justify-between gap-3 px-4 py-3 text-white md:px-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="min-w-0">
          <h3 id={labelId} className="truncate font-semibold">
            {title ? `${title}` : "Photos"}
          </h3>
          <p className="font-mono text-xs uppercase tracking-wider text-white/70">
            {safeIndex + 1} / {count}
          </p>
        </div>
        <button
          type="button"
          className="rounded-full bg-white/10 p-2 text-white transition-colors hover:bg-white/20"
          onClick={onClose}
          aria-label="Close gallery"
        >
          <span className="material-symbols-outlined">close</span>
        </button>
      </div>

      {/* Main stage */}
      <div
        className="relative flex min-h-0 flex-1 items-center justify-center px-12 md:px-16"
        onClick={(e) => e.stopPropagation()}
      >
        {count > 1 && (
          <button
            type="button"
            className="absolute left-2 z-10 flex h-11 w-11 items-center justify-center rounded-full bg-white/15 text-white shadow-lg transition hover:bg-white/25 md:left-4"
            onClick={() => go(-1)}
            aria-label="Previous photo"
          >
            <span className="material-symbols-outlined text-[28px]">chevron_left</span>
          </button>
        )}

        <div className="flex h-full max-h-full w-full max-w-5xl items-center justify-center">
          <img
            key={current}
            src={current}
            alt={title ? `${title} photo ${safeIndex + 1}` : `Photo ${safeIndex + 1}`}
            className="max-h-[min(70vh,calc(100%-1rem))] max-w-full select-none rounded-lg object-contain shadow-2xl"
            draggable={false}
          />
        </div>

        {count > 1 && (
          <button
            type="button"
            className="absolute right-2 z-10 flex h-11 w-11 items-center justify-center rounded-full bg-white/15 text-white shadow-lg transition hover:bg-white/25 md:right-4"
            onClick={() => go(1)}
            aria-label="Next photo"
          >
            <span className="material-symbols-outlined text-[28px]">chevron_right</span>
          </button>
        )}
      </div>

      {/* Bottom thumbnail strip — preview next/previous */}
      {count > 1 && (
        <div
          className="shrink-0 border-t border-white/10 bg-black/40 px-3 py-3 md:px-6 md:py-4"
          onClick={(e) => e.stopPropagation()}
        >
          <div
            ref={thumbRowRef}
            className="mx-auto flex max-w-5xl gap-2 overflow-x-auto pb-1 scrollbar-thin"
            role="listbox"
            aria-label="Photo previews"
          >
            {images.map((src, i) => {
              const active = i === safeIndex;
              return (
                <button
                  key={`${src}-thumb-${i}`}
                  type="button"
                  data-thumb-index={i}
                  role="option"
                  aria-selected={active}
                  onClick={() => onIndexChange(i)}
                  className={`relative h-16 w-20 shrink-0 overflow-hidden rounded-lg transition ring-2 md:h-20 md:w-28 ${
                    active
                      ? "ring-white opacity-100 scale-100"
                      : "ring-transparent opacity-55 hover:opacity-90"
                  }`}
                >
                  <img
                    src={src}
                    alt=""
                    className="h-full w-full object-cover"
                    draggable={false}
                  />
                  {active && (
                    <span className="pointer-events-none absolute inset-0 rounded-lg ring-2 ring-inset ring-primary/80" />
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
