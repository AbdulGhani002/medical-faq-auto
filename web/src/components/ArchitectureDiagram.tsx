/**
 * Full system architecture as one hand-laid-out SVG.
 *
 * Reads top-down: user input → preprocessing → query understanding →
 * 5-channel hybrid retrieval → blend & rerank → dialog → reply, plus
 * a side lane for the trainable neural models (MLP, dual encoder,
 * transformer, CRF) and the data corpus on the right.
 *
 * Pure SVG, no chart library, no dependency.
 */
export default function ArchitectureDiagram() {
  return (
    <div className="rounded-2xl border border-stone-200 bg-white shadow-card p-3 overflow-x-auto">
      <svg
        viewBox="0 0 1180 920"
        className="w-full min-w-[900px] block"
        role="img"
        aria-label="MedFAQ system architecture"
      >
        <defs>
          <marker
            id="arr"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path d="M0,0 L10,5 L0,10 z" fill="#1c1917" />
          </marker>
          <pattern
            id="dots"
            width="14"
            height="14"
            patternUnits="userSpaceOnUse"
          >
            <circle cx="1" cy="1" r="1" fill="#e7e5e4" />
          </pattern>
        </defs>

        <rect width="1180" height="920" fill="url(#dots)" />

        {/* Lane backgrounds */}
        <Lane x={20} y={20}  w={1140} h={70}  label="USER INPUT" />
        <Lane x={20} y={110} w={1140} h={120} label="PRE-PROCESSING" />
        <Lane x={20} y={250} w={1140} h={130} label="QUERY UNDERSTANDING" />
        <Lane x={20} y={400} w={1140} h={140} label="5-CHANNEL HYBRID RETRIEVAL" />
        <Lane x={20} y={560} w={1140} h={110} label="RANK · RERANK · DIALOG" />
        <Lane x={20} y={690} w={1140} h={50}  label="REPLY ENVELOPE" />
        <Lane x={20} y={760} w={1140} h={140} label="TRAINABLE NEURAL MODELS (FROM SCRATCH, GPU-READY)" />

        {/* Row 1 - user input */}
        <Block x={490} y={35} w={200} h={40}
               title="User message"
               subtitle="EN / Roman-Urdu, voice or text"
               tone="ink" />

        {/* Row 2 - preprocessing */}
        <Block x={60}  y={130} w={180} h={70}
               title="PHI scrubber"
               subtitle="CNIC, phone, email, dates → masked" />
        <Block x={260} y={130} w={180} h={70}
               title="Roman-Urdu expand"
               subtitle="sar → head, dard → pain" />
        <Block x={460} y={130} w={180} h={70}
               title="Coreference"
               subtitle={'"it" → last topic'} />
        <Block x={660} y={130} w={180} h={70}
               title="Context augment"
               subtitle="follow-up detection" />
        <Block x={860} y={130} w={180} h={70}
               title="Spell-correct"
               subtitle="Damerau-Levenshtein ≤ 2 over vocab" />

        {/* Row 3 - query understanding */}
        <Block x={60}   y={270} w={140} h={80}
               title="Tokeniser"  subtitle="regex + stop" />
        <Block x={220}  y={270} w={140} h={80}
               title="Lemmatiser" subtitle="rules + Porter" />
        <Block x={380}  y={270} w={140} h={80}
               title="POS tagger" subtitle="lexicon + HMM" />
        <Block x={540}  y={270} w={140} h={80}
               title="Intent"     subtitle="NB · MLP · Transformer" />
        <Block x={700}  y={270} w={140} h={80}
               title="NER"        subtitle="dict + percept + CRF" />
        <Block x={860}  y={270} w={140} h={80}
               title="Negation"   subtitle="NegEx scope" />
        <Block x={1020} y={270} w={140} h={80}
               title="Sentiment + " subtitle="triage cues" />

        {/* Row 4 - retrieval channels */}
        <Channel x={60}  y={425} title="TF-IDF (word)"     weight="0.20" tone="purple" />
        <Channel x={290} y={425} title="TF-IDF (char 3-5)" weight="0.45" tone="amber" />
        <Channel x={520} y={425} title="BM25 Okapi"        weight="0.25" tone="emerald" />
        <Channel x={750} y={425} title="LSA topic (SVD)"   weight="0.05" tone="sky" />
        <Channel x={980} y={425} title="PPMI embeddings"   weight="0.05" tone="rose" />

        {/* Row 5 - rank / rerank / dialog */}
        <Block x={60}   y={580} w={170} h={70}
               title="Weighted blend"  subtitle="5-channel ensemble" tone="ink" />
        <Block x={250}  y={580} w={170} h={70}
               title="PRF (Rocchio)"   subtitle="2-pass expansion" />
        <Block x={440}  y={580} w={170} h={70}
               title="LTR rerank"      subtitle="LogReg, 14 feats" />
        <Block x={630}  y={580} w={170} h={70}
               title="MMR diversify"   subtitle="relevance × novelty" />
        <Block x={820}  y={580} w={170} h={70}
               title="Dialog manager"  subtitle="opener · clarif · disambig" />
        <Block x={1010} y={580} w={150} h={70}
               title="Highlighter"     subtitle="stem overlap span" />

        {/* Row 6 - reply envelope */}
        <Block x={310} y={705} w={560} h={30}
               title="answer + matched FAQ + score breakdown + NLP analysis + dialog meta"
               tone="ink" />

        {/* Row 7 - trainable neural models */}
        <Block x={40}   y={780} w={210} h={100}
               title="MLP (myml)"
               subtitle="backprop · 64-32 · SGD + momentum"
               tone="purple" />
        <Block x={270}  y={780} w={210} h={100}
               title="Dual encoder (myml)"
               subtitle="Siamese MLP · InfoNCE · in-batch negatives"
               tone="emerald" />
        <Block x={500}  y={780} w={210} h={100}
               title="Word2Vec (myml)"
               subtitle="skip-gram + neg sampling · 64-d · vocab 780"
               tone="sky" />
        <Block x={730}  y={780} w={210} h={100}
               title="CRF NER (myml)"
               subtitle="forward-backward · Viterbi · 171 examples"
               tone="rose" />
        <Block x={960}  y={780} w={180} h={100}
               title="Transformer (PyTorch)"
               subtitle="2 layers · 4 heads · d=64 · GPU · acc 1.00"
               tone="ink" />

        {/* Arrows between lanes */}
        <Arrow x1={590} y1={75}  x2={590} y2={130} />
        <Arrow x1={590} y1={200} x2={590} y2={270} />
        <Arrow x1={590} y1={350} x2={590} y2={425} />
        <Arrow x1={590} y1={500} x2={590} y2={580} />
        <Arrow x1={590} y1={650} x2={590} y2={705} />
      </svg>

      <p className="px-3 pb-2 pt-3 text-[11px] text-stone-500">
        All boxes above are real Python modules under{" "}
        <code className="text-stone-700">api/app/</code>. The bottom lane
        is the from-scratch neural stack — every weight is randomly
        initialised and trained in-process (no pretrained downloads).
        The transformer auto-uses CUDA when available via{" "}
        <code className="text-stone-700">python api/train_transformer.py</code>.
      </p>
    </div>
  );
}

