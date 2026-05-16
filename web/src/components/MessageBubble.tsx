import type { Msg } from "@/lib/types";

export default function MessageBubble({ msg }: { msg: Msg }) {
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

  return (
    <div className="fade-in flex justify-start">
      <div className="max-w-[82%] rounded-2xl rounded-bl-md bg-white border border-stone-200 px-4 py-3 shadow-card">
        <div className="flex items-center gap-2 mb-1.5 text-[10px] tracking-[0.14em] uppercase text-stone-400">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-stone-950" />
          MedFAQ
        </div>
        <p className="text-[14px] leading-relaxed text-stone-900 whitespace-pre-line">
          {msg.text}
        </p>
        <div className="mt-2 flex items-center justify-between text-[10px] text-stone-500">
          <span>{time}</span>
          {msg.confidence !== undefined && (
            <span title="BM25 match strength" className="pill !py-0.5 !text-[10px]">
              match&nbsp;{(msg.confidence * 100).toFixed(0)}%
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
