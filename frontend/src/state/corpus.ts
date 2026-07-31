/** Corpus size from GET /api/health — drives search loader copy. */

export type CorpusStats = {
  businessCount: number | null;
  label: string;
  source: string;
};

let corpus: CorpusStats = {
  businessCount: null,
  label: "businesses",
  source: "none",
};

const listeners = new Set<() => void>();

export function getCorpusStats(): CorpusStats {
  return corpus;
}

export function setCorpusFromHealth(health: {
  business_count?: number | null;
  corpus_label?: string | null;
  corpus_source?: string | null;
}): void {
  const next: CorpusStats = {
    businessCount:
      typeof health.business_count === "number" && Number.isFinite(health.business_count)
        ? Math.max(0, Math.floor(health.business_count))
        : null,
    label: (health.corpus_label || "businesses").trim() || "businesses",
    source: health.corpus_source || "none",
  };
  const changed =
    next.businessCount !== corpus.businessCount ||
    next.label !== corpus.label ||
    next.source !== corpus.source;
  corpus = next;
  if (changed) {
    listeners.forEach((fn) => fn());
  }
}

export function subscribeCorpus(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** e.g. Searching 161,237 businesses… */
export function searchLoadingLabel(verb = "Searching"): string {
  const { businessCount, label } = corpus;
  if (businessCount != null && businessCount > 0) {
    return `${verb} ${businessCount.toLocaleString()} ${label}…`;
  }
  return `${verb} with Zeus…`;
}
