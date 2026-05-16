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

export type ChatResponse = {
  answer: string;
  matched_faq_id?: string | null;
  confidence: number;
};

export type Msg = {
  role: "user" | "bot";
  text: string;
  ts?: number;
  confidence?: number;
};
