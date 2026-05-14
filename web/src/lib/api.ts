import type { FAQItem, ChatResponse } from "./types";

const API =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function sendChat(
  sessionId: string,
  specialty: string,
  text: string
): Promise<ChatResponse> {
  const r = await fetch(`${API}/chat`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      specialty,
      text,
    }),
  });
  if (!r.ok) throw new Error("chat failed");
  return r.json();
}

export async function fetchFAQs(specialty: string): Promise<FAQItem[]> {
  const r = await fetch(`${API}/faq/${specialty}`);
  if (!r.ok) throw new Error("faq fetch failed");
  return r.json();
}
