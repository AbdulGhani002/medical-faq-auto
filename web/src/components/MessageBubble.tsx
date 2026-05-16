import type { Msg } from "@/lib/types";
import ScoreBreakdownPopover from "./ScoreBreakdown";

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
            {msg.text}
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

  return (
    <div className="fade-in flex justify-start">
      <div className="max-w-[86%] rounded-2xl rounded-bl-md bg-white border border-stone-200 px-4 py-3 shadow-card">
        <div className="flex items-center gap-2 mb-1.5 text-[10px] tracking-[0.14em] uppercase text-stone-400">
          <span className={"inline-block h-1.5 w-1.5 rounded-full " + dotColor} />
          {label}
        </div>

        {hasCorrections && (
          <div className="mb-2 flex flex-wrap gap-1.5">
            {msg.spell_corrections!.map((c, i) => (
              <span key={i} className="pill !text-[10px] !py-0.5">
                spell: {c.original} &rarr; {c.fixed}
              </span>
            ))}
          </div>
        )}

        <p className="text-[14px] leading-relaxed text-stone-900 whitespace-pre-line">
          {msg.text}
        </p>

        <div className="mt-2 flex items-center justify-between gap-3 text-[10px] text-stone-500">
          <span>{time}</span>
          <div className="flex items-center gap-2">
            <ScoreBreakdownPopover
              breakdown={msg.score_breakdown}
              corrections={msg.spell_corrections}
              addedTerms={msg.added_terms}
            />
            {msg.confidence !== undefined && (
              <span title="Blended TF-IDF + BM25 score" className="pill !py-0.5 !text-[10px]">
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

        {msg.alternatives && msg.alternatives.length > 0 && (
          <div className="mt-3 pt-3 border-t border-stone-200">
            <p className="text-[10px] uppercase tracking-[0.14em] text-stone-500 mb-2">
              You might also be asking
            </p>
            <div className="flex flex-col gap-1.5">
              {msg.alternatives.map((a) => (
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
      </div>
    </div>
  );
}
