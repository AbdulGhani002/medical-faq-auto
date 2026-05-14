export default function AdminPage() {
  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="text-2xl font-bold mb-1">Admin dashboard</h1>
      <p className="text-gray-600 mb-6">
        Review candidate FAQs, approve, edit, or reject. Watch trending
        issues. Export clusters as CSV.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <section className="border border-gray-200 rounded-md p-5">
          <h2 className="font-semibold mb-2">Candidate FAQs</h2>
          <p className="text-sm text-gray-500">
            TODO: list pipeline output where approved=false. Each row has
            Approve / Edit / Reject buttons.
          </p>
        </section>
        <section className="border border-gray-200 rounded-md p-5">
          <h2 className="font-semibold mb-2">Trending issues</h2>
          <p className="text-sm text-gray-500">
            TODO: clusters with fast growth in the last 24 hours.
          </p>
        </section>
        <section className="border border-gray-200 rounded-md p-5 md:col-span-2">
          <h2 className="font-semibold mb-2">Export</h2>
          <p className="text-sm text-gray-500">
            TODO: button that downloads all clusters and approved FAQs as
            CSV.
          </p>
        </section>
      </div>
    </div>
  );
}
