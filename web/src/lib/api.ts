import type { Candidate, ChatResponse, FAQItem } from "./types";

const API =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function jfetch<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

export function sendChat(
  sessionId: string,
  specialty: string,
  text: string
): Promise<ChatResponse> {
  return jfetch<ChatResponse>(`${API}/chat`, {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      specialty,
      text,
    }),
  });
}

export function fetchFAQs(specialty: string): Promise<FAQItem[]> {
  return jfetch<FAQItem[]>(`${API}/faq/${specialty}`);
}

export function fetchCandidates(specialty: string): Promise<Candidate[]> {
  return jfetch<Candidate[]>(`${API}/admin/candidates/${specialty}`);
}

export function approveFAQ(faqId: string) {
  return jfetch<{ ok: boolean }>(`${API}/admin/approve/${faqId}`, {
    method: "POST",
  });
}

export function rejectFAQ(faqId: string) {
  return jfetch<{ ok: boolean }>(`${API}/admin/reject/${faqId}`, {
    method: "POST",
  });
}

export function editFAQ(
  faqId: string,
  body: { question?: string; answer?: string }
) {
  return jfetch<{ ok: boolean }>(`${API}/admin/edit/${faqId}`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
