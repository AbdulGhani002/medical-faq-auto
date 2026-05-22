"use client";
import { useEffect, useState } from "react";
import { analyzeText } from "@/lib/api";
import type { Entity, NLPAnalysis } from "@/lib/types";

const SAMPLES = [
  "I have crushing chest pain and my left arm is numb",
  "do i need to fast before my mri scan tomorrow",
  "my knee hurts a lot after running, really worried",
  "sar mein dard ho raha hai aaj subah se",
  "no chest pain right now, only feeling tired",
  "what is angina and how do you treat it",
];

const LABEL_COLORS: Record<string, string> = {
  BODY: "bg-rose-100 text-rose-800 border-rose-200",
  SYMPTOM: "bg-amber-100 text-amber-800 border-amber-200",
  CONDITION: "bg-violet-100 text-violet-800 border-violet-200",
  DRUG: "bg-sky-100 text-sky-800 border-sky-200",
  PROCEDURE: "bg-emerald-100 text-emerald-800 border-emerald-200",
  TIME: "bg-stone-100 text-stone-700 border-stone-300",
  PERSON: "bg-fuchsia-100 text-fuchsia-800 border-fuchsia-200",
  NUMBER: "bg-stone-100 text-stone-700 border-stone-300",
};

function renderWithEntities(text: string, ents: Entity[]) {
  if (!ents.length) return <span>{text}</span>;
  const sorted = [...ents].sort((a, b) => a.start - b.start);
  const out: React.ReactNode[] = [];
  let cursor = 0;
  sorted.forEach((e, i) => {
    if (e.start > cursor) {
      out.push(<span key={`t-${i}`}>{text.slice(cursor, e.start)}</span>);
    }
    out.push(
      <span
        key={`e-${i}`}
        className={
          "inline-flex items-baseline gap-1 mx-0.5 px-1.5 py-0.5 rounded border align-baseline " +
          (LABEL_COLORS[e.label] || "")
        }
      >
        <span>{text.slice(e.start, e.end)}</span>
        <span className="text-[9px] uppercase tracking-[0.14em] opacity-70">
          {e.label}
        </span>
      </span>
    );
    cursor = e.end;
  });
  if (cursor < text.length) {
    out.push(<span key="t-end">{text.slice(cursor)}</span>);
  }
  return <>{out}</>;
}

