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
          Every box below is a real Python module in <code>api/app/myml/</code>,
          {" "}<code>api/app/nlp/</code> or <code>api/app/services/</code>.
          No third-party ML library is used — every algorithm is hand-rolled
          in numpy (or, for the trainable transformer, in PyTorch as a
          tensor / autograd backend with every layer defined by us, no
          pretrained weights).
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
      title: "myml — in-house ML library (pure numpy)",
      items: [
        ["TF-IDF vectoriser", "word + char_wb analyzers, n-grams, sublinear TF (myml/tfidf.py)"],
        ["BM25 Okapi", "Lucene-style smoothed IDF, length-normalised TF (myml/bm25.py)"],
        ["Multinomial Naive Bayes", "Laplace smoothing, stable log-sum-exp (myml/nb.py)"],
        ["Logistic Regression", "batch GD + L2 + class weights, softmax CE (myml/logreg.py)"],
        ["Truncated SVD", "Halko-Martinsson-Tropp randomised SVD (myml/svd.py)"],
        ["K-Means", "k-means++ init, Lloyd iterations (myml/kmeans.py)"],
        ["MLP + backprop", "Kaiming init, ReLU/softmax, mini-batch SGD + momentum (myml/mlp.py)"],
        ["Multi-head self-attention", "scaled dot-product, LayerNorm, transformer block (myml/attention.py)"],
        ["Linear-chain CRF", "forward-backward + Viterbi, hashed features, SGD on NLL (myml/crf.py)"],
        ["Word2Vec skip-gram + neg sampling", "Mikolov 2013, subsampling + unigram^0.75 (myml/word2vec.py)"],
        ["Dual-encoder bi-encoder", "Siamese MLP towers + in-batch InfoNCE (myml/dual_encoder.py)"],
        ["BPE tokenizer", "Sennrich 2016, learned merges over the FAQ corpus (myml/bpe.py)"],
      ],
    },
    {
      title: "Trainable transformer (PyTorch — GPU ready)",
      items: [
        ["Architecture", "Embed → sinusoidal pos enc → N pre-LN transformer blocks → masked mean-pool → softmax. Every layer written by us."],
        ["No pretrained weights", "Random init only — nothing downloaded from HuggingFace/PyTorch hub."],
        ["Defaults", "d_model 64 · 4 heads · 2 layers · d_ff 128 · max_len 32"],
        ["Training", "AdamW + cosine LR schedule + grad-clip, cross-entropy loss"],
        ["Data", "data/intents.jsonl + intents_augmented.jsonl (308 → 1206 rows via 6-way augmentation)"],
        ["Hardware", "Auto-detects CUDA. 40 epochs in seconds on a GPU; ~3 min CPU"],
        ["Result", "Trains to final loss 0.0003, training accuracy 1.00, vocab 667, 13 classes"],
        ["Endpoint", "POST /nlp/torch_intent returns label + top-3 + device info"],
        ["Train command", "python api/train_transformer.py --verbose"],
      ],
    },
    {
      title: "Token-level NLP",
      items: [
        ["Tokenizer", "regex word + medical-aware stopwords"],
        ["Porter stemmer", "1980 algorithm, pure Python"],
        ["Rule-based lemmatiser", "irregular forms + plural / verb / adj rules"],
        ["Lexicon POS tagger", "lexicon + suffix heuristics (NN/VB/JJ/RB/DT/PRP/WH…)"],
        ["HMM POS tagger", "Hidden Markov Model with Viterbi decoding, silver-labelled training"],
        ["Damerau-Levenshtein spell-correct", "edit-distance ≤ 2 over FAQ vocabulary"],
        ["Synonym expansion", "curated medical dictionary"],
        ["Roman-Urdu normaliser", "~80-word phonetic dictionary (sar → head, dard → pain)"],
      ],
    },
    {
      title: "Document-level NLP",
      items: [
        ["Word TF-IDF", "unigrams + bigrams, sublinear TF (myml)"],
        ["Char TF-IDF", "3-5 char n-grams (myml)"],
        ["BM25 Okapi", "lexical scoring over lemmatised stream (myml)"],
        ["LSA topic model", "myml TruncatedSVD over the TF-IDF matrix"],
        ["PPMI word embeddings", "positive PMI + truncated SVD"],
        ["Word2Vec embeddings (myml)", "skip-gram + negative sampling, 64-dim, vocab 780"],
        ["Kneser-Ney trigram LM", "interpolated smoothing for perplexity + autocomplete"],
        ["Word Mover's Distance", "relaxed WMD over PPMI embeddings"],
        ["Pseudo-relevance feedback", "Rocchio-lite query expansion from top docs"],
      ],
    },
    {
      title: "Query understanding",
      items: [
        ["Rule-based intent (chitchat + meta)", "greeting / thanks / frustration / help / meta / question"],
        ["Naive Bayes intent", "12 classes, trained on 308 examples (myml NB + TF-IDF)"],
        ["MLP intent (myml)", "64 → 32 → softmax, trained from scratch in numpy"],
        ["Transformer intent (PyTorch, GPU)", "2-block encoder, trained from scratch on 1206 examples"],
        ["Question type classifier", "yes_no / what / why / how / when / choice"],
        ["Dictionary medical NER", "longest-match across 7 entity types"],
        ["Statistical NER", "averaged structured perceptron + Viterbi"],
        ["CRF NER", "linear-chain CRF with forward-backward + Viterbi (myml)"],
        ["Noun-phrase chunker", "POS-pattern shallow parsing (DT? JJ* NN+)"],
        ["KG triple extractor", "SVO mining → 518 triples in data/kg_triples.jsonl"],
        ["Negation scope detector", "NegEx-style cue + window"],
        ["VADER-style sentiment", "lexicon + intensifiers + negation flip"],
        ["Triage / urgency detector", "3-tier red-flag regex"],
        ["TextRank keywords + summary", "weighted PageRank over co-occurrence / sentence cosine"],
        ["Slot extractor + coreference", "NER + regex; pronoun → last topic"],
      ],
    },
    {
      title: "Ranking + reranking",
      items: [
        ["Hybrid blender", "weighted ensemble of 5 channels (TF-IDF word + char + BM25 + LSA + PPMI)"],
        ["Reciprocal rank fusion", "for ranker-of-rankers"],
        ["MMR diversification", "relevance × novelty over the wider candidate set"],
        ["Learning-to-rank", "myml LogReg over 14 query–doc features"],
        ["Dual-encoder neural retrieval", "myml Siamese MLP + InfoNCE, exposed at /nlp/dual_encoder"],
        ["Confidence calibration", "soft-saturating curve to [0, 1]"],
      ],
    },
    {
      title: "Dialog manager",
      items: [
        ["Session state machine", "active topic, slots, last intent, turn count"],
        ["Bot-identity guard", "'who are you?' → canned reply, never hits the retriever"],
        ["Empathic opener generator", "sentiment + triage-aware"],
        ["Triage banner injector", "3-level emergency / moderate / mild"],
        ["Clarification trigger", "low-confidence + missing slots"],
        ["Disambiguation card", "near-tied alternatives"],
        ["Stem-overlap highlighter", "marks matched spans in the answer"],
      ],
    },
    {
      title: "Data pipeline (chat logs → FAQ candidates)",
      items: [
        ["Ingest", "JSONL chat sessions (Mongo fallback)"],
        ["Segment", "user-question detection (English + Roman-Urdu starters)"],
        ["Normalize + PHI scrub", "regex masking of CNIC, phone, email, dates"],
        ["Embed", "myml TF-IDF L2-normalised vectors"],
        ["Cluster", "myml K-Means per specialty (no sklearn)"],
        ["Select", "centroid-closest question + its bot reply"],
        ["Polish", "regex / string ops, max 4 sentences"],
        ["Publish", "Mongo or JSONL fallback to data/faq_candidates.jsonl"],
      ],
    },
    {
      title: "Data corpus + augmentation",
      items: [
        ["169 clinician FAQs", "hand-written, smart-quotes normalised, dedup by normalised question key"],
        ["308 intent examples (curated)", "12 + 1 classes incl. meta, ask_definition, ask_preparation, ..."],
        ["1206 intent examples (augmented)", "synonym swaps, phrase swaps, prefix/suffix wrappers, typo injection"],
        ["116 held-out eval queries", "Precision@1, MRR, Recall@5"],
        ["32 BIO-tagged NER sentences", "+ silver labels over all FAQ questions"],
        ["518 KG triples", "extracted from FAQ answers via SVO mining"],
        ["96 sentiment lexicon entries", "with intensifier and diminisher multipliers"],
        ["18 chat-log sessions", "feed the FAQ-mining pipeline"],
      ],
    },
    {
      title: "Deployment",
      items: [
        ["Docker compose", "docker compose up → web + api + mongo + qdrant + redis"],
        ["FastAPI image", "~250 MB, 2-stage build, healthcheck"],
        ["Next.js image", "~150 MB, standalone output, non-root nextjs user"],
        ["Auto-seeding", "API seeds Mongo from data/faqs.jsonl on first boot"],
        ["In-memory fallback", "runs without Mongo when FAQ_FORCE_MEMORY=1"],
        ["GPU training", "pip install torch --index-url …/cu121 → python api/train_transformer.py"],
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
    ["TF-IDF (char)", "0.45", "3-5 char n-grams; strongest single signal"],
    ["BM25", "0.25", "Okapi over lemmatised tokens"],
    ["LSA topic", "0.05", "TruncatedSVD topic-space cosine"],
    ["PPMI embed", "0.05", "Classical word embedding, doc-vector cosine"],
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
                <td className="py-2 text-right tabular-nums">{w}</td>
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
        ["Precision@1 (n=116)", "0.931"],
        ["MRR", "0.938"],
        ["Recall@5", "0.948"],
        ["Median latency", "22 ms"],
        ["FAQ corpus", "169"],
        ["Intent examples", "1206"],
        ["Transformer accuracy", "1.000"],
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
