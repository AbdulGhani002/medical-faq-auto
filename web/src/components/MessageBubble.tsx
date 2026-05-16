import type { Msg } from "@/lib/types";

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
    bucket === "best_guess"
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

  return (
    <div className="fade-in flex justify-start">
      <div className="max-w-[85%] rounded-2xl rounded-bl-md bg-white border border-stone-200 px-4 py-3 shadow-card">
        <div className="flex items-center gap-2 mb-1.5 text-[10px] tracking-[0.14em] uppercase text-stone-400">
          <span className={"inline-block h-1.5 w-1.5 rounded-full " + dotColor} />
          {label}
        </div>
        <p className="text-[14px] leading-relaxed text-stone-900 whitespace-pre-line">
          {msg.text}
        </p>
        <div className="mt-2 flex items-center justify-between text-[10px] text-stone-500">
          <span>{time}</span>
          {msg.confidence !== undefined && (
            <span title="Hybrid TF-IDF + BM25 score" className="pill !py-0.5 !text-[10px]">
              match&nbsp;{(msg.confidence * 100).toFixed(0)}%
            </span>
          )}
        </div>

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
