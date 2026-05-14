# Medical FAQ Auto-Generation System

Semester project. Auto-generate FAQs from medical chatbot logs for
**Radiology**, **Physiotherapy**, and **Cardiovascular** specialties.

The chatbot is fully retrieval-based. No LLM is used anywhere.
Every answer the user sees is a real, human-written reply selected by
our pipeline.

## Repo layout

```
medical-faq-proposal/
  Medical_FAQ_Proposal.pdf   # the project proposal (final PDF)
  generate_proposal.py       # script that regenerates the proposal
  README.md                  # you are here
  docker-compose.yml         # MongoDB, Qdrant, Redis
  .gitignore

  web/                       # Next.js 15 frontend (TypeScript, Tailwind)
    src/app/                 # routes: landing, chat, faq, admin
    src/components/          # ChatWidget, FAQList, SpecialtyCard
    src/lib/                 # API client + types

  api/                       # FastAPI backend (Python 3.11)
    app/routers/             # /chat, /faq, /admin
    app/services/            # retrieval, chat logger, PHI scrub

  pipeline/                  # NLP pipeline (no LLM)
    pipeline/runner.py       # CLI runner
    pipeline/stages/         # ingest, segment, normalize, embed,
                             # cluster, select, polish, publish

  data/
    seed_faqs.json           # initial FAQ pool (3 per specialty)
    templates.json           # template patterns for synthetic Q/A
```

## First-time setup

```bash
# 1. Start infrastructure (Mongo, Qdrant, Redis)
docker compose up -d
docker ps          # check 3 containers are running

# 2. Backend
cd api
python -m venv .venv
.\.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python seed.py                    # load 9 starter FAQs into Mongo
uvicorn app.main:app --reload --port 8000

# 3. Pipeline (separate terminal, optional for first run)
cd pipeline
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m pipeline.runner --once  # one-shot run

# 4. Frontend (separate terminal)
cd web
npm install
npm run dev
```

Frontend: <http://localhost:3000>
Backend Swagger UI: <http://localhost:8000/docs>
FAQ for radiology: <http://localhost:8000/faq/radiology>

### Quick smoke test (after Docker is up)

```bash
curl http://localhost:8000/health
curl http://localhost:8000/faq/radiology    # should return seeded FAQs
```

## Group Members

| # | Member | Focus Area |
|---|---|---|
| 1 | Abdul Ghani (F23607005) | Frontend and UI |
| 2 | Anas Bhatti (F23607044) | Conversation Processing |
| 3 | Muhammad Salman (F23607037) | Embedding and Clustering |
| 4 | [Member 4] | Backend, APIs, Data |
| 5 | [Member 5] | Selection, Issues, Eval |
