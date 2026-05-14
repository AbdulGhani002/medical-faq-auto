"use client";
import { useState } from "react";
import { sendChat } from "@/lib/api";

type Msg = { role: "user" | "bot"; text: string };

export default function ChatWidget({ specialty }: { specialty: string }) {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() =>
    typeof crypto !== "undefined" && crypto.randomUUID
      ? crypto.randomUUID()
      : String(Date.now())
  );

  async function send() {
    if (!input.trim() || loading) return;
    const userMsg: Msg = { role: "user", text: input };
    setMsgs((m) => [...m, userMsg]);
    const sent = input;
    setInput("");
    setLoading(true);
    try {
      const r = await sendChat(sessionId, specialty, sent);
      setMsgs((m) => [...m, { role: "bot", text: r.answer }]);
    } catch {
      setMsgs((m) => [
        ...m,
        { role: "bot", text: "Sorry, something went wrong. Try again." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="border border-gray-200 rounded-md p-4">
      <div className="h-80 overflow-y-auto mb-3 space-y-2">
        {msgs.length === 0 && (
          <p className="text-sm text-gray-400">
            Start the conversation below.
          </p>
        )}
        {msgs.map((m, i) => (
          <div
            key={i}
            className={
              "rounded-md p-2 text-sm " +
              (m.role === "user"
                ? "bg-gray-100 text-gray-900 ml-12"
                : "bg-gray-900 text-white mr-12")
            }
          >
            {m.text}
          </div>
        ))}
        {loading && (
          <p className="text-xs text-gray-400">Looking it up...</p>
        )}
      </div>
      <div className="flex gap-2">
        <input
          className="flex-1 border border-gray-300 rounded-md px-3 py-2 text-sm"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder={`Ask a ${specialty} question...`}
          disabled={loading}
        />
        <button
          onClick={send}
          disabled={loading}
          className="bg-gray-900 text-white rounded-md px-4 py-2 disabled:opacity-50 text-sm"
        >
          Send
        </button>
      </div>
    </div>
  );
}