export default function PlaygroundClient() {
  const [text, setText] = useState(SAMPLES[0]);
  const [analysis, setAnalysis] = useState<NLPAnalysis | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancel = false;
    const t = setTimeout(async () => {
      if (!text.trim()) {
        setAnalysis(null);
        return;
      }
      const t0 = performance.now();
      try {
        const r = await analyzeText(text);
        if (!cancel) {
          setAnalysis(r);
          setLatency(performance.now() - t0);
          setError(null);
        }
      } catch (e) {
        if (!cancel) setError("Backend unreachable.");
      }
    }, 250);
    return () => {
      cancel = true;
      clearTimeout(t);
    };
  }, [text]);

  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-stone-200 bg-white p-4 shadow-card">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
          className="w-full resize-none rounded-lg border border-stone-200 px-3 py-2 text-[14px] focus:outline-none focus:border-stone-900"
          placeholder="Type a medical question..."
        />
        <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap gap-1.5">
            {SAMPLES.map((s, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setText(s)}
                className="text-[11px] border border-stone-200 hover:border-stone-900 rounded-full px-2.5 py-1 text-stone-700 transition"
              >
                {s.slice(0, 32) + (s.length > 32 ? "…" : "")}
              </button>
            ))}
          </div>
          {latency !== null && (
            <span className="pill !text-[10px] !py-0.5">
              {latency.toFixed(0)} ms round-trip
            </span>
          )}
        </div>
        {error && (
          <p className="mt-2 text-[12px] text-rose-700">{error}</p>
        )}
      </div>

      {analysis && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          <Card title="Inline entity rendering">
            <p className="text-[14px] leading-relaxed">
              {renderWithEntities(analysis.raw_text, analysis.entities)}
            </p>
          </Card>

          <Card title="Naive Bayes intent">
            <div className="flex flex-wrap gap-2">
              <span className="pill !bg-stone-900 !text-stone-50 !border-stone-900">
                {analysis.intent.label} ·{" "}
                {(analysis.intent.confidence * 100).toFixed(0)}%
              </span>
              {analysis.intent.top3.slice(1).map(([l, p], i) => (
                <span key={i} className="pill">
                  {l} · {(p * 100).toFixed(0)}%
                </span>
              ))}
            </div>
            <p className="mt-2 text-[11px] text-stone-500">
              Multinomial Naive Bayes over TF-IDF (1-2 grams), trained on
              ~120 examples from <code>data/intents.jsonl</code>.
            </p>
          </Card>

          <Card title="Sentiment (lexicon + negation)">
            <div className="flex items-baseline gap-3">
              <span
                className={
                  "text-2xl font-semibold " +
                  (analysis.sentiment.label === "negative"
                    ? "text-rose-700"
                    : analysis.sentiment.label === "positive"
                    ? "text-emerald-700"
                    : "text-stone-700")
                }
              >
                {analysis.sentiment.compound.toFixed(2)}
              </span>
              <span className="pill">{analysis.sentiment.label}</span>
            </div>
            <div className="mt-2 flex flex-wrap gap-1">
              {analysis.sentiment.negatives.map((t, i) => (
                <span
                  key={i}
                  className="pill !text-[10px] !text-rose-700 !py-0.5"
                >
                  -{t}
                </span>
              ))}
              {analysis.sentiment.positives.map((t, i) => (
                <span
                  key={i}
                  className="pill !text-[10px] !text-emerald-700 !py-0.5"
                >
                  +{t}
                </span>
              ))}
            </div>
          </Card>

          <Card title="Triage / urgency">
            <div className="flex items-baseline gap-3">
              <span
                className={
                  "text-2xl font-semibold " +
                  (analysis.triage.level === 3
                    ? "text-red-700"
                    : analysis.triage.level === 2
                    ? "text-amber-700"
                    : analysis.triage.level === 1
                    ? "text-stone-700"
                    : "text-stone-400")
                }
              >
                Level {analysis.triage.level}
              </span>
              {analysis.triage.cues.length > 0 && (
                <span className="text-[11px] text-stone-500">
                  cues: {analysis.triage.cues.join(", ")}
                </span>
              )}
            </div>
          </Card>

          <Card title="POS tags">
            <div className="flex flex-wrap gap-2 text-[13px] font-mono">
              {analysis.pos.map((p, i) => (
                <span key={i}>
                  <span className="text-stone-800">{p.text}</span>
                  <span className="text-stone-400">/{p.tag}</span>
                </span>
              ))}
            </div>
          </Card>

          <Card title="Lemmas">
            <div className="flex flex-wrap gap-1.5">
              {analysis.tokens.map((t, i) => (
                <span key={i} className="pill !text-[11px] !py-0.5">
                  <span className="text-stone-500">{t}</span>
                  <span className="text-stone-400">→</span>
                  <span className="text-stone-900 font-medium">
                    {analysis.lemmas[i]}
                  </span>
                </span>
              ))}
            </div>
          </Card>

          <Card title="Keywords (TextRank)" wide>
            <div className="flex flex-wrap gap-2">
              {analysis.keywords.map((k, i) => (
                <span
                  key={i}
                  className="pill"
                  style={{
                    fontSize: 11 + Math.min(8, k.score * 4) + "px",
                  }}
                >
                  {k.text}
                </span>
              ))}
              {analysis.keywords.length === 0 && (
                <span className="text-[12px] text-stone-400">
                  No keywords (input too short)
                </span>
              )}
            </div>
          </Card>

          <Card title="Negation scope" wide>
            {analysis.negations.length === 0 ? (
              <span className="text-[12px] text-stone-400">
                No negation cues detected.
              </span>
            ) : (
              <div className="space-y-1.5">
                {analysis.negations.map((n, i) => (
                  <div key={i} className="text-[12px]">
                    <span className="pill !text-[10px] !py-0.5 mr-1">
                      {n.cue}
                    </span>
                    flips polarity of:{" "}
                    <span className="italic text-stone-700">
                      {n.scope.join(" ") || "(end of clause)"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card title="Question type">
            <span className="pill">{analysis.question_type}</span>
          </Card>

          <Card title="Slots filled">
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(analysis.slots)
                .filter(([k, v]) => k !== "entities" && v)
                .map(([k, v]) => (
                  <span key={k} className="pill !text-[11px] !py-0.5">
                    {k}: <b className="ml-1">{String(v)}</b>
                  </span>
                ))}
              {Object.entries(analysis.slots).every(
                ([k, v]) => k === "entities" || !v
              ) && (
                <span className="text-[12px] text-stone-400">
                  No slots filled.
                </span>
              )}
            </div>
          </Card>

          <Card title="LM perplexity (Kneser-Ney trigram)">
            {typeof analysis.lm_perplexity === "number" ? (
              <div className="flex items-baseline gap-3">
                <span className="text-2xl font-semibold tabular-nums">
                  {analysis.lm_perplexity.toFixed(2)}
                </span>
                <span className="text-[11px] text-stone-500">
                  lower = more fluent / more in-domain
                </span>
              </div>
            ) : (
              <span className="text-[12px] text-stone-400">unavailable</span>
            )}
          </Card>

          <Card title="Noun + verb phrases (shallow parsing)" wide>
            <div className="flex flex-wrap gap-2 mb-2">
              {(analysis.chunks?.noun_phrases || []).map((c, i) => (
                <span
                  key={"np" + i}
                  className="pill !text-[11px] !py-0.5 !bg-emerald-50 !text-emerald-800 !border-emerald-200"
                >
                  NP · {c.text}
                </span>
              ))}
            </div>
            <div className="flex flex-wrap gap-2">
              {(analysis.chunks?.verb_phrases || []).map((c, i) => (
                <span
                  key={"vp" + i}
                  className="pill !text-[11px] !py-0.5 !bg-sky-50 !text-sky-800 !border-sky-200"
                >
                  VP · {c.text}
                </span>
              ))}
            </div>
            {!(analysis.chunks?.noun_phrases?.length) &&
              !(analysis.chunks?.verb_phrases?.length) && (
                <span className="text-[12px] text-stone-400">
                  No chunks (input too short).
                </span>
              )}
          </Card>

          <Card title="Knowledge-graph triples (subject · predicate · object)" wide>
            {(analysis.triples || []).length === 0 ? (
              <span className="text-[12px] text-stone-400">
                No triples extracted from this sentence.
              </span>
            ) : (
              <div className="space-y-2">
                {(analysis.triples || []).map((t, i) => (
                  <div
                    key={i}
                    className="rounded-lg border border-stone-200 bg-stone-50 px-3 py-2"
                  >
                    <div className="flex items-center gap-2 text-[13px]">
                      <span className="font-semibold text-stone-900">
                        {t.subject}
                      </span>
                      <span className="text-stone-400">→</span>
                      <span
                        className={
                          "font-mono " +
                          (t.negated ? "text-rose-700" : "text-stone-700")
                        }
                      >
                        {t.negated ? "NOT " : ""}
                        {t.predicate}
                      </span>
                      <span className="text-stone-400">→</span>
                      <span className="font-semibold text-stone-900">
                        {t.object}
                      </span>
                    </div>
                    <p className="mt-1 text-[11px] text-stone-500 italic">
                      from: {t.sentence}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {(analysis.pos_hmm && analysis.pos_hmm.length > 0) && (
            <Card title="POS — HMM vs lexicon (only differences shown)" wide>
              <div className="flex flex-wrap gap-2 text-[12px] font-mono">
                {analysis.pos.map((p, i) => {
                  const hmm = analysis.pos_hmm![i];
                  if (!hmm || hmm.tag === p.tag) return null;
                  return (
                    <span
                      key={i}
                      className="pill !text-[10px] !py-0.5 !bg-amber-50 !text-amber-800 !border-amber-200"
                    >
                      {p.text}:{" "}
                      <span className="line-through opacity-60">{p.tag}</span>
                      {" → "}
                      <b>{hmm.tag}</b>
                    </span>
                  );
                })}
                {!analysis.pos.some(
                  (p, i) => analysis.pos_hmm![i]?.tag !== p.tag
                ) && (
                  <span className="text-stone-400">
                    HMM agrees with the lexicon tagger.
                  </span>
                )}
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

function Card({
  title,
  children,
  wide,
}: {
  title: string;
  children: React.ReactNode;
  wide?: boolean;
}) {
  return (
    <div
      className={
        "rounded-2xl border border-stone-200 bg-white p-4 shadow-card " +
        (wide ? "lg:col-span-2" : "")
      }
    >
      <p className="text-[10px] uppercase tracking-[0.16em] text-stone-500 mb-2">
        {title}
      </p>
      {children}
    </div>
  );
}
