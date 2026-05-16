export type FAQItem = {
  id: string;
  specialty: string;
  question: string;
  answer: string;
  count: number;
  updated_at: string;
  approved?: boolean;
  rejected?: boolean;
};

export type Candidate = FAQItem;

export type Alternative = {
  id: string;
  question: string;
  score: number;
};

export type ChatBucket = "confident" | "best_guess" | "none";

export type SpellCorrection = {
  original: string;
  fixed: string;
};

export type ScoreBreakdown = {
  tfidf_word: number;
  tfidf_char: number;
  bm25: number;
  blended: number;
  matched_question: string;
};

export type ChatResponse = {
  answer: string;
  matched_faq_id?: string | null;
  confidence: number;
  alternatives?: Alternative[];
  bucket?: ChatBucket;
  intent?: string;
  spell_corrections?: SpellCorrection[];
  expanded_query?: string;
  added_terms?: string[];
  score_breakdown?: ScoreBreakdown | null;
};

export type Msg = {
  role: "user" | "bot";
  text: string;
  ts?: number;
  confidence?: number;
  bucket?: ChatBucket;
  alternatives?: Alternative[];
  intent?: string;
  spell_corrections?: SpellCorrection[];
  added_terms?: string[];
  score_breakdown?: ScoreBreakdown | null;
};
