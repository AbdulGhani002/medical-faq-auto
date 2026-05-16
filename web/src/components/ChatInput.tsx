"use client";
import { useEffect, useRef } from "react";

export default function ChatInput({
  value,
  onChange,
  onSend,
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled?: boolean;
}) {
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  }, [value]);

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  }

  return (
    <div className="border-t border-stone-200 bg-white p-3">
      <div className="flex items-end gap-2 rounded-2xl border border-stone-200 focus-within:border-stone-900 bg-stone-50 px-3 py-2 transition">
        <textarea
          ref={ref}
          rows={1}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Ask anything &middot; Enter to send, Shift+Enter for a new line"
          disabled={disabled}
          className="flex-1 resize-none bg-transparent text-[14px] py-1.5 focus:outline-none disabled:opacity-50 placeholder:text-stone-400"
        />
        <button
          type="button"
          onClick={onSend}
          disabled={disabled || !value.trim()}
          className="shrink-0 inline-flex items-center gap-1.5 bg-stone-950 text-white rounded-xl px-3.5 py-2 text-[13px] font-medium disabled:opacity-30 hover:bg-stone-800 transition"
        >
          Send
          <svg
            width="12"
            height="12"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden
          >
            <path d="M5 12h14M13 5l7 7-7 7" />
          </svg>
        </button>
      </div>
      <p className="mt-1.5 text-[10px] text-stone-400 px-1">
        Replies are matched from clinician-reviewed answers. No AI is used.
      </p>
    </div>
  );
}
