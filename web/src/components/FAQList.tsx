"use client";
import { useEffect, useMemo, useState } from "react";
import { fetchFAQs } from "@/lib/api";
import type { FAQItem } from "@/lib/types";

export default function FAQList({ specialty }: { specialty: string }) {
  const [items, setItems] = useState<FAQItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    setLoading(true);
    fetchFAQs(specialty)
      .then(setItems)
      .catch(() => setErr("Failed to load FAQs."))
      .finally(() => setLoading(false));
  }, [specialty]);

  const filtered = useMemo(() => {
    if (!query.trim()) return items;
    const q = query.toLowerCase();
    return items.filter(
      (it) =>
        it.question.toLowerCase().includes(q) ||
        it.answer.toLowerCase().includes(q)
    );
  }, [items, query]);

  if (loading) {
    return (
      <div className="rounded-2xl border border-stone-200 bg-white p-6 flex items-center gap-2 text-stone-500">
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="typing-dot" />
        <span className="ml-2 text-sm">Loading FAQs...</span>
      </div>
    );
  }
  if (err) {
    return (
      <p className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {err}
      </p>
    );
  }
  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-stone-200 bg-white p-8 text-center">
        <p className="text-stone-700 font-medium mb-1">Nothing here yet</p>
        <p className="text-sm text-stone-500">
          No FAQs have been approved for this specialty yet.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="relative mb-5">
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden
          className="absolute left-3.5 top-1/2 -translate-y-1/2 text-stone-400"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="m21 21-4.3-4.3" />
        </svg>
        <input
          type="search"
          placeholder={`Search ${items.length} FAQs...`}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 rounded-full border border-stone-200 bg-white focus:outline-none focus:border-stone-900 text-sm"
        />
      </div>

      {filtered.length === 0 && (
        <p className="text-sm text-stone-500 mb-4">
          No FAQs match &ldquo;{query}&rdquo;.
        </p>
      )}

      <div className="space-y-3">
        {filtered.map((it) => (
          <details
            key={it.id}
            className="group rounded-2xl border border-stone-200 bg-white shadow-card p-5 transition open:shadow-card-hover"
          >
            <summary className="cursor-pointer list-none flex items-center justify-between gap-4">
              <span className="font-medium text-stone-900">
                {it.question}
              </span>
              <span className="flex items-center gap-2 shrink-0">
                <span className="pill">{it.count} asked</span>
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="text-stone-400 group-open:rotate-180 transition-transform"
                  aria-hidden
                >
                  <path d="m6 9 6 6 6-6" />
                </svg>
              </span>
            </summary>
            <p className="mt-3 text-[14px] text-stone-700 leading-relaxed whitespace-pre-line">
              {it.answer}
            </p>
          </details>
        ))}
      </div>
    </div>
  );
}
