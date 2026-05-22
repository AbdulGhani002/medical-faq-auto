import HeroGraphic from "@/components/HeroGraphic";
import SpecialtyCard from "@/components/SpecialtyCard";
import { fetchFAQs } from "@/lib/api";

const SPECIALTIES = [
  {
    slug: "radiology",
    title: "Radiology",
    desc: "Scan preparation, contrast safety, imaging reports.",
  },
  {
    slug: "physiotherapy",
    title: "Physiotherapy",
    desc: "Exercises, soreness, recovery and session frequency.",
  },
  {
    slug: "cardiovascular",
    title: "Cardiovascular",
    desc: "Heart health, medication timing, diet and warning signs.",
  },
];

async function getCounts(): Promise<Record<string, number>> {
  const out: Record<string, number> = {};
  await Promise.all(
    SPECIALTIES.map(async (s) => {
      try {
        const faqs = await fetchFAQs(s.slug);
        out[s.slug] = faqs.length;
      } catch {
        out[s.slug] = 0;
      }
    })
  );
  return out;
}

export default async function Home() {
  const counts = await getCounts();
  const total = Object.values(counts).reduce((a, b) => a + b, 0);

  return (
    <div className="mx-auto max-w-6xl px-6">
      <section className="relative pt-16 pb-20 grid grid-cols-1 lg:grid-cols-[1.05fr_0.95fr] gap-12 items-center">
        <div className="dotted-bg absolute inset-x-0 -top-6 h-72 -z-10 opacity-60" />
        <div>
          <span className="pill mb-5">
            <span className="h-1.5 w-1.5 rounded-full bg-stone-950 inline-block" />
            Retrieval only &middot; No LLM in the loop
          </span>
          <h1 className="display text-5xl md:text-6xl text-stone-950 mb-5">
            Clinician answers,
            <br />
            <span className="text-stone-500">not generated text.</span>
          </h1>
          <p className="text-stone-600 text-lg max-w-xl leading-relaxed mb-8">
            Three specialty assistants. Hybrid TF-IDF + BM25 + LSA + PPMI
            retrieval, plus a from-scratch MLP, CRF and PyTorch transformer
            trained on our own corpus. Every reply is a real
            clinician-reviewed answer, never machine-written.
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              href="#specialties"
              className="inline-flex items-center gap-2 bg-stone-950 text-white text-sm font-medium px-5 py-3 rounded-full hover:bg-stone-800 transition shadow-card"
            >
              Pick a specialty
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                   strokeLinejoin="round" aria-hidden>
                <path d="M5 12h14M13 5l7 7-7 7" />
              </svg>
            </a>
            <a
              href="/faq/radiology"
              className="inline-flex items-center text-sm font-medium px-5 py-3 rounded-full border border-stone-300 hover:border-stone-900 transition"
            >
              Browse FAQs
            </a>
          </div>

          <dl className="mt-10 grid grid-cols-3 gap-6 max-w-md">
            <Stat label="Specialties" value="3" />
            <Stat label="Approved FAQs" value={String(total)} />
            <Stat label="In-house models" value="13" />
          </dl>
        </div>

        <div className="hidden lg:block justify-self-end">
          <HeroGraphic />
        </div>
      </section>

      <section
        id="specialties"
        className="pt-6 pb-12 scroll-mt-24"
      >
        <div className="flex items-baseline justify-between mb-6">
          <h2 className="text-2xl font-semibold tracking-tight">
            Choose an assistant
          </h2>
          <p className="text-sm text-stone-500 hidden sm:block">
            Each runs the same hybrid TF-IDF + BM25 + LSA + PPMI retriever
            over its specialty&apos;s index.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {SPECIALTIES.map((s) => (
            <SpecialtyCard key={s.slug} {...s} count={counts[s.slug]} />
          ))}
        </div>
      </section>

      <section className="py-16 border-t border-stone-200">
        <h2 className="text-2xl font-semibold tracking-tight mb-2">
          How it works
        </h2>
        <p className="text-stone-600 mb-8 max-w-2xl">
          Three steps, end to end. No model is ever trained, called, or
          deployed.
        </p>
        <ol className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <Step
            num="01"
            title="You ask"
            body="Type your question in plain English, or mix in Urdu. The text is PHI-scrubbed before storage."
          />
          <Step
            num="02"
            title="Classical NLP ranks"
            body="TF-IDF (word + char) plus BM25 plus LSA topic similarity, with Naive Bayes intent, medical NER, negation, and sentiment all running locally."
          />
          <Step
            num="03"
            title="A clinician answer"
            body="The highest-scoring approved FAQ is returned verbatim. You always see the source confidence."
          />
        </ol>
      </section>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-[0.18em] text-stone-500">
        {label}
      </dt>
      <dd className="text-3xl font-semibold mt-1">{value}</dd>
    </div>
  );
}

function Step({
  num,
  title,
  body,
}: {
  num: string;
  title: string;
  body: string;
}) {
  return (
    <li className="rounded-2xl border border-stone-200 bg-white p-6 shadow-card">
      <div className="text-xs tracking-[0.18em] text-stone-400 mb-3">
        STEP {num}
      </div>
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-sm text-stone-600 leading-relaxed">{body}</p>
    </li>
  );
}
