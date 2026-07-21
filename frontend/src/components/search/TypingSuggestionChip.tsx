import { useEffect, useRef, useState } from "react";

export const DEFAULT_SUGGESTIONS = [
  "Best sushi for a first date",
  "Quiet parks with wifi",
  "Cozy cafe for working near downtown",
  "Best hiking trails with views",
] as const;

type Props = {
  suggestions?: readonly string[];
  onSelect: (suggestion: string) => void;
  label?: string;
  /** ms per character while typing */
  typeMs?: number;
  /** ms per character while deleting */
  deleteMs?: number;
  /** pause after a full phrase before deleting */
  holdMs?: number;
  /** pause after delete before next phrase */
  betweenMs?: number;
};

/**
 * Stitch "Try asking" chip: cycles suggestions with a typewriter + blink cursor.
 * Click fills the parent search with the current (or fully typed) suggestion.
 */
export default function TypingSuggestionChip({
  suggestions = DEFAULT_SUGGESTIONS,
  onSelect,
  label = "Try asking:",
  typeMs = 100,
  deleteMs = 50,
  holdMs = 3000,
  betweenMs = 500,
}: Props) {
  const list = suggestions.length > 0 ? suggestions : DEFAULT_SUGGESTIONS;
  const [index, setIndex] = useState(0);
  const [text, setText] = useState("");
  const [deleting, setDeleting] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const indexRef = useRef(0);
  const textRef = useRef("");
  const deletingRef = useRef(false);

  useEffect(() => {
    indexRef.current = index;
  }, [index]);

  useEffect(() => {
    textRef.current = text;
  }, [text]);

  useEffect(() => {
    deletingRef.current = deleting;
  }, [deleting]);

  useEffect(() => {
    let cancelled = false;

    const clear = () => {
      if (timerRef.current != null) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };

    const tick = () => {
      if (cancelled) return;
      const full = list[indexRef.current] ?? "";
      const current = textRef.current;
      const isDel = deletingRef.current;

      if (!isDel) {
        if (current.length < full.length) {
          const next = full.slice(0, current.length + 1);
          textRef.current = next;
          setText(next);
          timerRef.current = setTimeout(tick, typeMs);
          return;
        }
        // Full phrase — hold, then delete
        timerRef.current = setTimeout(() => {
          if (cancelled) return;
          deletingRef.current = true;
          setDeleting(true);
          tick();
        }, holdMs);
        return;
      }

      if (current.length > 0) {
        const next = current.slice(0, -1);
        textRef.current = next;
        setText(next);
        timerRef.current = setTimeout(tick, deleteMs);
        return;
      }

      // Empty — advance phrase
      timerRef.current = setTimeout(() => {
        if (cancelled) return;
        const nextIdx = (indexRef.current + 1) % list.length;
        indexRef.current = nextIdx;
        setIndex(nextIdx);
        deletingRef.current = false;
        setDeleting(false);
        tick();
      }, betweenMs);
    };

    // Reset when suggestion list identity/length changes
    clear();
    indexRef.current = 0;
    textRef.current = "";
    deletingRef.current = false;
    setIndex(0);
    setText("");
    setDeleting(false);
    timerRef.current = setTimeout(tick, typeMs);

    return () => {
      cancelled = true;
      clear();
    };
  }, [list, typeMs, deleteMs, holdMs, betweenMs]);

  const currentFull = list[index] ?? "";

  return (
    <div className="flex flex-wrap justify-center items-center gap-2 text-sm min-h-8">
      <span className="text-[10px] font-mono uppercase tracking-widest text-outline">
        {label}
      </span>
      <button
        type="button"
        className="font-normal text-sm text-primary hover:underline bg-surface-container px-3 py-1 rounded
          inline-flex items-center min-w-[200px] justify-center h-8 transition-all duration-200"
        onClick={() => onSelect(currentFull)}
        aria-label={`Use suggestion: ${currentFull}`}
      >
        <span className="typing-cursor">{text}</span>
      </button>
    </div>
  );
}
