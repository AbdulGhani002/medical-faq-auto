const SAMPLES: Record<string, string[]> = {
  radiology: [
    "Do I need to fast before my MRI?",
    "Is the contrast injection safe?",
    "How long will my CT scan take?",
    "When do I get my scan report?",
  ],
  physiotherapy: [
    "How often should I do my home exercises?",
    "Is it normal to feel sore after a session?",
    "How many sessions will I need?",
    "When can I return to running?",
  ],
  cardiovascular: [
    "When should I take my BP medicine?",
    "Can I exercise with high blood pressure?",
    "What foods should I avoid?",
    "Is chest tightness a warning sign?",
  ],
};

export default function SuggestedQuestions({
  specialty,
  onPick,
}: {
  specialty: string;
  onPick: (q: string) => void;
}) {
  const list = SAMPLES[specialty] || [];
  if (!list.length) return null;
  return (
    <div className="mt-2">
      <p className="text-[10px] uppercase tracking-[0.18em] text-stone-500 mb-2.5">
        Suggested questions
      </p>
      <div className="flex flex-wrap gap-2">
        {list.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => onPick(q)}
            className="text-[13px] border border-stone-200 hover:border-stone-900 bg-white rounded-full px-3.5 py-2 text-stone-800 hover:text-stone-950 hover:shadow-card transition"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}
