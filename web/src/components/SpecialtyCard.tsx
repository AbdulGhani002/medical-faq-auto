import Link from "next/link";
import { SpecialtyIcon } from "./SpecialtyIcons";

export default function SpecialtyCard({
  slug,
  title,
  desc,
  count,
}: {
  slug: string;
  title: string;
  desc: string;
  count?: number;
}) {
  return (
    <Link
      href={`/chat/${slug}`}
      className="group relative block rounded-2xl border border-stone-200 bg-white p-6 shadow-card shadow-card-hover transition"
    >
      <div className="flex items-start justify-between mb-5">
        <div className="rounded-xl border border-stone-200 bg-stone-50 p-2.5 text-stone-700 group-hover:text-stone-950 group-hover:border-stone-300 transition">
          <SpecialtyIcon slug={slug} size={28} />
        </div>
        {count !== undefined && (
          <span className="pill">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-600 inline-block" />
            {count} approved
          </span>
        )}
      </div>

      <h3 className="text-lg font-semibold tracking-tight mb-1.5">{title}</h3>
      <p className="text-sm text-stone-600 leading-relaxed mb-6 min-h-[40px]">
        {desc}
      </p>

      <div className="flex items-center justify-between text-[13px]">
        <span className="text-stone-500">Open assistant</span>
        <span className="inline-flex items-center gap-1.5 font-medium text-stone-950 group-hover:gap-2.5 transition-all">
          Chat now
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden
          >
            <path d="M5 12h14M13 5l7 7-7 7" />
          </svg>
        </span>
      </div>

      <span
        aria-hidden
        className="absolute inset-x-6 bottom-0 h-px bg-gradient-to-r from-transparent via-stone-300 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"
      />
    </Link>
  );
}
