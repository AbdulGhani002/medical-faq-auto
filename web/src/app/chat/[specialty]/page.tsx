import ChatWidget from "@/components/ChatWidget";
import { SpecialtyIcon } from "@/components/SpecialtyIcons";
import Link from "next/link";

const VALID = ["radiology", "physiotherapy", "cardiovascular"];
const TITLES: Record<string, string> = {
  radiology: "Radiology",
  physiotherapy: "Physiotherapy",
  cardiovascular: "Cardiovascular",
};

export default async function ChatPage({
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
    <div className="mx-auto max-w-3xl px-6 py-10">
      <nav className="flex items-center gap-1.5 text-[11px] tracking-[0.14em] uppercase text-stone-400 mb-4">
        <Link href="/" className="hover:text-stone-900">
          Home
        </Link>
        <span>/</span>
        <Link href="/faq/radiology" className="hover:text-stone-900">
          Specialties
        </Link>
        <span>/</span>
        <span className="text-stone-700">{TITLES[specialty]}</span>
      </nav>

      <header className="mb-6 flex items-start gap-4">
        <div className="rounded-2xl border border-stone-200 bg-white p-3 text-stone-800 shadow-card">
          <SpecialtyIcon slug={specialty} size={32} />
        </div>
        <div className="flex-1">
          <h1 className="display text-3xl mb-1">
            {TITLES[specialty]} assistant
          </h1>
          <p className="text-stone-600">
            Answers come from a clinician-reviewed FAQ index. Pure BM25
            retrieval, no LLM or AI model.
          </p>
        </div>
      </header>

      <ChatWidget specialty={specialty} />

      <p className="mt-6 text-sm text-stone-500">
        Looking for the full list?{" "}
        <Link
          href={`/faq/${specialty}`}
          className="link-underline text-stone-800 font-medium"
        >
          Browse the {specialty} FAQ
        </Link>
      </p>
    </div>
  );
}
