import ArchitectureDiagram from "@/components/ArchitectureDiagram";
import Link from "next/link";

export const metadata = {
  title: "Architecture - MedFAQ",
};

export default function ArchitecturePage() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-10">
      <nav className="flex items-center gap-1.5 text-[11px] tracking-[0.14em] uppercase text-stone-400 mb-4">
        <Link href="/" className="hover:text-stone-900">Home</Link>
        <span>/</span>
        <span className="text-stone-700">Architecture</span>
      </nav>

      <header className="mb-8">
        <h1 className="display text-3xl mb-2">System architecture</h1>
        <p className="text-stone-600 max-w-3xl">
          Every box below is a real Python module in <code>api/app/nlp/</code>
          {" "}or <code>api/app/services/</code>. No LLM, no neural network,
          no model download. Hover any block for the technique behind it.
        </p>
      </header>

      <ArchitectureDiagram />

      <Stack />
      <Channels />
      <Numbers />
    </div>
  );
}

function Stack() {
  const groups = [
    {
      title: "Token-level NLP",
      items: [
        ["Tokenizer", "regex word + medical-aware stopwords"],
        ["Porter stemmer", "1980 algorithm, pure Python"],
        ["Rule-based lemmatiser", "irregular forms + plural/verb/adj rules"],
        ["Lexicon POS tagger", "lexicon + suffix heuristics (NN/VB/JJ/RB/DT/PRP/WH…)"],
        ["HMM POS tagger", "Hidden Markov Model with Viterbi decoding, trained on the FAQ corpus"],
        ["Damerau-Levenshtein spell-correct", "edit-distance ≤ 2 over FAQ vocabulary"],
        ["Synonym expansion", "curated medical dictionary"],
        ["Roman-Urdu normaliser", "~80-word phonetic dictionary (sar→head, dard→pain)"],
      ],
    },
    {
      title: "Document-level NLP",
      items: [
        ["Word TF-IDF", "unigrams + bigrams, sublinear TF"],
        ["Char TF-IDF", "3–5 char n-grams (typo/morphology tolerance)"],
        ["BM25 Okapi", "lexical scoring over lemmatised stream"],
        ["LSA topic model", "TruncatedSVD over the TF-IDF matrix"],
        ["PPMI word embeddings", "positive PMI + truncated SVD (classical word2vec)"],
        ["Kneser-Ney trigram LM", "interpolated smoothing for perplexity + autocomplete"],
        ["Word Mover's Distance", "relaxed WMD over PPMI embeddings (semantic similarity)"],
        ["Pseudo-relevance feedback", "Rocchio-lite query expansion from top docs"],
      ],
    },
    {
      title: "Query understanding",
      items: [
        ["Naive Bayes intent classifier", "12 classes, trained on 258 examples"],
        ["Question type classifier", "yes_no / what / why / how / when / choice"],
        ["Medical NER", "dictionary longest-match across 7 entity types"],
        ["Statistical NER", "Averaged structured perceptron + Viterbi decoding"],
        ["Noun-phrase chunker", "POS-pattern shallow parsing (DT? JJ* NN+)"],
        ["KG triple extractor", "SVO mining → 428 triples in data/kg_triples.jsonl"],
        ["Negation scope detector", "NegEx-style cue + window"],
        ["VADER-style sentiment", "lexicon + intensifiers + negation flip"],
        ["Triage / urgency detector", "3-tier red-flag regex"],
        ["TextRank keywords", "weighted PageRank over co-occurrence"],
        ["TextRank summariser", "sentence-cosine graph"],
        ["Slot extractor + coreference", "NER + regex; pronoun → last topic"],
      ],
    },
    {
      title: "Ranking + reranking",
      items: [
        ["Hybrid blender", "weighted ensemble of 5 channels (tuned via ablation)"],
        ["Reciprocal rank fusion", "for ranker-of-rankers"],
        ["MMR diversification", "diverse 'Did you mean?' alternatives"],
        ["Learning-to-rank", "LogReg over 14 features, gates on lexical uncertainty"],
        ["Confidence calibration", "soft-saturating curve to [0,1]"],
      ],
    },
    {
      title: "Dialog manager",
      items: [
        ["Session state machine", "active topic, slots, last intent, turn count"],
        ["Empathic opener generator", "sentiment + triage-aware"],
        ["Triage banner injector", "3-level emergency/moderate/mild"],
        ["Clarification trigger", "low-confidence + missing slots"],
        ["Disambiguation card", "near-tied alternatives"],
        ["Stem-overlap highlighter", "marks matched spans in the answer"],
      ],
    },
    {
      title: "Pipeline (chat logs → FAQ candidates)",
      items: [
        ["Ingest", "JSONL chat sessions (Mongo fallback)"],
        ["Segment", "user-question detection (English + Roman-Urdu starters)"],
        ["Normalize + PHI scrub", "regex masking of CNIC, phone, email, dates"],
        ["Embed", "TF-IDF L2-normalised vectors (no transformer)"],
        ["Cluster", "sklearn Agglomerative (cosine, per specialty)"],
        ["Select", "centroid-closest question + its bot reply"],
        ["Polish", "regex/string ops, max 4 sentences"],
        ["Publish", "Mongo or JSONL fallback to data/faq_candidates.jsonl"],
      ],
    },
  ];

  return (
    <section className="mt-12 grid grid-cols-1 lg:grid-cols-2 gap-5">
      {groups.map((g) => (
        <div
          key={g.title}
          className="rounded-2xl border border-stone-200 bg-white shadow-card p-5"
        >
          <h3 className="font-semibold text-lg mb-3">{g.title}</h3>
          <ul className="space-y-2">
            {g.items.map(([title, desc]) => (
              <li key={title} className="flex gap-3 items-baseline">
                <span className="h-1.5 w-1.5 rounded-full bg-stone-900 mt-2 shrink-0" />
                <div>
                  <p className="text-[13px] font-medium text-stone-900">
                    {title}
                  </p>
                  <p className="text-[12px] text-stone-600 leading-snug">
                    {desc}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}

function Channels() {
  const rows = [
    ["TF-IDF (word)", "0.20", "Unigram + bigram, sublinear TF"],
    ["TF-IDF (char)", "0.45", "3–5 char n-grams; strongest single signal"],
    ["BM25", "0.25", "Okapi over lemmatised tokens"],
    ["LSA topic", "0.05", "TruncatedSVD topic-space cosine"],
    ["PPMI embed", "0.05", "Classical word2vec, doc-vector cosine"],
  ];
  return (
    <section className="mt-10">
      <div className="rounded-2xl border border-stone-200 bg-white shadow-card p-5">
        <p className="text-[10px] uppercase tracking-[0.16em] text-stone-500 mb-2">
          Blended ranking weights (tuned by ablation)
        </p>
        <table className="w-full text-[13px]">
          <thead className="text-[10px] uppercase tracking-[0.14em] text-stone-500">
            <tr className="border-b border-stone-200">
              <th className="text-left py-2">Channel</th>
              <th className="text-right py-2 w-20">Weight</th>
              <th className="text-left py-2 pl-4">Notes</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([name, w, note]) => (
              <tr key={name} className="border-b border-stone-100 last:border-0">
                <td className="py-2 font-mono">{name}</td>
                <td className="py-2 text-right tabular-nums">
                  {w}
                </td>
                <td className="py-2 pl-4 text-stone-600">{note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Numbers() {
  return (
    <section className="mt-10 grid grid-cols-2 md:grid-cols-4 gap-4">
      {[
        ["Precision@1 (n=87)", "0.920"],
        ["MRR", "0.925"],
        ["Recall@5", "0.943"],
        ["Median latency", "20 ms"],
        ["FAQ corpus size", "139"],
        ["KG triples mined", "428"],
        ["NB intent examples", "258"],
        ["sklearn used", "no"],
      ].map(([k, v]) => (
        <div
          key={k}
          className="rounded-2xl border border-stone-200 bg-white p-5 shadow-card"
        >
          <p className="text-[10px] uppercase tracking-[0.14em] text-stone-500">
            {k}
          </p>
          <p className="text-2xl font-semibold mt-1 tabular-nums">{v}</p>
        </div>
      ))}
    </section>
  );
}
