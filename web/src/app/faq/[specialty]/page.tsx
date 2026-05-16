import FAQList from "@/components/FAQList";
import { SpecialtyIcon } from "@/components/SpecialtyIcons";
import Link from "next/link";

const VALID = ["radiology", "physiotherapy", "cardiovascular"];

const SPECIALTIES = [
  { slug: "radiology", title: "Radiology" },
  { slug: "physiotherapy", title: "Physiotherapy" },
  { slug: "cardiovascular", title: "Cardiovascular" },
];

export default async function FAQPage({
  params,
}: {
  params: Promise<{ specialty: string }>;
}) {
  const { specialty } = await params;
  if (!VALID.includes(specialty)) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-12">
        <p className="text-stone-500">
          Unknown specialty.{" "}
          <Link href="/" className="underline">
            Back to home
          </Link>
        </p>
      </div>
    );
  }
  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <nav className="flex items-center gap-1.5 text-[11px] tracking-[0.14em] uppercase text-stone-400 mb-4">
        <Link href="/" className="hover:text-stone-900">
          Home
        </Link>
        <span>/</span>
        <span className="text-stone-700">FAQ</span>
      </nav>
      <header className="mb-6 flex items-start gap-4">
        <div className="rounded-2xl border border-stone-200 bg-white p-3 text-stone-800 shadow-card">
          <SpecialtyIcon slug={specialty} size={32} />
        </div>
        <div>
          <h1 className="display text-3xl capitalize mb-1">
            {specialty} FAQ
          </h1>
          <p className="text-stone-600">
            Clinician-reviewed answers, ranked by how often the question is
            asked.
          </p>
        </div>
      </header>

      <div className="mb-6 flex flex-wrap items-center gap-2 text-[12px]">
        {SPECIALTIES.map((s) => (
          <Link
            key={s.slug}
            href={`/faq/${s.slug}`}
            className={
              "rounded-full px-3 py-1.5 border " +
              (s.slug === specialty
                ? "bg-stone-950 text-white border-stone-950"
                : "border-stone-200 hover:border-stone-900")
            }
          >
            {s.title}
          </Link>
        ))}
      </div>

      <FAQList specialty={specialty} />

      <p className="mt-8 text-sm text-stone-500">
        Cannot find your question?{" "}
        <Link
          href={`/chat/${specialty}`}
          className="link-underline text-stone-800 font-medium"
        >
          Chat with the {specialty} assistant
        </Link>
      </p>
    </div>
  );
}
