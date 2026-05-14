import Link from "next/link";

export default function SpecialtyCard({
  slug,
  title,
  desc,
}: {
  slug: string;
  title: string;
  desc: string;
}) {
  return (
    <Link
      href={`/chat/${slug}`}
      className="border border-gray-200 rounded-md p-5 hover:border-gray-900 transition block"
    >
      <h2 className="font-semibold text-lg mb-1">{title}</h2>
      <p className="text-sm text-gray-600 mb-3">{desc}</p>
      <span className="text-sm underline">Open chat &rarr;</span>
    </Link>
  );
}
