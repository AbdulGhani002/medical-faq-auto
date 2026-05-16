import "./globals.css";

import Footer from "@/components/Footer";
import Header from "@/components/Header";

export const metadata = {
  title: "MedFAQ - Clinician-reviewed answers, no AI in the loop",
  description:
    "Ask one of three specialty assistants. Retrieval-only, BM25 ranked over an approved FAQ index. No LLM, no AI model.",
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
