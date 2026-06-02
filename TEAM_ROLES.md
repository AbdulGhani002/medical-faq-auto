# MedFAQ — Team Roles

Four members. Every person owns a substantial slice of NLP work plus
supporting infrastructure. Roles are organised around the four big
NLP responsibilities of the project so that everyone can defend a
distinct technical contribution in the viva.

The work boundaries are deliberately drawn so each member can answer:
*"Here are the NLP techniques I built and trained, and here is how
they connect to the rest of the system."*

---

## Member 1 — Token + Retrieval (Abdul Ghani · F23607005)

**Focus.** Turning raw user text into a vector that can be matched
against the FAQ index. Owns everything from the moment the message
arrives to the moment a candidate FAQ is selected.

**NLP work (owned end to end).**
- Tokenisation, Porter stemmer (1980 algorithm), and the rule-based
  lemmatiser with irregular forms and morphology rules
- POS tagger: lexicon plus suffix heuristics, and the HMM POS tagger
  with Viterbi decoding trained on the FAQ corpus
- Damerau-Levenshtein spell corrector over the FAQ vocabulary
- Synonym expansion using a curated medical dictionary
- Roman Urdu phonetic normaliser (sar to head, dard to pain, etc.)
- TF-IDF vectoriser from scratch (word and char n-gram analysers)
- BM25 Okapi from scratch (smoothed IDF, length normalisation)
- LSA topic model using randomised truncated SVD
- PPMI word embeddings
- Word2Vec skip-gram with negative sampling, trained from scratch
- Byte-Pair Encoding tokenizer (Sennrich 2016)
- Interpolated Kneser-Ney n-gram language model
- Word Mover's Distance over PPMI embeddings
- Pseudo-relevance feedback (Rocchio) query expansion
- The 5-channel hybrid blender that combines TF-IDF word, TF-IDF
  char, BM25, LSA, PPMI scores into one ranked list

**Supporting work.**
- The Next.js chat widget UI, with the live NLP debug panel
- The /playground page that visualises every NLP layer in real time
- The score-breakdown popover showing per-channel scores

**Files owned.**
- `api/app/nlp/normalize.py`, `stem.py`, `lemmatize.py`, `pos.py`,
  `hmm_pos.py`, `spell.py`, `synonyms.py`, `roman_urdu.py`,
  `feedback.py`, `lm.py`, `wmd.py`, `indexer.py`
- `api/app/myml/tfidf.py`, `bm25.py`, `svd.py`, `linalg.py`,
  `word2vec.py`, `bpe.py`
- `web/src/components/ChatWidget.tsx`, `ScoreBreakdown.tsx`,
  `MessageBubble.tsx`
- `web/src/app/chat/[specialty]/page.tsx`,
  `web/src/app/playground/page.tsx`

---

## Member 2 — Information Extraction + Classification (Anas Bhatti · F23607044)

**Focus.** Pulling structured meaning out of the user text. Every
classifier and tagger that turns a sentence into labels, entities,
sentiment, or intent.

**NLP work (owned end to end).**
- Medical Named Entity Recognition: dictionary longest-match plus an
  averaged structured perceptron, and the linear-chain CRF written
  from scratch (forward-backward, Viterbi, hashed features, SGD on
  the negative log-likelihood)
- Negation scope detector (NegEx-style cue plus window)
- VADER-style sentiment analyser with intensifiers and negation flip
- 3-tier triage and urgency detector (red-flag regex)
- Question-type classifier (yes_no / what / why / how / when / choice)
- Slot extractor that turns NER plus regex into a structured slot map
- TextRank keyword extractor (weighted PageRank over co-occurrence)
- TextRank extractive summariser (sentence-cosine graph)
- Knowledge-graph triple extractor (SVO mining over FAQ answers)
- Naive Bayes intent classifier (myml NB plus TF-IDF, 12 classes,
  trained on 387 curated examples)
- MLP intent classifier with backprop, from scratch in numpy
- **Transformer-based intent classifier** in PyTorch, with every
  layer (attention, FFN, LayerNorm, positional encoding) defined by
  hand. Trained on 1517 augmented examples. Final loss 0.0002,
  training accuracy 1.000.

