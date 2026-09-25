/** Catalog size for chrome and search-loader copy. */
export type HealthResponse = {
  ok: boolean;
  app_version?: string;
  business_count?: number | null;
  corpus_label?: string;
  corpus_source?: string;
};

export type BusinessCard = {
  name: string;
  description: string;
  image: string;
  /** Optional gallery under /business-images/<id>/. */
  images?: string[];
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
  /** Typeahead extras. */
  subtitle?: string;
  source?: string;
};

export type SuggestResponse = {
  query: string;
  results: BusinessCard[];
  count: number;
  source: string;
  error?: string | null;
};

export type SearchResponse = {
  chat_id: string;
  query: string;
  answer: string;
  structured_answer: { context?: string; tip?: string } | null;
  results: BusinessCard[];
};

export type ReviewItem = {
  author: string;
  stars: string;
  text: string;
  date: string;
  review_id?: string;
  user_id?: string;
  user_review_count?: string;
  user_average_stars?: string;
  yelping_since?: string;
};

export type ReviewsResponse = {
  business_id: string;
  reviews: ReviewItem[];
  count: number;
  source?: string;
  error?: string | null;
};

export type InsightResponse = {
  business_id: string;
  business?: BusinessCard | null;
  summary: string;
  the_good: string[];
  the_bad: string[];
  best_for: string[];
  reviews: ReviewItem[];
  error?: string;
};

export type UiBusiness = {
  id: string;
  title: string;
  description: string;
  image: string;
  images: string[];
  rating: number | null;
  reviewCount: string;
  categories: string;
  priceLabel: string;
  isOpen: boolean | null;
  hoursToday: string;
  location: string;
  address: string;
  city: string;
  state: string;
  url: string;
  latitude: number | null;
  longitude: number | null;
  raw: BusinessCard;
};
