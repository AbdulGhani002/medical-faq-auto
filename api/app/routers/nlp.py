"""NLP introspection endpoints. Useful for the report + the debug panel."""
from fastapi import APIRouter, HTTPException

from app.models import NLPAnalysis, NLPAnalyzeRequest
from app.nlp.nb_intent import training_source
from app.services.analyzer import analyse as analyse_text
from app.services.datasets import list_datasets, peek

router = APIRouter()


@router.post("/analyze", response_model=NLPAnalysis)
async def analyze(req: NLPAnalyzeRequest):
    return NLPAnalysis(**analyse_text(req.text))


@router.get("/health")
async def health():
    return {"ok": True, "nb_intent_source": training_source()}


@router.get("/datasets")
async def datasets():
    return {"datasets": list_datasets()}


@router.get("/datasets/{name}")
async def dataset_peek(name: str, n: int = 5):
    # Allow only the JSONL filenames that exist in the manifest.
    known = {d["name"] for d in list_datasets() if d["present"]}
    if name not in known:
        raise HTTPException(404, f"Unknown dataset: {name}")
    return {"name": name, "rows": peek(name, n=max(1, min(n, 50)))}


# ---------------- new technique endpoints ----------------


@router.post("/perplexity")
async def lm_perplexity(req: NLPAnalyzeRequest):
    """Tri-/bi-/uni-gram LM perplexity with Kneser-Ney smoothing."""
    from app.nlp.lm import get_model, perplexity
    return {
        "text": req.text,
        "perplexity": round(perplexity(req.text), 4),
        "model": {
            "order": get_model().order,
            "vocab_size": len(get_model().vocab),
            "trained_on_sentences": get_model().train_size,
        },
    }


@router.post("/autocomplete")
async def lm_autocomplete(req: NLPAnalyzeRequest, k: int = 5):
    """Top-k next-word suggestions from the n-gram LM."""
    from app.nlp.lm import autocomplete
    return {"prefix": req.text, "suggestions": [
        {"word": w, "prob": round(p, 6)}
        for w, p in autocomplete(req.text, k=k)
    ]}


@router.post("/chunks")
async def chunks(req: NLPAnalyzeRequest):
    """Noun-phrase + verb-phrase chunks via HMM POS + pattern parser."""
    from app.nlp.chunker import chunk as do_chunk
    from app.nlp.hmm_pos import hmm_tag
    from app.nlp.normalize import tokenize
    toks = tokenize(req.text, drop_stopwords=False)
    tagged = hmm_tag(toks)
    out = do_chunk(tagged)
    return {
        "text": req.text,
        "tagged": [{"text": w, "tag": t} for w, t in tagged],
        **out,
    }


@router.post("/triples")
async def triples(req: NLPAnalyzeRequest):
    """SVO triples extracted from the text."""
    from app.nlp.kg import extract_triples
    return {"text": req.text, "triples": extract_triples(req.text)}


@router.post("/ner_stat")
async def ner_statistical(req: NLPAnalyzeRequest):
    """Statistical NER (averaged structured perceptron + Viterbi)."""
    from app.nlp.ner_stat import get_model
    m = get_model()
    return {
        "text": req.text,
        "entities": m.predict_entities(req.text),
    }


@router.post("/wmd")
async def wmd_pair(req_a: NLPAnalyzeRequest, req_b_text: str = ""):
    """Word Mover's Distance similarity between two short texts.

    Uses the corpus PPMI embeddings. Returns both raw RWMD and an
    exp(-d) similarity in [0, 1].
    """
    from app.nlp.embeddings import CorpusEmbeddings
    from app.nlp.wmd import relaxed_wmd, similarity
    from app.services.retrieval import _ensure_index

    # Build an embeddings model on-the-fly over the first specialty's
    # corpus (cheap; 90 docs).
    idx, _, _ = await _ensure_index("radiology")
    if idx is None or idx._emb is None:
        return {"error": "embeddings not available"}
    emb = idx._emb
    from app.nlp.normalize import tokenize
    a = tokenize(req_a.text, drop_stopwords=True)
    b = tokenize(req_b_text, drop_stopwords=True)
    return {
        "a": req_a.text,
        "b": req_b_text,
        "rwmd": round(relaxed_wmd(a, b, emb), 4),
        "similarity": round(similarity(a, b, emb), 4),
    }


@router.get("/triples_dump")
async def triples_dump(limit: int = 20, specialty: str | None = None):
    """Read pre-computed KG triples from data/kg_triples.jsonl."""
    from app.services.datasets import iter_jsonl
    out: list[dict] = []
    for rec in iter_jsonl("kg_triples.jsonl"):
        if specialty and rec.get("specialty") != specialty:
            continue
        out.append(rec)
        if len(out) >= limit:
            break
    return {"specialty": specialty, "n": len(out), "triples": out}


