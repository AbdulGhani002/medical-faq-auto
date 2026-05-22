import "./globals.css";

import Footer from "@/components/Footer";
import Header from "@/components/Header";

export const metadata = {
  title: "MedFAQ - Clinician-reviewed answers, classical NLP only",
  description:
    "Three specialty assistants. Hybrid retrieval: TF-IDF + BM25 + LSA + PPMI embeddings, with Naive Bayes intent, medical NER, sentiment, triage, and multi-turn dialog. No LLM, no neural network.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-stone-50 text-stone-950">
        <Header />
        <main className="flex-1 w-full">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
