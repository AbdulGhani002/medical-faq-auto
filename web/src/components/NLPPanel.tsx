"use client";
import { useState } from "react";
import type { NLPAnalysis } from "@/lib/types";

const LABEL_COLORS: Record<string, string> = {
  BODY: "bg-rose-100 text-rose-800 border-rose-200",
  SYMPTOM: "bg-amber-100 text-amber-800 border-amber-200",
  CONDITION: "bg-violet-100 text-violet-800 border-violet-200",
  DRUG: "bg-sky-100 text-sky-800 border-sky-200",
  PROCEDURE: "bg-emerald-100 text-emerald-800 border-emerald-200",
  TIME: "bg-stone-100 text-stone-700 border-stone-200",
  PERSON: "bg-fuchsia-100 text-fuchsia-800 border-fuchsia-200",
  NUMBER: "bg-stone-100 text-stone-700 border-stone-200",
};

const POS_COLORS: Record<string, string> = {
  NN: "text-emerald-700",
  VB: "text-sky-700",
  JJ: "text-amber-700",
  RB: "text-rose-700",
  PRP: "text-stone-500",
  DT: "text-stone-400",
  IN: "text-stone-400",
  WH: "text-violet-700",
  CC: "text-stone-400",
  MD: "text-fuchsia-700",
  CD: "text-stone-700",
  UH: "text-pink-600",
};

export default function NLPPanel({ nlp }: { nlp: NLPAnalysis | null }) {
  const [open, setOpen] = useState(false);
  if (!nlp) return null;

  const senti = nlp.sentiment;
  const sentiColor =
    senti.label === "negative"
      ? "bg-rose-50 text-rose-700 border-rose-200"
      : senti.label === "positive"
      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
      : "bg-stone-50 text-stone-700 border-stone-200";

  return (
    <div className="mt-2 rounded-xl border border-stone-200 bg-stone-50/70">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full px-3 py-2 text-left flex items-center justify-between text-[11px] uppercase tracking-[0.16em] text-stone-600 hover:text-stone-900"
      >
        <span>NLP analysis</span>
        <span className="text-stone-400">{open ? "Hide" : "Show"}</span>
      </button>

      {open && (
        <div className="px-3 pb-3 pt-1 space-y-3 border-t border-stone-200">
          {/* Intent row */}
          <Row title="Intent (Naive Bayes)">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="pill !bg-stone-900 !text-stone-50 !border-stone-900">
                {nlp.intent.label} · {(nlp.intent.confidence * 100).toFixed(0)}
                %
              </span>
              {nlp.intent.top3.slice(1).map(([l, p], i) => (
                <span key={i} className="pill !py-0.5">
                  {l} · {(p * 100).toFixed(0)}%
                </span>
              ))}
            </div>
          </Row>

          {/* Question type & sentiment */}
          <Row title="Question type">
            <span className="pill">{nlp.question_type}</span>
          </Row>

          <Row title="Sentiment (lexicon + negation)">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={"pill " + sentiColor}>
                {senti.label} · {senti.compound.toFixed(2)}
              </span>
              {senti.negatives.slice(0, 4).map((n, i) => (
                <span
                  key={i}
                  className="pill !text-[10px] !py-0.5 !text-rose-700"
                >
                  -{n}
                </span>
              ))}
              {senti.positives.slice(0, 4).map((n, i) => (
                <span
                  key={i}
                  className="pill !text-[10px] !py-0.5 !text-emerald-700"
                >
                  +{n}
                </span>
              ))}
            </div>
          </Row>

          {/* Triage */}
          {nlp.triage.level > 0 && (
            <Row title="Triage / urgency">
              <div className="flex items-center gap-2 flex-wrap">
                <span
                  className={
                    "pill " +
                    (nlp.triage.level === 3
                      ? "!bg-red-100 !text-red-800 !border-red-200"
                      : nlp.triage.level === 2
                      ? "!bg-amber-100 !text-amber-800 !border-amber-200"
                      : "!bg-stone-100")
                  }
                >
                  level {nlp.triage.level}
                </span>
                {nlp.triage.cues.map((c, i) => (
                  <span key={i} className="pill !text-[10px] !py-0.5">
                    {c}
                  </span>
                ))}
              </div>
            </Row>
          )}

          {/* Entities */}
          {nlp.entities.length > 0 && (
            <Row title="Entities (medical NER)">
              <div className="flex flex-wrap gap-1.5">
                {nlp.entities.map((e, i) => (
                  <span
                    key={i}
                    className={
                      "pill !text-[10px] !py-0.5 " +
                      (LABEL_COLORS[e.label] || "")
                    }
                  >
                    {e.text} · {e.label}
                  </span>
                ))}
              </div>
            </Row>
          )}

          {/* Slots */}
          {Object.entries(nlp.slots).some(
            ([k, v]) => k !== "entities" && v
          ) && (
            <Row title="Slots filled">
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(nlp.slots)
                  .filter(([k, v]) => k !== "entities" && v)
                  .map(([k, v]) => (
                    <span key={k} className="pill !text-[10px] !py-0.5">
                      {k}: <b className="ml-1">{String(v)}</b>
                    </span>
                  ))}
              </div>
            </Row>
          )}

          {/* Negation */}
          {nlp.negations.length > 0 && (
            <Row title="Negation scope">
              <div className="flex flex-wrap gap-1.5">
                {nlp.negations.map((n, i) => (
                  <span key={i} className="pill !text-[10px] !py-0.5">
                    {n.cue} → {n.scope.join(" ") || "(end)"}
                  </span>
                ))}
              </div>
            </Row>
          )}

          {/* Keywords */}
          {nlp.keywords.length > 0 && (
            <Row title="Keywords (TextRank)">
              <div className="flex flex-wrap gap-1.5">
                {nlp.keywords.map((k, i) => (
                  <span key={i} className="pill !text-[10px] !py-0.5">
                    {k.text}
                  </span>
                ))}
              </div>
            </Row>
          )}

          {/* POS tagging */}
          <Row title="POS tags">
            <div className="flex flex-wrap gap-1">
              {nlp.pos.map((p, i) => (
                <span key={i} className="text-[11px] font-mono">
                  <span className="text-stone-800">{p.text}</span>
                  <span
                    className={
                      "ml-1 " + (POS_COLORS[p.tag] || "text-stone-400")
                    }
                  >
                    /{p.tag}
                  </span>
                </span>
              ))}
            </div>
          </Row>
        </div>
      )}
    </div>
  );
}

function Row({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-[0.16em] text-stone-500 mb-1.5">
        {title}
      </p>
      {children}
    </div>
  );
}
