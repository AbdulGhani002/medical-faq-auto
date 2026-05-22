# MedFAQ — Slide deck

Source for the PowerPoint generator (`make_slides.py`) and also a
standalone readable handout.

---

## 1. Title

**MedFAQ — Auto-Generated Medical FAQ Assistant**

A semester project that builds a clinician-grade chatbot for
Radiology, Physiotherapy and Cardiology without using any pretrained
LLM. Every model is trained from scratch in numpy or PyTorch.

NUTECH, 6th semester · Group: Abdul Ghani · Anas Bhatti · Muhammad Salman · +2

---

## 2. Scope and requirements

**Problem.** Patients ask the same dozens of questions every week.
Clinicians want a single source of truth without delegating to a
generative LLM that can hallucinate.

**Goal.** Build a retrieval-based chatbot that:
- answers from an approved, clinician-reviewed FAQ index
- supports three specialties (Radiology, Physiotherapy, Cardiovascular)
- never invents text — every reply is a real human-written answer
- runs locally, no API keys, no external model downloads

**Constraints.**
- No LLM, no pretrained transformer, no sentence-transformers
- Every ML algorithm must be built by us (numpy or PyTorch)
- Must work on a laptop and in Docker
- Pakistan context: Roman-Urdu phonetic input, salaam/shukria handling

---

## 3. Pipeline

User message → PHI scrub → Roman-Urdu phonetic expand → coreference
("it" → last topic) → context augmentation → Damerau-Levenshtein
spell-correct.

Then 5-channel hybrid retrieval:
- TF-IDF word (weight 0.20)
- TF-IDF char (weight 0.45)
- BM25 Okapi (weight 0.25)
- LSA topic (weight 0.05)
- PPMI word embeddings (weight 0.05)

Followed by PRF query expansion (Rocchio-lite), MMR diversification,
learning-to-rank, and a dialog manager that wraps the answer with
opener, triage banner, span highlights and disambiguation cards.

A separate "chat-log → FAQ candidate" pipeline runs offline:
ingest → segment → normalise → embed (TF-IDF) → cluster (K-Means)
→ extractive select → polish → publish.

---

## 4. Dataset

| Source | Records | Description |
|---|---:|---|
| `data/faqs.jsonl` | 169 | Hand-written clinician-style FAQs across 3 specialties |
| `data/intents.jsonl` | 308 | Curated intent training examples, 13 classes |
| `data/intents_augmented.jsonl` | 1206 | 6-way augmentation: synonyms, prefixes, typos, casing |
| `data/eval_queries.jsonl` | 116 | Held-out evaluation queries with expected keywords |
| `data/ner_examples.jsonl` | 32 | BIO-tagged sentences for the CRF NER |
| `data/sentiment_lexicon.jsonl` | 96 | Polarity weights + intensifiers |
| `data/chat_logs.jsonl` | 18 | Synthetic patient sessions for the mining pipeline |
| `data/kg_triples.jsonl` | 518 | Auto-mined (subject, predicate, object) triples |

Every FAQ has been smart-quote normalised, deduplicated, and the
counts persist in MongoDB live so popular FAQs surface to the top
of `/faq/{specialty}`.

---

## 5. Models (every one built from scratch)

**In-house numpy stack — `api/app/myml/`**
- TF-IDF vectoriser (word + char n-grams, sublinear TF)
- BM25 Okapi with Lucene-style smoothed IDF
- Multinomial Naive Bayes with Laplace smoothing
- Multinomial Logistic Regression (batch GD + L2)
- Randomised Truncated SVD (Halko, Martinsson, Tropp 2011)
- K-Means with k-means++
- MLP with backprop, Kaiming init, momentum SGD
- Multi-head self-attention + LayerNorm + transformer block
- Linear-chain CRF (forward-backward + Viterbi)
- Word2Vec skip-gram + negative sampling (Mikolov 2013)
- Dual encoder bi-encoder + in-batch InfoNCE
- Byte-Pair Encoding tokenizer (Sennrich 2016)

