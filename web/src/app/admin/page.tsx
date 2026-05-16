import AdminDashboard from "@/components/AdminDashboard";
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
          Approve, edit, or reject candidate FAQs before they appear on the
          public site. The pipeline writes candidates here for clinician
          review.
        </p>
      </header>
      <AdminDashboard />
    </div>
  );
}
