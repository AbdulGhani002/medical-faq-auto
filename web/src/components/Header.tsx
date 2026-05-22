import Link from "next/link";
import BrandMark from "./BrandMark";

const NAV = [
  { href: "/", label: "Home" },
  { href: "/faq/radiology", label: "FAQs" },
  { href: "/playground", label: "Playground" },
  { href: "/architecture", label: "Architecture" },
  { href: "/admin", label: "Admin" },
];

export default function Header() {
  return (
    <header className="sticky top-0 z-20 bg-white/90 backdrop-blur border-b border-stone-200">
      <div className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between">
        <Link
          href="/"
          className="flex items-center gap-3 group"
          aria-label="MedFAQ home"
        >
          <BrandMark size={28} withText />
        </Link>

        <nav className="hidden sm:flex items-center gap-7 text-[13px]">
          {NAV.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className="link-underline text-stone-700 hover:text-stone-950"
            >
              {n.label}
            </Link>
          ))}
        </nav>

        <Link
          href="/chat/radiology"
          className="hidden sm:inline-flex items-center gap-2 bg-stone-950 text-white text-[13px] font-medium px-4 py-2 rounded-full hover:bg-stone-800 transition shadow-card"
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
          >
            <path d="M5 12h14M13 5l7 7-7 7" />
          </svg>
        </Link>
      </div>
    </header>
  );
}
