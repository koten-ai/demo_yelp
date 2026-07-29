/** GET /api/health — includes installed kotenai-zeus-client version for chrome. */
export type HealthResponse = {
  ok: boolean;
  zeus_client_version: string;
};

export type BusinessCard = {
  name: string;
  description: string;
  image: string;
  business_id?: string;
  rating?: string;
  review_count?: string;
  categories?: string;
  price?: string;
  is_open?: string;
  hours_today?: string;
  location?: string;
  address?: string;
  city?: string;
  state?: string;
  latitude?: string;
  longitude?: string;
  url?: string;
};

export type SearchResponse = {
  chat_id: string;
  query: string;
  answer: string | Record<string, unknown>;
  structured_answer: Record<string, unknown> | null;
  structured_response: Record<string, unknown>;
  results: BusinessCard[];
  trace: Record<string, unknown>;
  tool_order: { v1: string[]; v2: string[] };
  target: string;
  api_version: string;
  mode: string;
  model: string;
  provider: string;
  zeus_connection: string;
  zeus_url: string;
  session_id: string;
  session_round: number;
  contract_status: string | null;
  /** Echo of ClientSettings.ai_process_result for this turn (0.2.1+). */
  ai_process_result?: boolean;
  error?: string;
};

export type InsightResponse = {
  business_id: string;
  business?: BusinessCard | null;
  summary: string;
  the_good: string[];
  the_bad: string[];
  best_for: string[];
  reviews: { author: string; stars: string; text: string; date: string }[];
  chat_id?: string;
  trace?: Record<string, unknown>;
  answer?: string;
  error?: string;
};

export type UiBusiness = {
  id: string;
  title: string;
  description: string;
  image: string;
  rating: number | null;
  reviewCount: string;
  categories: string;
  priceLabel: string;
  isOpen: boolean | null;
  location: string;
  latitude: number | null;
  longitude: number | null;
  raw: BusinessCard;
};
