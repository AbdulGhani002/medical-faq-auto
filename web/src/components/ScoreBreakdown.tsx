"use client";
import { useState } from "react";
import type { ScoreBreakdown as Sb, SpellCorrection } from "@/lib/types";

function bar(value: number) {
  const pct = Math.max(0, Math.min(100, value * 100));
  return (
    <div className="h-1.5 w-24 bg-stone-100 rounded-full overflow-hidden">
      <div className="h-full bg-stone-700" style={{ width: `${pct}%` }} />
    </div>
  );
}

export default function ScoreBreakdownPopover({
  breakdown,
  corrections,
  addedTerms,
}: {
  breakdown?: Sb | null;
  corrections?: SpellCorrection[];
  addedTerms?: string[];
}) {
  const [open, setOpen] = useState(false);
  if (!breakdown && !(corrections?.length) && !(addedTerms?.length)) return null;

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="text-[10px] tracking-[0.14em] uppercase text-stone-500 hover:text-stone-900 underline-offset-2 hover:underline"
        aria-expanded={open}
      >
        Why this match?
      </button>
      {open && (
        <div className="absolute right-0 z-30 mt-2 w-72 rounded-xl border border-stone-200 bg-white shadow-card p-4 text-[11px]">
          {breakdown && (
            <>
              <p className="text-[10px] uppercase tracking-[0.14em] text-stone-500 mb-2">
                Matched FAQ
              </p>
              <p className="text-stone-800 mb-3 leading-snug">
                {breakdown.matched_question}
              </p>
              <p className="text-[10px] uppercase tracking-[0.14em] text-stone-500 mb-2">
                Per-method scores
              </p>
              <div className="space-y-1.5 mb-3">
                <Row label="TF-IDF (word)" value={breakdown.tfidf_word} />
                <Row label="TF-IDF (char)" value={breakdown.tfidf_char} />
                <Row label="BM25" value={breakdown.bm25} />
                {typeof breakdown.lsa === "number" && (
                  <Row label="LSA topic" value={breakdown.lsa} />
                )}
                <Row
                  label="Blended"
                  value={breakdown.blended}
                  bold
                />
              </div>
            </>
          )}

          {corrections && corrections.length > 0 && (
            <div className="mb-2 pt-2 border-t border-stone-200">
              <p className="text-[10px] uppercase tracking-[0.14em] text-stone-500 mb-1.5">
                Spell-corrected
              </p>
              <div className="flex flex-wrap gap-1.5">
                {corrections.map((c, i) => (
                  <span
                    key={i}
                    className="pill !text-[10px] !py-0.5"
                  >
                    {c.original} &rarr; {c.fixed}
                  </span>
                ))}
              </div>
            </div>
          )}

          {addedTerms && addedTerms.length > 0 && (
            <div className="pt-2 border-t border-stone-200">
              <p className="text-[10px] uppercase tracking-[0.14em] text-stone-500 mb-1.5">
                Pseudo-relevance terms added
              </p>
              <p className="text-stone-700 italic">{addedTerms.join(", ")}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Row({
  label, value, bold,
}: { label: string; value: number; bold?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className={"text-stone-600 " + (bold ? "font-semibold text-stone-900" : "")}>
        {label}
      </span>
      <div className="flex items-center gap-2">
        {bar(value)}
        <span className={"tabular-nums text-stone-700 " + (bold ? "font-semibold" : "")}>
          {value.toFixed(2)}
        </span>
      </div>
    </div>
  );
}
