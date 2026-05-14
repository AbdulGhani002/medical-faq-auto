"use client";
import { useEffect, useState } from "react";
import { fetchFAQs } from "@/lib/api";
import type { FAQItem } from "@/lib/types";

export default function FAQList({ specialty }: { specialty: string }) {
  const [items, setItems] = useState<FAQItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchFAQs(specialty)
      .then(setItems)
      .catch(() => setErr("Failed to load FAQs."))
      .finally(() => setLoading(false));
  }, [specialty]);

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (err) return <p className="text-red-600 text-sm">{err}</p>;
  if (items.length === 0) {
    return (
      <p className="text-gray-500">
        No FAQs yet. They appear once the pipeline clusters enough chats.
      </p>
    );
  }
  return (
    <div className="space-y-3">
      {items.map((it) => (
        <details
          key={it.id}
          className="border border-gray-200 rounded-md p-3"
        >
          <summary className="cursor-pointer font-medium">
            {it.question}
          </summary>
          <p className="mt-2 text-gray-700 text-sm whitespace-pre-line">
            {it.answer}
          </p>
          <p className="mt-2 text-xs text-gray-400">
            Asked {it.count} times
          </p>
        </details>
      ))}
    </div>
  );
}
