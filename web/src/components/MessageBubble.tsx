import type { Entity, HighlightSegment, Msg } from "@/lib/types";
import NLPPanel from "./NLPPanel";
import ScoreBreakdownPopover from "./ScoreBreakdown";

function renderHighlighted(segs: HighlightSegment[]) {
  return (
    <>
      {segs.map((s, i) =>
        s.hl ? (
          <mark
            key={i}
            className="bg-amber-100 text-stone-900 rounded px-0.5"
          >
            {s.text}
          </mark>
        ) : (
          <span key={i}>{s.text}</span>
        )
      )}
    </>
  );
}

const USER_ENT_CLR: Record<string, string> = {
  BODY: "bg-rose-300/30 underline decoration-rose-300",
  SYMPTOM: "bg-amber-300/30 underline decoration-amber-300",
  CONDITION: "bg-violet-300/30 underline decoration-violet-300",
  DRUG: "bg-sky-300/30 underline decoration-sky-300",
  PROCEDURE: "bg-emerald-300/30 underline decoration-emerald-300",
  TIME: "bg-stone-400/20 underline decoration-stone-400",
  PERSON: "bg-fuchsia-300/30 underline decoration-fuchsia-300",
  NUMBER: "bg-stone-400/20",
};

function renderUserWithEntities(text: string, ents: Entity[]) {
  if (!ents.length) return <>{text}</>;
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
        title={e.label}
        className={"px-0.5 rounded " + (USER_ENT_CLR[e.label] || "")}
      >
        {text.slice(e.start, e.end)}
      </span>
    );
    cursor = e.end;
  });
  if (cursor < text.length) {
    out.push(<span key="t-end">{text.slice(cursor)}</span>);
  }
  return <>{out}</>;
}