**Trainable transformer — `api/app/myml/torch_transformer.py`**
- PyTorch tensors + autograd only — every layer (attention, FFN,
  LayerNorm, positional encoding, embedding) defined by us
- No pretrained weights, no `nn.Transformer`
- 2 encoder blocks · 4 heads · d=64 · d_ff=128 · max_len=32
- Trained on the 1206-row augmented intent corpus
- AdamW + cosine LR schedule + grad clip
- GPU auto-detected — finishes in seconds with CUDA, ~3 min CPU

---

## 6. Evaluation

| Metric | Value |
|---|---:|
| Eval queries | 116 |
| Precision@1 | 0.931 |
| MRR | 0.938 |
| Recall@5 | 0.948 |
| Median latency | 22 ms |
| p95 latency | 47 ms |

Per-specialty:

| Specialty | n | P@1 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| Radiology | 36 | 0.861 | 0.889 | 0.870 |
| Physiotherapy | 35 | 0.971 | 0.971 | 0.971 |
| Cardiovascular | 45 | 0.956 | 0.978 | 0.967 |

Transformer intent classifier: **train accuracy 1.000**,
final cross-entropy loss 0.0003 after 40 epochs.

Integration suite: **62 / 62 PASS**.

---

## 7. Strengths

- **No LLM dependency.** Reproducible, auditable, no API costs, no
  hallucinations.
- **Every algorithm is ours.** Drop-in replacements for sklearn,
  rank_bm25 and sentence-transformers. Total ~3000 LoC.
- **Hybrid retrieval works.** P@1 0.93 across 116 held-out queries
  with 22 ms p50 latency.
- **Multi-turn dialog.** Coreference, topic tracking, slot filling,
  triage banners, empathic openers, disambiguation cards.
- **Pakistan-friendly.** Roman-Urdu phonetic mapping (`sar → head`,
  `dard → pain`), 1122 emergency banner, no PHI leakage.
- **One-command deploy.** `docker compose up` brings web + api +
  mongo + qdrant + redis live with auto-seeding from JSONL.
- **Real-time analytics.** FAQ counts increment on every match,
  persisted in Mongo, surfaced in the admin dashboard.

## Limitations

- Small corpus (169 FAQs, 116 eval queries). P@1 numbers will hold
  only for questions covered by the corpus. Out-of-distribution
  queries get "best-guess" or "no good match" responses.
- Transformer trained on 1206 augmented intent examples — risks
  overfitting; we mitigate with weight decay + cosine LR but the
  test set is still self-augmented.
- NER is dictionary-first. The CRF + structured perceptron variants
  improve it but the BIO data is only 32 hand-annotated sentences.
- Roman-Urdu coverage is heuristic (80-word dictionary).
- Web Speech voice input only works in Chrome / Edge.

## Future direction

- Grow the FAQ corpus to 500+ with clinician validation.
- Train the dual encoder bi-encoder on real labeled query–FAQ pairs
  (right now it learns from auto-derived positives only).
- Add an offline active-learning loop: when retrieval confidence
  drops below threshold, queue the message for clinician review and
  feed approved Q/A pairs back into the corpus.
- True Urdu-script input via a transliteration model trained on a
  parallel corpus.
- A second eval pass with a clinician-rated ranking metric (NDCG)
  rather than a keyword match heuristic.
- Optional GPU service container so heavier neural models become a
  one-click extension.

---

## 8. Demo

Open `http://localhost:3000` after `docker compose up`:
- `/chat/radiology` — full chatbot with NLP debug panel
- `/playground` — type any sentence, see every NLP layer live
- `/architecture` — system architecture diagram
- `/admin` — analytics dashboard with live FAQ counts
- `/faq/{specialty}` — browse the approved index

Train the transformer on your own GPU:
```
pip install torch --index-url https://download.pytorch.org/whl/cu121
cd api && python train_transformer.py --verbose
```
