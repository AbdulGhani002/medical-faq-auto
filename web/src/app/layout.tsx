import "./globals.css";

export const metadata = {
  title: "Medical FAQ",
  description: "Auto-generated medical FAQs from chatbot logs.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-white text-gray-900">
        <header className="border-b border-gray-200 px-6 py-4">
          <a href="/" className="font-semibold">
            Medical FAQ
          </a>
          <a
            href="/admin"
            className="float-right text-sm text-gray-500 underline"
          >
            Admin
          </a>
        </header>
        <main className="px-6 py-8">{children}</main>
        <footer className="border-t border-gray-200 px-6 py-4 text-xs text-gray-500 mt-12">
          Semester project. Retrieval-based, no LLM. Answers come from
          clinician-reviewed sources.
        </footer>
      </body>
    </html>
  );
}
