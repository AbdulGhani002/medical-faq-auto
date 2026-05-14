export type FAQItem = {
  id: string;
  specialty: string;
  question: string;
  answer: string;
  count: number;
  updated_at: string;
};

export type ChatResponse = {
  answer: string;
  matched_faq_id?: string | null;
  confidence: number;
};
