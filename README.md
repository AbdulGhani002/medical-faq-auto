# Medical FAQ Auto-Generation System

Semester project. Auto-generates FAQs from medical chatbot logs for
**Radiology**, **Physiotherapy**, and **Cardiovascular** specialties.

> Fully retrieval-based. No LLM is used anywhere. **Every ML algorithm
> is implemented from scratch in pure numpy** (`api/app/myml/`). Every
> answer the user sees is a real, clinician-written reply selected by
> our pipeline.

## Quick start (Docker — recommended)

```bash
docker compose up --build
```

Then open:

| URL | What it is |
|---|---|
| http://localhost:3000 | Next.js web UI (chat, playground, architecture, admin) |
| http://localhost:8000/docs | FastAPI swagger / OpenAPI |
| http://localhost:8000/health | Liveness probe |

The stack consists of five services:

| Service | Role |
|---|---|
| **`web`** | Next.js 15 frontend (standalone build, ~150 MB image) |
| **`api`** | FastAPI backend + the in-house ML stack |
| **`mongo`** | MongoDB (auto-seeded from `data/faqs.jsonl` on first boot) |
| **`qdrant`** | (Reserved for the pipeline) |
| **`redis`** | (Reserved for the pipeline) |

If you don't want Mongo, set `FAQ_FORCE_MEMORY=1` in the `api` service
environment — the API will load FAQs from `data/faqs.jsonl` directly.

### Smoke test after `docker compose up`

```bash
curl http://localhost:8000/health
curl http://localhost:8000/faq/radiology
curl -X POST http://localhost:8000/chat \
  -H 'content-type: application/json' \
  -d '{"session_id":"s1","specialty":"radiology","text":"do i need to fast before my mri?"}'
```

## Quick start (local Python — for hacking)

```powershell
# Backend (Python 3.11+)
cd api
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
$env:FAQ_FORCE_MEMORY = "1"
python -m uvicorn app.main:app --port 8000

# Frontend (Node 20+)
cd web
npm install
npm run dev
```

## What's inside

### In-house ML library — `api/app/myml/`
Every algorithm written in pure numpy. No `scikit-learn`, no `rank_bm25`,
no `sentence-transformers`, no model downloads.

| File | Technique |
|---|---|
| `linalg.py` | cosine similarity, L2 normalisation, randomised SVD (Halko-Martinsson-Tropp) |
| `tfidf.py` | TF-IDF vectoriser with `word` and `char_wb` analysers |
| `bm25.py` | BM25 Okapi (Lucene-style smoothed IDF) |
| `nb.py` | Multinomial Naive Bayes with Laplace smoothing |
| `logreg.py` | Multinomial logistic regression, batch GD + L2 + class weights |
| `svd.py` | Truncated SVD wrapper |
| `kmeans.py` | K-Means with k-means++ initialisation |
| `mlp.py` | Multi-layer perceptron with backprop, mini-batch SGD + momentum |
| `attention.py` | Multi-head scaled dot-product self-attention, LayerNorm, transformer encoder block |
| `crf.py` | Linear-chain CRF — forward-backward + Viterbi, hashed features, SGD on NLL |
| `word2vec.py` | Skip-gram with negative sampling (Mikolov 2013) |
| `dual_encoder.py` | Siamese bi-encoder + in-batch InfoNCE contrastive loss |
| `bpe.py` | Byte-pair encoding (Sennrich 2016) |
| `torch_transformer.py` | **Trainable** transformer encoder + intent classifier in PyTorch. Every layer (attention, FFN, LayerNorm, pos enc) defined by us — no `nn.Transformer`, no pretrained weights. CPU + GPU. Train with `python api/train_transformer.py`. |

### Trained models
```bash
# Train the transformer (uses GPU automatically if CUDA is available)
cd api && python train_transformer.py --verbose
# Auto-detects device → "cuda" or "cpu"
# Runs ~60 epochs over data/intents.jsonl + data/intents_augmented.jsonl
# Saves to api/app/myml/checkpoints/torch_intent.pt
```

After training, the API exposes `POST /nlp/torch_intent` which serves
predictions from the saved checkpoint.

### NLP layer — `api/app/nlp/`
Stem (Porter), lemmatise (rule-based), lexicon POS, HMM POS (Viterbi),
medical NER (dictionary + structured perceptron + CRF), negation
(NegEx), sentiment (VADER-style lexicon), triage detector, Naive Bayes
intent + MLP neural intent, question-type classifier, TextRank
keywords + summary, LSA topic model, PPMI word embeddings,
pseudo-relevance feedback, MMR diversification, Roman-Urdu phonetic
normaliser, dialog state manager, learning-to-rank reranker, coreference,
N-gram language model (interpolated Kneser-Ney), NP chunker,
knowledge-graph (SVO) triple extractor, Word Mover's Distance.

### Repo layout

```
medical-faq-proposal/
  README.md
  docker-compose.yml         # the one command that starts everything
  NLP_UPGRADE_REPORT.md      # technical writeup
  EVALUATION_REPORT.md       # eval numbers
  Medical_FAQ_Proposal.pdf   # original project proposal

  web/                       # Next.js 15 frontend
    Dockerfile               # 3-stage build → ~150 MB image
    src/app/                 # routes: /, /chat, /faq, /playground, /architecture, /admin
    src/components/          # ChatWidget, NLPPanel, ArchitectureDiagram, ...

  api/                       # FastAPI backend
    Dockerfile               # 2-stage build → ~250 MB image
    app/myml/                # ML implemented from scratch (numpy only)
    app/nlp/                 # text-level NLP modules
    app/routers/             # /chat, /faq, /admin, /nlp, /stats
    app/services/            # retrieval, analyzer, datasets, neural_models
    eval.py                  # Precision@1 / MRR / Recall@5
    final_test.py            # full integration smoke
    e2e_test.py              # end-to-end NLP scenarios

  pipeline/                  # chat-log → FAQ-candidate pipeline (no LLM)
    pipeline/runner.py
    pipeline/stages/         # ingest, segment, normalize, embed, cluster, select, polish, publish

  data/
    faqs.jsonl               # 139 clinician FAQs (10 overview + ~129 detail)
    intents.jsonl            # 258 intent training examples
    ner_examples.jsonl       # 12 BIO-tagged sentences
    eval_queries.jsonl       # 87 evaluation queries
    chat_logs.jsonl          # synthetic chat sessions
    sentiment_lexicon.jsonl  # 96 polarity weights
    kg_triples.jsonl         # extracted SVO triples (regenerated on demand)
    dataset_manifest.json
    build_jsonl.py           # regenerate every JSONL
```

## Tests

```bash
# Integration: hits the live API + web on docker
docker compose up -d
python api/final_test.py          # 62/62 PASS

# Retrieval evaluation: Precision@1, Recall@5, MRR
python api/eval.py
#   Precision@1 : 0.920
#   MRR         : 0.925
#   Recall@5    : 0.943
#   p50 latency : 20 ms
```

## Group members

| # | Member | Focus area |
|---|---|---|
| 1 | Abdul Ghani (F23607005) | Frontend and UI |
| 2 | Anas Bhatti (F23607044)  | Conversation processing |
| 3 | Muhammad Salman (F23607037) | Embedding and clustering |
| 4 | [Member 4] | Backend, APIs, data |
| 5 | [Member 5] | Selection, issues, eval |