**Supporting work.**
- The /architecture page write-up: the SVG diagram, the technique
  table, the metric tiles
- The NLP debug panel component that renders intent + sentiment +
  triage + entities + keywords in the chat reply
- The intent classifier evaluation report (held-out F1 plus
  confusion matrix)

**Files owned.**
- `api/app/nlp/ner.py`, `ner_stat.py`, `negation.py`, `sentiment.py`,
  `triage.py`, `qtype.py`, `slots.py`, `keywords.py`, `summarize.py`,
  `kg.py`, `intent.py`, `nb_intent.py`, `mlp_intent.py`
- `api/app/myml/nb.py`, `logreg.py`, `crf.py`, `attention.py`,
  `torch_transformer.py`
- `api/app/services/crf_ner.py`
- `api/app/services/analyzer.py`
- `api/train_transformer.py`, `api/intent_eval.py`
- `web/src/components/NLPPanel.tsx`,
  `web/src/app/architecture/page.tsx`,
  `web/src/components/ArchitectureDiagram.tsx`

---

## Member 3 — Generation, Dialog, Auto-FAQ (Muhammad Salman · F23607037)

**Focus.** Writing the bot's reply, holding the conversation, and
closing the loop from chat traffic back to new FAQs. Owns the two
heaviest from-scratch neural models in the project.

**NLP work (owned end to end).**
- **Seq2seq encoder-decoder with Bahdanau attention** in PyTorch,
  every layer (bi-LSTM encoder, additive attention, LSTM decoder,
  output head) defined by hand. Teacher-forced cross-entropy training
  with cosine LR and gradient clipping. Greedy decoding at inference.
- The grounded generation service: generates a candidate reply,
  scores its cosine similarity against the retrieved FAQ, falls back
  to the retrieved text when the generation drifts (so the bot can
  never invent off-corpus medical content)
- MLP with backprop from scratch
- Dual encoder bi-encoder (Siamese MLP) trained with in-batch InfoNCE
- K-Means clustering from scratch (k-means++ initialisation, Lloyd
  iterations)
- Real-time **auto-FAQ mining**: every chat turn that scores below
  the threshold goes into a per-specialty queue; the queue is
  clustered every 5 turns; clusters of size 3 or more become
  candidate FAQs that appear in the admin dashboard with
  `auto_generated = True`
- Dialog manager: empathic opener generator, triage banner injector,
  clarification trigger, disambiguation card, stem-overlap span
  highlighter, follow-up suggestion
- MMR diversification for the "Did you mean" alternatives
- Learning-to-rank reranker (logistic regression over 14 features)
- Pronoun coreference resolution
- Live FAQ count tracker that increments the matched FAQ via
  `$inc` in MongoDB on every successful chat turn

**Supporting work.**
- The PyTorch training scripts for both neural models, with GPU auto
  detection
- The admin "candidate FAQs" view and approve / reject workflow

**Files owned.**
- `api/app/myml/seq2seq.py`, `mlp.py`, `dual_encoder.py`, `kmeans.py`,
  `mmr.py`
- `api/app/services/generator.py`, `auto_faq.py`,
  `services/neural_models.py`, `services/torch_intent.py`
- `api/app/nlp/dialog.py`, `coref.py`, `ltr.py`, `highlight.py`,
  `context.py`, `topic.py`
- `api/train_seq2seq.py`
- `api/app/routers/chat.py`
- `api/app/services/retrieval.py` (the orchestrator that calls all of
  the above into one chat reply)

---

## Member 4 — Data, Evaluation, Deployment (5th group member)

**Focus.** Owning the corpus, the augmentation, the measurement, and
the path from a fresh laptop to a running stack. All four members
agreed the project lives or dies on this work too.

**NLP work (owned end to end).**
- The 214 hand-written clinician-style FAQs across radiology,
  physiotherapy, and cardiology. Wrote, normalised (smart-quote
  cleanup), and deduplicated using a normalised question-key
