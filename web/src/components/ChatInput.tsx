"use client";
import { useEffect, useRef, useState } from "react";

type SR = {
  start: () => void;
  stop: () => void;
  onresult: ((ev: any) => void) | null;
  onend: (() => void) | null;
  onerror: ((ev: any) => void) | null;
  lang: string;
  interimResults: boolean;
  continuous: boolean;
};

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
  const recogRef = useRef<SR | null>(null);
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "0px";
    el.style.height = Math.min(el.scrollHeight, 120) + "px";
  }, [value]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    setSupported(!!SpeechRecognition);
  }, []);

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  }

  function toggleVoice() {
    if (!supported) return;
    if (listening) {
      recogRef.current?.stop();
      return;
    }
    const SR =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    const r: SR = new SR();
    r.lang = "en-US";
    r.continuous = false;
    r.interimResults = false;
    r.onresult = (ev: any) => {
      const tx = ev.results?.[0]?.[0]?.transcript || "";
      if (tx) onChange((value ? value + " " : "") + tx);
    };
    r.onerror = () => setListening(false);
    r.onend = () => setListening(false);
    recogRef.current = r;
    r.start();
    setListening(true);
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
        {supported && (
          <button
            type="button"
            onClick={toggleVoice}
            disabled={disabled}
            title={listening ? "Listening… click to stop" : "Voice input (browser-native)"}
            className={
              "shrink-0 inline-flex items-center justify-center rounded-xl border w-9 h-9 transition " +
              (listening
                ? "bg-rose-600 text-white border-rose-600 animate-pulse"
                : "border-stone-200 text-stone-700 hover:border-stone-900")
            }
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden
            >
              <rect x="9" y="2" width="6" height="13" rx="3" />
              <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
            </svg>
          </button>
        )}
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
        {supported && " · Voice input is browser-native Web Speech API"}
      </p>
    </div>
  );
}
