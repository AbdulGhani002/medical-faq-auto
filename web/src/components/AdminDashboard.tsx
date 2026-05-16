"use client";
import { useCallback, useEffect, useState } from "react";
import {
  approveFAQ, editFAQ, fetchCandidates, fetchFAQs, rejectFAQ,
} from "@/lib/api";
import type { Candidate, FAQItem } from "@/lib/types";
import EditFAQModal from "./EditFAQModal";
import { SpecialtyIcon } from "./SpecialtyIcons";

const TABS = ["radiology", "physiotherapy", "cardiovascular"] as const;

export default function AdminDashboard() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("radiology");
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [approved, setApproved] = useState<FAQItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [editing, setEditing] = useState<FAQItem | null>(null);

  const refresh = useCallback(async () => {
    setBusy(true);
    try {
      const [c, a] = await Promise.all([fetchCandidates(tab), fetchFAQs(tab)]);
      setCandidates(c);
      setApproved(a);
    } catch {
      setMsg("Failed to load. Is the API on :8000?");
    } finally {
      setBusy(false);
    }
  }, [tab]);

  useEffect(() => { refresh(); }, [refresh]);

  async function act(fn: () => Promise<unknown>, ok: string) {
    setBusy(true); setMsg(null);
    try {
      await fn();
      setMsg(ok);
      await refresh();
    } catch {
      setMsg("Action failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <StatCard label="Awaiting review" value={candidates.length} tone="warn" />
        <StatCard label="Approved" value={approved.length} tone="ok" />
        <StatCard label="Specialty" value={tab} tone="neutral" capitalize />
      </div>

      <div className="flex items-center gap-1 mb-5 border border-stone-200 rounded-full p-1 bg-white w-fit">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={
              "flex items-center gap-1.5 capitalize text-sm px-3.5 py-1.5 rounded-full transition " +
              (tab === t
                ? "bg-stone-950 text-white"
                : "text-stone-600 hover:text-stone-950")
            }
          >
            <SpecialtyIcon slug={t} size={14} />
            {t}
          </button>
        ))}
        <button
          type="button"
          onClick={refresh}
          disabled={busy}
          className="ml-2 text-xs px-3 py-1.5 rounded-full border border-stone-200 hover:border-stone-900 disabled:opacity-40"
        >
          {busy ? "Working..." : "Refresh"}
        </button>
      </div>

      {msg && (
        <div className="mb-4 text-sm rounded-2xl border border-stone-200 bg-white px-4 py-3 text-stone-700 shadow-card">
          {msg}
        </div>
      )}

      <section className="mb-10">
        <h2 className="text-lg font-semibold mb-3">Candidates awaiting review</h2>
        {candidates.length === 0 ? (
          <p className="text-sm text-stone-500 rounded-2xl border border-dashed border-stone-300 p-6 text-center">
            No pending candidates. The pipeline writes new candidates here with
            approved=false.
          </p>
        ) : (
          <div className="space-y-3">
            {candidates.map((c) => (
              <div key={c.id} className="rounded-2xl border border-stone-200 bg-white p-5 shadow-card">
                <div className="text-[10px] uppercase tracking-[0.14em] text-stone-400 mb-1.5">
                  Candidate &middot; {c.count} asked
                </div>
                <div className="font-semibold mb-2">{c.question}</div>
                <p className="text-sm text-stone-700 mb-4 leading-relaxed">{c.answer}</p>
                <div className="flex flex-wrap gap-2 text-sm">
                  <button onClick={() => act(() => approveFAQ(c.id), "Approved.")}
                    disabled={busy}
                    className="bg-stone-950 text-white rounded-full px-4 py-1.5 hover:bg-stone-800 disabled:opacity-40">Approve</button>
                  <button onClick={() => setEditing(c)} disabled={busy}
                    className="border border-stone-300 rounded-full px-4 py-1.5 hover:border-stone-900 disabled:opacity-40">Edit</button>
                  <button onClick={() => act(() => rejectFAQ(c.id), "Rejected.")} disabled={busy}
                    className="border border-red-300 text-red-700 rounded-full px-4 py-1.5 hover:bg-red-50 disabled:opacity-40">Reject</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold mb-3">
          Approved &middot; visible on the public FAQ page
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {approved.map((it) => (
            <div key={it.id} className="rounded-2xl border border-stone-200 bg-white p-4 shadow-card">
              <div className="font-medium text-sm mb-1.5">{it.question}</div>
              <p className="text-xs text-stone-600 line-clamp-3 leading-relaxed">{it.answer}</p>
              <div className="mt-3 flex items-center justify-between text-xs text-stone-500">
                <span>{it.count} asked</span>
                <button onClick={() => setEditing(it)}
                  className="link-underline text-stone-800 font-medium">Edit</button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {editing && (
        <EditFAQModal
          initialQuestion={editing.question}
          initialAnswer={editing.answer}
          saving={busy}
          onClose={() => setEditing(null)}
          onSave={async (q, a) => {
            await act(() => editFAQ(editing.id, { question: q, answer: a }), "Saved.");
            setEditing(null);
          }}
        />
      )}
    </div>
  );
}

function StatCard({
  label, value, tone, capitalize,
}: {
  label: string; value: string | number;
  tone: "ok" | "warn" | "neutral"; capitalize?: boolean;
}) {
  const dot = tone === "ok" ? "bg-emerald-600"
    : tone === "warn" ? "bg-amber-500" : "bg-stone-400";
  return (
    <div className="rounded-2xl border border-stone-200 bg-white p-5 shadow-card">
      <div className="text-[10px] uppercase tracking-[0.18em] text-stone-500 flex items-center gap-1.5">
        <span className={"h-1.5 w-1.5 rounded-full inline-block " + dot} />
        {label}
      </div>
      <div className={"text-3xl font-semibold mt-2 " + (capitalize ? "capitalize" : "")}>
        {value}
      </div>
    </div>
  );
}