# ---------------- from-scratch neural endpoints ----------------


@router.post("/mlp_intent")
async def mlp_intent(req: NLPAnalyzeRequest):
    """Intent classification via the in-house MLP (myml + backprop)."""
    from app.nlp.mlp_intent import classify, stats
    return {"prediction": classify(req.text), "model": stats()}


@router.post("/attention")
async def attention_embed(req: NLPAnalyzeRequest):
    """Encode text through the in-house transformer encoder.

    Returns the mean-pooled vector (head only) + the attention weights
    of the last layer averaged across heads. Pure numpy.
    """
    from app.myml.attention import TransformerEncoder, encode_text
    from app.nlp.normalize import tokenize
    toks = tokenize(req.text, drop_stopwords=False)
    enc = TransformerEncoder(d_model=32, n_heads=4, d_ff=64, seed=42)
    # Lazy global vocab so we don't rebuild on every request.
    global _ATTN_VOCAB
    if "_ATTN_VOCAB" not in globals() or _ATTN_VOCAB is None:
        from app.services.datasets import iter_jsonl
        _vocab: dict[str, int] = {}
        for rec in iter_jsonl("faqs.jsonl"):
            for t in tokenize(rec.get("question", ""), drop_stopwords=False):
                if t not in _vocab:
                    _vocab[t] = len(_vocab) + 2  # 0=PAD, 1=UNK
            for t in tokenize(rec.get("answer", ""), drop_stopwords=False):
                if t not in _vocab:
                    _vocab[t] = len(_vocab) + 2
        _ATTN_VOCAB = _vocab
    vec, weights = encode_text(toks, _ATTN_VOCAB, enc, max_len=32)
    return {
        "tokens": toks[:32],
        "vector_preview": [round(float(v), 4) for v in vec[:8]],
        "vector_norm": round(float((vec ** 2).sum() ** 0.5), 4),
        "attn_weights_shape": (
            list(weights.shape) if weights is not None else None
        ),
        "model": {
            "d_model": enc.d_model,
            "n_heads": enc.mha.n_heads,
            "vocab_size": len(_ATTN_VOCAB),
        },
    }


_ATTN_VOCAB: dict | None = None


@router.post("/crf_ner")
async def crf_ner(req: NLPAnalyzeRequest):
    """NER via the in-house linear-chain CRF (forward-backward + Viterbi)."""
    from app.services.crf_ner import predict_entities, stats
    return {
        "text": req.text,
        "entities": predict_entities(req.text),
        "model": stats(),
    }


# ---------------- word2vec / BPE / dual encoder ----------------


@router.post("/word2vec_neighbours")
async def word2vec_neighbours(req: NLPAnalyzeRequest, k: int = 6):
    """Top-k nearest-neighbour words for each token in the input,
    using our from-scratch word2vec skip-gram model."""
    from app.services.neural_models import get_word2vec, word2vec_stats
    from app.nlp.normalize import tokenize
    w2v = get_word2vec()
    toks = tokenize(req.text, drop_stopwords=True)
    out = []
    for t in toks:
        nbrs = w2v.most_similar(t, k=k)
        out.append({
            "word": t,
            "neighbours": [{"word": w, "sim": round(float(s), 4)}
                           for w, s in nbrs],
        })
    return {"text": req.text, "tokens": out, "model": word2vec_stats()}


@router.post("/bpe")
async def bpe_encode(req: NLPAnalyzeRequest):
    """Subword tokenisation via the from-scratch BPE tokenizer."""
    from app.services.neural_models import bpe_stats, get_bpe
    bpe = get_bpe()
    return {
        "text": req.text,
        "subwords": bpe.encode(req.text),
        "model": bpe_stats(),
    }


@router.post("/dual_encoder")
async def dual_encoder(req: NLPAnalyzeRequest, k: int = 5):
    """Neural retrieval via the from-scratch dual-encoder bi-encoder.
    Trained with in-batch InfoNCE contrastive loss."""
    from app.services.neural_models import dual_encoder_stats, neural_retrieve
    return {
        "query": req.text,
        "results": neural_retrieve(req.text, k=k),
        "model": dual_encoder_stats(),
    }


@router.post("/torch_intent")
async def torch_intent(req: NLPAnalyzeRequest):
    """Intent classification via the PyTorch transformer trained from
    scratch (every layer defined by us — no pretrained weights). The
    checkpoint is produced by ``python api/train_transformer.py``.
    """
    from app.services.torch_intent import classify, stats
    pred = classify(req.text)
    return {"prediction": pred, "model": stats()}
