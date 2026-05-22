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
  lsa?: number;
  blended: number;
  matched_question: string;
};

export type HighlightSegment = { text: string; hl: boolean };
export type CorefEdit = { original: string; replacement: string };

export type Entity = {
  text: string;
  label:
    | "BODY"
    | "SYMPTOM"
    | "CONDITION"
    | "DRUG"
    | "PROCEDURE"
    | "TIME"
    | "PERSON"
    | "NUMBER";
  start: number;
  end: number;
};

export type Keyword = { text: string; score: number };
export type Negation = { cue: string; scope: string[] };
export type Sentiment = {
  compound: number;
  label: "positive" | "negative" | "neutral";
  positives: string[];
  negatives: string[];
};
export type TriageInfo = { level: 0 | 1 | 2 | 3; cues: string[] };
export type IntentScore = {
  label: string;
  confidence: number;
  top3: [string, number][];
};
export type POSToken = { text: string; tag: string };

export type Slots = {
  body_part?: string | null;
  symptom?: string | null;
  condition?: string | null;
  drug?: string | null;
  procedure?: string | null;
  person?: string | null;
  duration?: string | null;
  frequency?: string | null;
  age?: number | null;
  entities: Entity[];
};

export type Chunk = { text: string; start_tok: number; end_tok: number };
export type Triple = {
  subject: string;
  predicate: string;
  object: string;
  negated: boolean;
  sentence: string;
};

export type NLPAnalysis = {
  raw_text: string;
  tokens: string[];
  lemmas: string[];
  pos: POSToken[];
  pos_hmm?: POSToken[];
  intent: IntentScore;
  question_type: string;
  sentiment: Sentiment;
  triage: TriageInfo;
  negations: Negation[];
  entities: Entity[];
  slots: Slots;
  keywords: Keyword[];
  chunks?: { noun_phrases: Chunk[]; verb_phrases: Chunk[] };
  triples?: Triple[];
  lm_perplexity?: number | null;
};

export type DialogMeta = {
  opener: string;
  triage_level: number;
  triage_cues: string[];
  banner: string | null;
  clarification: string | null;
  coref: CorefEdit[];
  disambiguation: Alternative[] | null;
  active_topic: string | null;
  chitchat: boolean;
};

export type ChatResponse = {
  answer: string;
  matched_faq_id?: string | null;
  matched_question?: string | null;
  confidence: number;
  alternatives?: Alternative[];
  bucket?: ChatBucket;
  intent?: string;
  spell_corrections?: SpellCorrection[];
  expanded_query?: string;
  added_terms?: string[];
  score_breakdown?: ScoreBreakdown | null;
  highlighted?: HighlightSegment[] | null;
  nlp?: NLPAnalysis | null;
  dialog?: DialogMeta;
  summary?: string | null;
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
  highlighted?: HighlightSegment[] | null;
  nlp?: NLPAnalysis | null;
  dialog?: DialogMeta | null;
  matched_question?: string | null;
  /** Inline entity annotations for the user's own message (set after the
   *  /chat call returns). */
  user_entities?: Entity[] | null;
};
