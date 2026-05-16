import BrandMark from "./BrandMark";

export default function Footer() {
  return (
    <footer className="border-t border-stone-200 mt-20 bg-white">
      <div className="mx-auto max-w-6xl px-6 py-10 grid grid-cols-1 sm:grid-cols-3 gap-8 text-sm">
        <div>
          <BrandMark withText />
          <p className="mt-3 text-stone-600 max-w-xs leading-relaxed">
            A clinician-reviewed FAQ assistant for three specialties.
            Retrieval-only, BM25 ranked, no AI model in the loop.
          </p>
        </div>

        <div>
          <p className="font-medium text-stone-900 mb-2">Specialties</p>
          <ul className="space-y-1.5 text-stone-600">
            <li>
              <a href="/chat/radiology" className="link-underline">
                Radiology
              </a>
            </li>
            <li>
              <a href="/chat/physiotherapy" className="link-underline">
                Physiotherapy
              </a>
            </li>
            <li>
              <a href="/chat/cardiovascular" className="link-underline">
                Cardiovascular
              </a>
            </li>
          </ul>
        </div>

        <div>
          <p className="font-medium text-stone-900 mb-2">Project</p>
          <ul className="space-y-1.5 text-stone-600">
            <li>
              <a
                href="https://github.com/AbdulGhani002/medical-faq-auto"
                className="link-underline"
              >
                GitHub repository
              </a>
            </li>
            <li>
              <a href="/admin" className="link-underline">
                Admin dashboard
              </a>
            </li>
            <li>Semester project, NUTECH</li>
          </ul>
        </div>
      </div>
      <div className="border-t border-stone-200">
        <div className="mx-auto max-w-6xl px-6 py-4 text-xs text-stone-500 flex flex-wrap justify-between gap-2">
          <p>Built without LLMs. Pure retrieval, BM25 over a curated index.</p>
          <p>
            &copy; {new Date().getFullYear()} MedFAQ. Clinical content for
            information only.
          </p>
        </div>
      </div>
    </footer>
  );
}
