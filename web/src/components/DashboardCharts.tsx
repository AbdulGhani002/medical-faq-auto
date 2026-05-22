"use client";
import { useEffect, useState } from "react";

const API =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Overview = {
  specialties: {
    specialty: string;
    approved: number;
    pending: number;
    rejected: number;
    chat_turns: number;
  }[];
};

type DistEntry = { label: string; count: number };
type Distribution = {
  specialty: string;
  n_turns_analysed: number;
  intent: DistEntry[];
  sentiment: DistEntry[];
  triage: DistEntry[];
  entity_label: DistEntry[];
  question_type: DistEntry[];
  top_keywords: DistEntry[];
};

const SPECIALTIES = ["radiology", "physiotherapy", "cardiovascular"];

const COLORS: Record<string, string> = {
  positive: "#15803d",
  neutral: "#78716c",
  negative: "#be123c",
  "level-0": "#a8a29e",
  "level-1": "#f59e0b",
  "level-2": "#ea580c",
  "level-3": "#dc2626",
};

export default function DashboardCharts() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [specialty, setSpecialty] = useState("cardiovascular");
  const [dist, setDist] = useState<Distribution | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API}/stats/overview`).then((r) => r.json()).then(setOverview);
  }, []);

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/stats/chat_distribution/${specialty}?limit=500`)
      .then((r) => r.json())
      .then((d) => {
        setDist(d);
        setLoading(false);
      });
  }, [specialty]);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {(overview?.specialties || []).map((s) => (
          <div
            key={s.specialty}
            className="rounded-2xl border border-stone-200 bg-white shadow-card p-5"
          >
            <p className="text-[10px] uppercase tracking-[0.18em] text-stone-500 mb-3 capitalize">
              {s.specialty}
            </p>
            <div className="grid grid-cols-3 gap-3">
              <Stat label="Approved" value={s.approved} />
              <Stat label="Pending" value={s.pending} />
              <Stat label="Turns" value={s.chat_turns} />
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-stone-200 bg-white shadow-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
          <div>
            <p className="text-[10px] uppercase tracking-[0.18em] text-stone-500 mb-1">
              Chat-turn analytics
            </p>
            <h3 className="font-semibold text-lg capitalize">
              {specialty} {loading && <span className="text-stone-400 text-sm">(loading…)</span>}
            </h3>
            <p className="text-[12px] text-stone-500">
              {dist
                ? `${dist.n_turns_analysed} user turns analysed`
                : "Loading…"}
            </p>
          </div>
          <div className="flex gap-1.5">
            {SPECIALTIES.map((s) => (
              <button
                key={s}
                onClick={() => setSpecialty(s)}
                className={
                  "text-[12px] px-3 py-1.5 rounded-full border transition capitalize " +
                  (s === specialty
                    ? "bg-stone-900 text-white border-stone-900"
                    : "border-stone-200 hover:border-stone-900")
                }
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {dist && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Chart title="Intent distribution" data={dist.intent} />
            <Chart
              title="Sentiment"
              data={dist.sentiment}
              colorFor={(d) => COLORS[d.label]}
            />
            <Chart
              title="Triage levels"
              data={dist.triage}
              colorFor={(d) => COLORS[d.label]}
            />
            <Chart title="Question type" data={dist.question_type} />
            <Chart title="Entity labels" data={dist.entity_label} wide />
            <KeywordCloud title="Top keywords" data={dist.top_keywords} />
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <p className="text-[10px] uppercase tracking-[0.14em] text-stone-500">
        {label}
      </p>
      <p className="text-2xl font-semibold mt-0.5 tabular-nums">{value}</p>
    </div>
  );
}

function Chart({
  title,
  data,
  colorFor,
  wide,
}: {
  title: string;
  data: DistEntry[];
  colorFor?: (d: DistEntry) => string | undefined;
  wide?: boolean;
}) {
  const max = Math.max(1, ...data.map((d) => d.count));
  return (
    <div className={wide ? "lg:col-span-2" : ""}>
      <p className="text-[10px] uppercase tracking-[0.16em] text-stone-500 mb-2">
        {title}
      </p>
      {data.length === 0 ? (
        <p className="text-[12px] text-stone-400">No data yet.</p>
      ) : (
        <div className="space-y-1.5">
          {data.map((d) => {
            const pct = (d.count / max) * 100;
            const c = (colorFor && colorFor(d)) || "#1c1917";
            return (
              <div key={d.label} className="flex items-center gap-2">
                <span className="w-32 shrink-0 text-[11px] text-stone-600 truncate">
                  {d.label}
                </span>
                <div className="flex-1 h-3 bg-stone-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{ width: pct + "%", background: c }}
                  />
                </div>
                <span className="w-8 text-right text-[11px] tabular-nums text-stone-500">
                  {d.count}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function KeywordCloud({
  title,
  data,
}: {
  title: string;
  data: DistEntry[];
}) {
  const max = Math.max(1, ...data.map((d) => d.count));
  return (
    <div>
      <p className="text-[10px] uppercase tracking-[0.16em] text-stone-500 mb-2">
        {title}
      </p>
      {data.length === 0 ? (
        <p className="text-[12px] text-stone-400">No keywords yet.</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {data.map((d) => {
            const scale = 0.8 + (d.count / max) * 0.8;
            return (
              <span
                key={d.label}
                className="pill"
                style={{
                  fontSize: 10 * scale + "px",
                  padding: `${4 * scale}px ${10 * scale}px`,
                }}
              >
                {d.label}
                <span className="opacity-50 ml-1">×{d.count}</span>
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}
