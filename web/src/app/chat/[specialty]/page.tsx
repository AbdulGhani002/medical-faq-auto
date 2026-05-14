import ChatWidget from "@/components/ChatWidget";
import Link from "next/link";

const VALID = ["radiology", "physiotherapy", "cardiovascular"];

export default async function ChatPage({
  params,
}: {
  params: Promise<{ specialty: string }>;
}) {
  const { specialty } = await params;
  if (!VALID.includes(specialty)) {
    return <p className="text-gray-500">Unknown specialty.</p>;
  }
  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold mb-1 capitalize">{specialty}</h1>
      <p className="text-gray-600 mb-4">
        Ask your question. Answers come from real human-written replies,
        selected by our retrieval pipeline. No generative model is used.
      </p>
      <ChatWidget specialty={specialty} />
      <p className="mt-6 text-sm text-gray-500">
        <Link className="underline" href={`/faq/${specialty}`}>
          See the public FAQ for {specialty}
        </Link>
      </p>
    </div>
  );
}
