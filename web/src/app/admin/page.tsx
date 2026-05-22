import AdminDashboard from "@/components/AdminDashboard";
import DashboardCharts from "@/components/DashboardCharts";
import Link from "next/link";

export default function AdminPage() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <nav className="flex items-center gap-1.5 text-[11px] tracking-[0.14em] uppercase text-stone-400 mb-4">
        <Link href="/" className="hover:text-stone-900">
          Home
        </Link>
        <span>/</span>
        <span className="text-stone-700">Admin</span>
      </nav>
      <header className="mb-8">
        <h1 className="display text-3xl mb-1">Admin dashboard</h1>
        <p className="text-stone-600 max-w-2xl">
          Live analytics + candidate-FAQ review. Chart data is produced by
          the NLP analyser running on the FastAPI backend over recent chat
          turns. No data leaves the server.
        </p>
      </header>

      <DashboardCharts />

      <div className="mt-10 border-t border-stone-200 pt-8">
        <h2 className="text-xl font-semibold mb-1">Candidate FAQs</h2>
        <p className="text-sm text-stone-500 mb-5">
          Approve, edit, or reject candidate FAQs before they appear on the
          public site.
        </p>
        <AdminDashboard />
      </div>
    </div>
  );
}