// ---------- atoms ----------

const TONES = {
  ink: { fill: "#1c1917", stroke: "#1c1917", text: "#fafaf9" },
  purple: { fill: "#ede9fe", stroke: "#7c3aed", text: "#4c1d95" },
  amber: { fill: "#fef3c7", stroke: "#d97706", text: "#78350f" },
  emerald: { fill: "#d1fae5", stroke: "#059669", text: "#064e3b" },
  sky: { fill: "#e0f2fe", stroke: "#0284c7", text: "#0c4a6e" },
  rose: { fill: "#ffe4e6", stroke: "#e11d48", text: "#881337" },
  default: { fill: "#ffffff", stroke: "#1c1917", text: "#1c1917" },
} as const;

type Tone = keyof typeof TONES;

function Lane({
  x, y, w, h, label,
}: {
  x: number; y: number; w: number; h: number; label: string;
}) {
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx="14"
            fill="#fafaf9" stroke="#e7e5e4" />
      <text x={x + 16} y={y + 16} fontSize="9"
            letterSpacing="0.18em" fill="#a8a29e">
        {label}
      </text>
    </g>
  );
}

function Block({
  x, y, w, h, title, subtitle, tone = "default" as Tone,
}: {
  x: number; y: number; w: number; h: number;
  title: string; subtitle?: string; tone?: Tone;
}) {
  const t = TONES[tone];
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx="10"
            fill={t.fill} stroke={t.stroke} strokeWidth="1.4" />
      <text x={x + w / 2}
            y={y + (subtitle ? h / 2 - 4 : h / 2 + 4)}
            textAnchor="middle" fontSize="12" fontWeight="600"
            fill={t.text}>
        {title}
      </text>
      {subtitle && (
        <text x={x + w / 2} y={y + h / 2 + 12}
              textAnchor="middle" fontSize="10"
              fill={t.text} opacity="0.75">
          {subtitle}
        </text>
      )}
    </g>
  );
}

function Channel({
  x, y, title, weight, tone,
}: {
  x: number; y: number; title: string; weight: string; tone: Tone;
}) {
  const t = TONES[tone];
  return (
    <g>
      <rect x={x} y={y} width={170} height={90} rx="12"
            fill={t.fill} stroke={t.stroke} strokeWidth="1.6" />
      <text x={x + 85} y={y + 32} textAnchor="middle"
            fontSize="13" fontWeight="600" fill={t.text}>
        {title}
      </text>
      <text x={x + 85} y={y + 56} textAnchor="middle"
            fontSize="10" letterSpacing="0.16em"
            fill={t.text} opacity="0.6">
        WEIGHT
      </text>
      <text x={x + 85} y={y + 78} textAnchor="middle"
            fontSize="20" fontWeight="700" fill={t.text}>
        {weight}
      </text>
    </g>
  );
}

function Arrow({
  x1, y1, x2, y2,
}: {
  x1: number; y1: number; x2: number; y2: number;
}) {
  return (
    <line x1={x1} y1={y1} x2={x2} y2={y2}
          stroke="#1c1917" strokeWidth="1.6"
          markerEnd="url(#arr)" />
  );
}
