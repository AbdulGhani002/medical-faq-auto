# JSONL dataset bundle

Streaming-friendly NLP data for the Medical FAQ chatbot. Every file is
newline-delimited JSON (one JSON object per line). Regenerate the entire
bundle with:

```powershell
python data/build_jsonl.py
```

The manifest is `data/dataset_manifest.json`.

## Files

### 1. `faqs.jsonl`  (≈ 90 records)

Merged FAQ corpus across radiology / physiotherapy / cardiovascular.
This file is consumed by:

- `api/seed.py` when seeding Mongo.
- `api/app/db.py` for the in-memory fallback (no Docker required).
- `pipeline/` for evaluation / clustering passes.

```json
{"id":"radiology-0000","specialty":"radiology","question":"Do I need to fast before my MRI scan?","answer":"For most MRI scans, fasting is not required...","approved":true,"tags":["imaging","preparation"]}
```

### 2. `intents.jsonl`  (≈ 120 records)

Training data for the Naive Bayes intent classifier
(`api/app/nlp/nb_intent.py`). The classifier auto-loads this file at
import time; if it is missing, it falls back to a hard-coded list.

```json
{"id":"intent-0023","text":"do i need to fast before my mri","label":"ask_preparation"}
```

Labels:

```
greeting · thanks · frustration · help
ask_definition · ask_preparation · ask_recovery · ask_medication
ask_symptom · ask_lifestyle · ask_procedure · ask_warning
```

### 3. `eval_queries.jsonl`  (≈ 50 records)

Held-out evaluation queries used by `api/eval.py`.

```json
{"id":"eval-0001","specialty":"radiology","query":"is contrast dye safe","expected_keyword":"gadolinium"}
```

### 4. `chat_logs.jsonl`

Synthetic patient chat sessions. Each line is one whole session with a
list of turns; the pipeline ingests these as the raw input to the
FAQ-mining process.

```json
{"session_id":"log-rad-001","specialty":"radiology","turns":[{"role":"user","text":"do i need to fast before my mri scan tomorrow"},{"role":"bot","text":"..."}]}
```

### 5. `ner_examples.jsonl`

Annotated NER examples in BIO scheme. The annotations are produced by
running the project's dictionary NER (`api/app/nlp/ner.py`) over the raw
sentences, so the file is a sanity check on the labelled output and a
seed for any future statistical NER work.

```json
{"id":"ner-0001","text":"i have crushing chest pain","tokens":["i","have","crushing","chest","pain"],"tags":["O","O","O","B-SYMPTOM","I-SYMPTOM"],"entities":[{"text":"chest pain","label":"SYMPTOM","start":15,"end":25}]}
```

### 6. `sentiment_lexicon.jsonl`

Exported polarity weights from `api/app/nlp/sentiment.py`.

```json
{"word":"worried","polarity":-1.5,"kind":"negative"}
```

## Inspect at runtime

The API also exposes these as endpoints:

```
GET /nlp/datasets               # list all datasets + record counts
GET /nlp/datasets/{name}?n=3    # peek the first N rows of a JSONL file
```

Example:

```powershell
curl http://localhost:8000/nlp/datasets
curl "http://localhost:8000/nlp/datasets/faqs.jsonl?n=2"
```
