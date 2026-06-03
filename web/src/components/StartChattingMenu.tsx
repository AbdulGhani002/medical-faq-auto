"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { SpecialtyIcon } from "./SpecialtyIcons";

const SPECIALTIES = [
  {
    slug: "radiology",
    title: "Radiology",
    desc: "Scans, MRI, CT, contrast safety",
  },
  {
    slug: "physiotherapy",
    title: "Physiotherapy",
    desc: "Exercise, soreness, recovery",
  },
  {
    slug: "cardiovascular",
    title: "Cardiovascular",
    desc: "Heart, blood pressure, palpitations",
  },
];

export default function StartChattingMenu() {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Close on outside-click and on Escape.
  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, []);

  return (
    <div ref={wrapperRef} className="relative hidden sm:block">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="inline-flex items-center gap-2 bg-stone-950 text-white text-[13px] font-medium px-4 py-2 rounded-full hover:bg-stone-800 transition shadow-card"
      >
        Start chatting
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
          className={"transition " + (open ? "rotate-90" : "")}
        >
          <path d="M5 12h14M13 5l7 7-7 7" />
        </svg>
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-72 rounded-2xl border border-stone-200 bg-white shadow-card overflow-hidden z-30"
        >
          <p className="px-4 pt-3 pb-2 text-[10px] uppercase tracking-[0.18em] text-stone-500">
            Pick a specialty
          </p>
          <ul className="pb-2">
            {SPECIALTIES.map((s) => (
              <li key={s.slug}>
                <Link
                  href={`/chat/${s.slug}`}
                  role="menuitem"
                  onClick={() => setOpen(false)}
                  className="flex items-start gap-3 px-4 py-2.5 hover:bg-stone-50"
                >
                  <span className="mt-0.5 rounded-lg border border-stone-200 bg-white p-1.5 text-stone-800">
                    <SpecialtyIcon slug={s.slug} size={16} />
                  </span>
                  <span className="flex-1">
                    <span className="block text-[13px] font-medium text-stone-900">
                      {s.title}
                    </span>
                    <span className="block text-[11px] text-stone-500">
                      {s.desc}
                    </span>
                  </span>
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="mt-1 text-stone-400"
                    aria-hidden
                  >
                    <path d="M9 18l6-6-6-6" />
                  </svg>
                </Link>
              </li>
            ))}
          </ul>
          <div className="border-t border-stone-200 px-4 py-2.5 bg-stone-50/60 flex items-center justify-between text-[11px]">
            <Link
              href="/playground"
              onClick={() => setOpen(false)}
              className="text-stone-700 hover:text-stone-950"
            >
              Open Playground
            </Link>
            <Link
              href="/architecture"
              onClick={() => setOpen(false)}
              className="text-stone-700 hover:text-stone-950"
            >
              View Architecture
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