- Three rounds of corpus expansion: `expand_corpus.py`,
  `expand_corpus_v2.py`, `expand_corpus_v3.py`
- 6-way intent augmentation (`augment_intents.py`): synonym swap,
  phrase swap, prefix variant, casing change, single typo, prefix
  plus suffix combo. Grew 387 curated intents into 1517 examples.
- Synthetic chat-log generator (`synth_chat_logs.py`) with paraphrase
  rules, Roman-Urdu sprinkles and follow-up turns. Produced 14,357
  realistic patient sessions across all three specialties.
- 156 held-out evaluation queries with expected-keyword labels
- 32 BIO-tagged NER training sentences (handed off to Member 2)
- The 96-entry VADER-style sentiment lexicon (handed off to Member 2)
- PHI scrub regex set for CNIC, phone, email, dates
- The offline chat-log to FAQ-candidate **pipeline** (ingest, segment,
  normalise, embed using TF-IDF, cluster using K-Means, select,
  polish, publish). Lives in `pipeline/`.
- The evaluation harness (`api/eval.py`) reporting Precision at 1,
  MRR, Recall at 5, median and p95 latency, per-specialty breakdown

**Supporting work.**
- The MongoDB schema and auto-seeding from JSONL on first boot
- The in-memory fallback store that lets the API run without Mongo
- The full Docker stack (api Dockerfile, web Dockerfile, healthchecks
  in `docker-compose.yml`)
- The FastAPI router layer (`/chat`, `/faq`, `/admin`, `/nlp`,
  `/stats`)
- The integration suite (`api/final_test.py`) and end-to-end test
  (`api/e2e_test.py`)
- The pytest unit suite, the ablation study, the intent evaluation
- The slide deck, the project documentation PDF, the regeneration
  scripts (`make_slides.py`, `make_pdf.py`)
- The Desktop deliverable RAR archive

**Files owned.**
- All `data/*.json` and `data/*.jsonl` files
- `data/build_jsonl.py`, `augment_intents.py`, `synth_chat_logs.py`,
  `expand_corpus*.py`
- `pipeline/` (the whole offline mining job)
- `api/app/db.py`, `seed.py`
- `api/app/routers/*.py`
- `api/app/services/phi_scrub.py`, `chat_logger.py`, `datasets.py`
- `api/app/main.py`, `config.py`, `models.py`
- `api/eval.py`, `final_test.py`, `e2e_test.py`, `intent_eval.py`,
  `ablate.py`, `tests/`
- `docker-compose.yml`, `api/Dockerfile`, `web/Dockerfile`,
  `api/.dockerignore`, `web/.dockerignore`
- `make_slides.py`, `make_pdf.py`, `README.md`, `SLIDES.md`

---

## Summary of NLP ownership

| Area | Member |
|---|---|
| Tokenisation, stemming, lemmatisation | 1 |
| POS tagging (lexicon + HMM) | 1 |
| Spell correction, synonym expansion | 1 |
| Roman-Urdu normalisation | 1 |
| TF-IDF, BM25, LSA, PPMI, Word2Vec, BPE | 1 |
| Kneser-Ney LM, Word Mover's Distance, PRF | 1 |
| Hybrid retrieval blender | 1 |
| Medical NER (dictionary + perceptron + CRF) | 2 |
| Negation, sentiment, triage | 2 |
| Question type, slot extraction | 2 |
| TextRank keywords + summary, KG triples | 2 |
| Naive Bayes / MLP / Transformer intent | 2 |
| Seq2seq with Bahdanau attention | 3 |
| MLP, dual encoder, K-Means | 3 |
| Grounded generation service | 3 |
| Auto-FAQ real-time miner | 3 |
| Dialog manager, MMR, LTR, coreference | 3 |
| FAQ corpus (214 hand-written) | 4 |
| 6-way intent augmentation | 4 |
| Synthetic chat-log generator (14k sessions) | 4 |
| PHI scrub, evaluation harness | 4 |
| Offline mining pipeline | 4 |

Every member has at least one trainable model or a classifier as
their core contribution. Every member built at least one of the
algorithms in `api/app/myml/` from scratch.
