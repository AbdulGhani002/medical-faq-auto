import PlaygroundClient from "@/components/PlaygroundClient";
import Link from "next/link";

export const metadata = {
  title: "NLP Playground - MedFAQ",
};

export default function PlaygroundPage() {
  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <nav className="flex items-center gap-1.5 text-[11px] tracking-[0.14em] uppercase text-stone-400 mb-4">
        <Link href="/" className="hover:text-stone-900">Home</Link>
        <span>/</span>
        <span className="text-stone-700">Playground</span>
      </nav>

      <header className="mb-6">
        <h1 className="display text-3xl mb-1">NLP Playground</h1>
        <p className="text-stone-600 max-w-2xl">
          Type any sentence. Every component of the chatbot's NLP pipeline
          runs locally on the FastAPI backend and renders here in real time:
          tokenisation, lemmatisation, POS, NER, negation scope, intent
          (Naive Bayes), question type, sentiment, triage, keywords. No LLM
          is called.
        </p>
      </header>

      <PlaygroundClient />
    </div>
  );
}
