"use client";
import { useState } from "react";

export default function EditFAQModal({
  initialQuestion,
  initialAnswer,
  onSave,
  onClose,
  saving,
}: {
  initialQuestion: string;
  initialAnswer: string;
  onSave: (q: string, a: string) => void;
  onClose: () => void;
  saving?: boolean;
}) {
  const [q, setQ] = useState(initialQuestion);
  const [a, setA] = useState(initialAnswer);

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-5">
        <h3 className="font-semibold text-lg mb-3">Edit FAQ</h3>
        <label className="block text-xs text-slate-500 mb-1">
          Question
        </label>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="w-full mb-3 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-slate-900"
        />
        <label className="block text-xs text-slate-500 mb-1">
          Answer
        </label>
        <textarea
          value={a}
          onChange={(e) => setA(e.target.value)}
          rows={6}
          className="w-full mb-4 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-slate-900 resize-y"
        />
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="text-sm px-4 py-2 rounded-lg border border-slate-300 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => onSave(q, a)}
            disabled={saving || (!q.trim() && !a.trim())}
            className="text-sm px-4 py-2 rounded-lg bg-slate-900 text-white hover:bg-slate-700 disabled:opacity-40"
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
