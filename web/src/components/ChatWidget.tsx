"use client";
import { useEffect, useRef, useState } from "react";
import { resetChat, sendChat } from "@/lib/api";
import type { Msg } from "@/lib/types";
import { SpecialtyIcon } from "./SpecialtyIcons";
import ChatInput from "./ChatInput";
import MessageBubble from "./MessageBubble";
import SuggestedQuestions from "./SuggestedQuestions";

function newSessionId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return String(Date.now()) + Math.random().toString(36).slice(2);
}

export default function ChatWidget({ specialty }: { specialty: string }) {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(newSessionId);
  const [topic, setTopic] = useState<string | null>(null);
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scroller.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [msgs, loading]);

  async function ask(text: string) {
    const t = text.trim();
    if (!t || loading) return;
    const userMsgIdx = msgs.length;
    setMsgs((m) => [...m, { role: "user", text: t, ts: Date.now() }]);
    setInput("");
    setLoading(true);
    try {
      const r = await sendChat(sessionId, specialty, t);
      setTopic(r.dialog?.active_topic ?? topic);
      const userEnts = r.nlp?.entities ?? null;
      setMsgs((m) => {
        const next = [...m];
        // Backfill entity annotations on the user bubble we just added.
        if (next[userMsgIdx] && next[userMsgIdx].role === "user") {
          next[userMsgIdx] = { ...next[userMsgIdx], user_entities: userEnts };
        }
        next.push({
          role: "bot",
          text: r.answer,
          confidence: r.confidence,
          bucket: r.bucket,
          alternatives: r.alternatives,
          intent: r.intent,
          spell_corrections: r.spell_corrections,
          added_terms: r.added_terms,
          score_breakdown: r.score_breakdown ?? null,
          highlighted: r.highlighted ?? null,
          nlp: r.nlp ?? null,
          dialog: r.dialog ?? null,
          matched_question: r.matched_question ?? null,
          ts: Date.now(),
        });
        return next;
      });
    } catch {
      setMsgs((m) => [
        ...m,
        {
          role: "bot",
          text: "The server is unreachable. Please try again in a moment.",
          ts: Date.now(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function onReset() {
    try {
      await resetChat(sessionId);
    } catch {
      /* ignore */
    }
    setMsgs([]);
    setTopic(null);
    setSessionId(newSessionId());
  }

  return (
    <div className="rounded-3xl border border-stone-200 bg-white shadow-card overflow-hidden">
      <div className="px-5 py-3.5 border-b border-stone-200 flex items-center gap-3 bg-white">
        <div className="rounded-xl border border-stone-200 bg-stone-50 p-2 text-stone-800">
          <SpecialtyIcon slug={specialty} size={20} />
        </div>
        <div className="flex-1">
          <p className="text-[13px] font-semibold capitalize">
            {specialty} assistant
          </p>
          <p className="text-[11px] text-stone-500">
            TF-IDF + BM25 + LSA + PPMI + transformer / CRF / MLP — every
            model trained from scratch
          </p>
        </div>
        {topic && (
          <span
            title="Active conversation topic detected by NER"
            className="pill !py-0.5 !text-[10px] !bg-stone-900 !text-stone-50 !border-stone-900"
          >
            topic: {topic}
          </span>
        )}
        <button
          type="button"
          onClick={onReset}
          className="ml-1 text-[11px] text-stone-500 hover:text-stone-900 underline-offset-2 hover:underline"
        >
          Reset chat
        </button>
        <span className="pill">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-600 inline-block" />
          Online
        </span>
      </div>

      <div
        ref={scroller}
        className="chat-scroll h-[560px] overflow-y-auto px-4 py-5 space-y-3 bg-stone-50"
      >
        {msgs.length === 0 && (
          <div>
            <div className="rounded-2xl border border-stone-200 bg-white p-4 mb-4">
              <p className="text-[10px] uppercase tracking-[0.18em] text-stone-500 mb-2">
                Welcome
              </p>
              <p className="text-sm text-stone-800 leading-relaxed">
                Hi, I am the <span className="capitalize">{specialty}</span>{" "}
                assistant. Ask me about prep, recovery, medication, or any
                question on this topic. I look up clinician-reviewed answers
                using a hybrid TF-IDF + BM25 + LSA + PPMI retriever, with full NLP
                analysis (NER, intent, sentiment, triage). No AI in the loop.
              </p>
            </div>
            <SuggestedQuestions specialty={specialty} onPick={ask} />
          </div>
        )}

        {msgs.map((m, i) => (
          <MessageBubble key={i} msg={m} onAltClick={ask} />
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-stone-200 rounded-2xl rounded-bl-md px-4 py-3 shadow-card">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        )}
      </div>

      <ChatInput
        value={input}
        onChange={setInput}
        onSend={() => ask(input)}
        disabled={loading}
      />
    </div>
  );
}
