import { useEffect, useState } from "react";
import {
  getCorpusStats,
  searchLoadingLabel,
  subscribeCorpus,
  type CorpusStats,
} from "../state/corpus";

/** Subscribe to catalog stats filled from the sample catalog (AppShell). */
export function useCorpusStats(): CorpusStats {
  const [stats, setStats] = useState(getCorpusStats);
  useEffect(() => subscribeCorpus(() => setStats(getCorpusStats())), []);
  return stats;
}

/** Live search-loader string, e.g. \"Searching 161,237 businesses…\". */
export function useSearchLoadingLabel(verb = "Searching"): string {
  const stats = useCorpusStats();
  // Recompute when stats identity fields change.
  void stats.businessCount;
  void stats.label;
  return searchLoadingLabel(verb);
}