export default function MessageBubble({
  msg,
  onAltClick,
}: {
  msg: Msg;
  onAltClick?: (text: string) => void;
}) {
  const isUser = msg.role === "user";
  const time = msg.ts
    ? new Date(msg.ts).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      })
    : "";

  if (isUser) {
    return (
      <div className="fade-in flex justify-end">
        <div className="max-w-[78%] rounded-2xl rounded-br-md bg-stone-950 text-stone-50 px-4 py-3 shadow-card">
          <p className="text-[14px] leading-snug whitespace-pre-line">
            {msg.user_entities && msg.user_entities.length > 0
              ? renderUserWithEntities(msg.text, msg.user_entities)
              : msg.text}
          </p>
          <div className="mt-1.5 text-[10px] text-stone-300 text-right">
            {time}
          </div>
        </div>
      </div>
    );
  }

  const bucket = msg.bucket || "confident";
  const label =
    msg.intent && msg.intent !== "question"
      ? msg.intent === "greeting"
        ? "Greeting"
        : msg.intent === "thanks"
        ? "Reply"
        : msg.intent === "frustration"
        ? "Sorry"
        : msg.intent === "help"
        ? "Help"
        : "Answer"
      : bucket === "best_guess"
      ? "Closest match"
      : bucket === "none"
      ? "No good match"
      : "Answer";
  const dotColor =
    bucket === "best_guess"
      ? "bg-amber-500"
      : bucket === "none"
      ? "bg-stone-400"
      : "bg-emerald-600";

  const hasCorrections = (msg.spell_corrections?.length ?? 0) > 0;
  const hasAddedTerms = (msg.added_terms?.length ?? 0) > 0;
  const triageLvl = msg.dialog?.triage_level ?? 0;
  const disambig = msg.dialog?.disambiguation;
  const coref = msg.dialog?.coref ?? [];

  // Split prefix (banner + opener) from the matched FAQ body using \n\n.
  let prefix: string | null = null;
  let body: string = msg.text;
  if (msg.highlighted && msg.highlighted.length > 0 && msg.matched_question) {
    // The highlighter operates on the FAQ answer only; everything before
    // the body must be the prefix injected by the dialog manager.
    const joined = msg.highlighted.map((s) => s.text).join("");
    const idx = msg.text.indexOf(joined);
    if (idx > 0) {
      prefix = msg.text.slice(0, idx).trim();
      body = joined;
    }
  }

  return (
    <div className="fade-in flex justify-start">
      <div className="max-w-[92%] rounded-2xl rounded-bl-md bg-white border border-stone-200 px-4 py-3 shadow-card w-full">
        <div className="flex items-center gap-2 mb-1.5 text-[10px] tracking-[0.14em] uppercase text-stone-400">
          <span className={"inline-block h-1.5 w-1.5 rounded-full " + dotColor} />
          {label}
          {msg.dialog?.active_topic && (
            <span className="ml-auto pill !py-0.5 !text-[10px] !text-stone-500">
              topic: {msg.dialog.active_topic}
            </span>
          )}
        </div>

        {triageLvl >= 2 && (
          <div
            className={
              "mb-2 rounded-lg border px-3 py-2 text-[12px] " +
              (triageLvl === 3
                ? "border-red-300 bg-red-50 text-red-800"
                : "border-amber-300 bg-amber-50 text-amber-900")
            }
          >
            <p className="font-semibold mb-0.5">
              {triageLvl === 3 ? "Emergency cues detected" : "Please review today"}
            </p>
            <p className="leading-snug">
              {msg.dialog?.banner ||
                "This sounds time-sensitive. Use the answer as guidance only."}
            </p>
          </div>
        )}

        {coref.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-1.5">
            {coref.map((c, i) => (
              <span key={i} className="pill !text-[10px] !py-0.5">
                coref: {c.original} → {c.replacement}
              </span>
            ))}
          </div>
        )}

        {hasCorrections && (
          <div className="mb-2 flex flex-wrap gap-1.5">
            {msg.spell_corrections!.map((c, i) => (
              <span key={i} className="pill !text-[10px] !py-0.5">
                spell: {c.original} &rarr; {c.fixed}
              </span>
            ))}
          </div>
        )}

        {prefix && (
          <p className="text-[13px] text-stone-600 italic leading-relaxed mb-2 whitespace-pre-line">
            {prefix}
          </p>
        )}

        <p className="text-[14px] leading-relaxed text-stone-900 whitespace-pre-line">
          {msg.highlighted && msg.highlighted.length > 0
            ? renderHighlighted(msg.highlighted)
            : body}
        </p>

        {disambig && disambig.length > 0 && (
          <div className="mt-3 rounded-lg border border-stone-200 bg-stone-50 p-3">
            <p className="text-[10px] uppercase tracking-[0.14em] text-stone-500 mb-2">
              Did you mean one of these?
            </p>
            <div className="flex flex-col gap-1.5">
              {disambig.map((a) => (
                <button
                  key={a.id}
                  type="button"
                  onClick={() => onAltClick?.(a.question)}
                  className="text-left text-[12px] text-stone-700 hover:text-stone-950 hover:bg-white px-2 py-1.5 rounded-md border border-stone-200 transition"
                >
                  {a.question}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="mt-2 flex items-center justify-between gap-3 text-[10px] text-stone-500">
          <span>{time}</span>
          <div className="flex items-center gap-2">
            <ScoreBreakdownPopover
              breakdown={msg.score_breakdown}
              corrections={msg.spell_corrections}
              addedTerms={msg.added_terms}
            />
            {msg.confidence !== undefined && (
              <span title="Blended TF-IDF (word + char) + BM25 + LSA + PPMI score" className="pill !py-0.5 !text-[10px]">
                match&nbsp;{(msg.confidence * 100).toFixed(0)}%
              </span>
            )}
          </div>
        </div>

        {hasAddedTerms && (
          <div className="mt-2 pt-2 border-t border-stone-200 text-[10px] text-stone-500">
            <span className="uppercase tracking-[0.14em] mr-2">Expanded with</span>
            <span className="italic">{msg.added_terms!.join(", ")}</span>
          </div>
        )}

        {msg.alternatives && msg.alternatives.length > 0 && !disambig && (
          <div className="mt-3 pt-3 border-t border-stone-200">
            <p className="text-[10px] uppercase tracking-[0.14em] text-stone-500 mb-2">
              You might also be asking
            </p>
            <div className="flex flex-col gap-1.5">
              {msg.alternatives.slice(0, 3).map((a) => (
                <button
                  key={a.id}
                  type="button"
                  onClick={() => onAltClick?.(a.question)}
                  className="text-left text-[12px] text-stone-700 hover:text-stone-950 hover:bg-stone-50 px-2 py-1.5 rounded-md border border-stone-200 transition"
                >
                  {a.question}
                </button>
              ))}
            </div>
          </div>
        )}

        {msg.nlp && <NLPPanel nlp={msg.nlp} />}
      </div>
    </div>
  );
}
