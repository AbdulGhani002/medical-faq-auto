import SpecialtyCard from "@/components/SpecialtyCard";

const specialties = [
  {
    slug: "radiology",
    title: "Radiology",
    desc: "Scans, imaging prep, contrast, reports.",
  },
  {
    slug: "physiotherapy",
    title: "Physiotherapy",
    desc: "Exercises, recovery, soreness, sessions.",
  },
  {
    slug: "cardiovascular",
    title: "Cardiovascular",
    desc: "Heart health, BP, diet, medication timing.",
  },
];

export default function Home() {
  return (
    <div className="mx-auto max-w-4xl">
      <h1 className="text-3xl font-bold mb-2">Pick a specialty to chat</h1>
      <p className="text-gray-600 mb-8">
        Ask anything. Your chat is saved (with consent) and used to improve
        the public FAQ for everyone.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {specialties.map((s) => (
          <SpecialtyCard key={s.slug} {...s} />
        ))}
      </div>
    </div>
  );
}
