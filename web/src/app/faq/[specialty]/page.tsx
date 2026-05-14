import FAQList from "@/components/FAQList";
import Link from "next/link";

const VALID = ["radiology", "physiotherapy", "cardiovascular"];

export default async function FAQPage({
  params,
}: {
  params: Promise<{ specialty: string }>;
}) {
  const { specialty } = await params;
  if (!VALID.includes(specialty)) {
    return <p className="text-gray-500">Unknown specialty.</p>;
  }
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-2xl font-bold mb-1 capitalize">
        {specialty} FAQ
      </h1>
      <p className="text-gray-600 mb-6">
        Auto-built from clustered patient questions, reviewed by clinicians
        before publishing.
      </p>
      <FAQList specialty={specialty} />
      <p className="mt-6 text-sm text-gray-500">
        <Link className="underline" href={`/chat/${specialty}`}>
          Or chat with the {specialty} bot
        </Link>
      </p>
    </div>
  );
}
