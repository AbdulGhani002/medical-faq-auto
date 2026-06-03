import Link from "next/link";
import BrandMark from "./BrandMark";
import StartChattingMenu from "./StartChattingMenu";

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

        <StartChattingMenu />
      </div>
    </header>
  );
}
