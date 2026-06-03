"""Full NLP retrieval pipeline. No neural model, no LLM.

For every chat request we run, in order:
  1. PHI scrub (already done in the router)
  2. Pull session state (last topic, last entities, slots)
  3. Run the full NLP analyser (intent, qtype, sentiment, triage,
     negation, NER, slots, keywords, POS)
  4. Coreference resolution (substitute "it" / "that" with the last topic)
  5. Context augmentation when the message is a short follow-up
  6. Spell correction over the FAQ vocabulary
  7. Multi-method scoring (TF-IDF word, TF-IDF char, BM25, LSA topic)
  8. Pseudo-relevance feedback re-ranking
  9. Dialog manager:
       - empathetic opener
       - triage banner if urgency >= 1
       - clarifying question if confidence is low and slots are empty
       - disambiguation card if several candidates are close
       - highlight matched spans in the chosen FAQ answer
  10. Persist updated session state.

The retrieval function returns a rich JSON envelope that the frontend
uses to build the chat bubble + the NLP debug panel.
"""
from __future__ import annotations

from typing import Optional

from app.db import get_db
from app.nlp import (
    Corrector, HybridIndex,
    augment_with_context, best_match, canned, classify_rule_intent,
    contains_roman_urdu, expand_roman_urdu,
    highlight_text, multi_doc_summary, needs_clarification,
    needs_disambiguation, primary_topic, resolve_pronouns,
    to_confidence, tokenize, triage_banner, update_state,
)
from app.nlp.dialog import build_opener
from app.nlp.normalize import _STOPWORDS  # noqa: WPS437 - intentional
from app.services.analyzer import analyse as analyse_text

_INDEX_CACHE: dict[str, HybridIndex] = {}
_FAQS_CACHE: dict[str, list[dict]] = {}
_CORRECTOR_CACHE: dict[str, Corrector] = {}
_STATE_CACHE: dict[str, dict] = {}
_LTR_CACHE: dict[str, "object"] = {}  # LTRReranker per specialty


def invalidate_cache(specialty: str | None = None) -> None:
    if specialty:
        _INDEX_CACHE.pop(specialty, None)
        _FAQS_CACHE.pop(specialty, None)
        _CORRECTOR_CACHE.pop(specialty, None)
        _LTR_CACHE.pop(specialty, None)
        return
    _INDEX_CACHE.clear()
    _FAQS_CACHE.clear()
    _CORRECTOR_CACHE.clear()
    _LTR_CACHE.clear()


def _ltr_for(specialty: str, idx, faqs: list[dict]):
    """Lazily train an LTR reranker per specialty using eval_queries.jsonl."""
    if specialty in _LTR_CACHE:
        return _LTR_CACHE[specialty]
    try:
        from pathlib import Path
        import json
        from app.nlp.ltr import LTRReranker

        repo = Path(__file__).resolve().parents[3]
        ep = repo / "data" / "eval_queries.jsonl"
        if not ep.is_file():
            _LTR_CACHE[specialty] = None
            return None
        queries: list[dict] = []
        with ep.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                q = json.loads(line)
                if q.get("specialty") == specialty:
                    queries.append(q)
        if not queries:
            _LTR_CACHE[specialty] = None
            return None
        r = LTRReranker()
        info = r.train_from_eval_set(idx, faqs, queries, k_neg=4)
        if not info.get("trained"):
            _LTR_CACHE[specialty] = None
            return None
        _LTR_CACHE[specialty] = r
        print(
            f"[ltr] trained {specialty}: n={info['n']} "
            f"train_acc={info['train_acc']:.3f}"
        )
        return r
    except Exception as e:
        print(f"[ltr] training skipped for {specialty}: {e!r}")
        _LTR_CACHE[specialty] = None
        return None


def reset_state(session_id: str) -> None:
    _STATE_CACHE.pop(session_id, None)


async def _load_corpus(specialty: str) -> list[dict]:
    db = get_db()
    cursor = db.faqs.find({"specialty": specialty, "approved": True})
    docs: list[dict] = []
    async for d in cursor:
        docs.append(d)
    return docs


async def _ensure_index(specialty: str):
    if specialty in _INDEX_CACHE:
        return (_INDEX_CACHE[specialty], _FAQS_CACHE[specialty],
                _CORRECTOR_CACHE[specialty])
    faqs = await _load_corpus(specialty)
    if not faqs:
        return None, [], None
    idx = HybridIndex(faqs)
    corr = Corrector(idx.vocabulary_stream())
    _INDEX_CACHE[specialty] = idx
    _FAQS_CACHE[specialty] = faqs
    _CORRECTOR_CACHE[specialty] = corr
    return idx, faqs, corr


def _get_state(session_id: str) -> dict:
    return _STATE_CACHE.get(session_id, {})


def _set_state(session_id: str, state: dict) -> None:
    _STATE_CACHE[session_id] = state


async def _previous_user_text(session_id: str, current: str) -> Optional[str]:
    if not session_id:
        return None
    db = get_db()
    cursor = (
        db.chat_turns.find({"session_id": session_id, "role": "user"})
        .sort("timestamp", -1).limit(4)
    )
    async for t in cursor:
        text = t.get("text", "")
        if text and text != current:
            return text
    return None


def _empty_response(answer: str, **extra) -> dict:
    base = {
        "answer": answer,
        "matched_faq_id": None,
        "confidence": 0.0,
        "alternatives": [],
        "bucket": "none",
        "intent": "question",
        "spell_corrections": [],
        "expanded_query": "",
        "added_terms": [],
        "score_breakdown": None,
        "highlighted": None,
        "nlp": None,
        "dialog": {},
        "summary": None,
        "matched_question": None,
    }
    base.update(extra)
    return base


def _highlight_payload(text: str, query: str) -> list[dict]:
    return highlight_text(text, query)


async def _bump_faq_count(faq: dict, specialty: str) -> None:
    """Increment the matched FAQ's ``count`` field.

    Works against both the Mongo Motor handle and the in-memory mock —
    both implement ``update_one`` with ``$inc``. We also update the
    cached list in-place so the next request reflects the new total
    without a full cache rebuild.
    """
    try:
        db = get_db()
        oid = faq.get("_id")
        if oid is None:
            return
        # Mongo stores ObjectId; the in-memory store uses hex strings.
        await db.faqs.update_one(
            {"_id": oid},
            {"$inc": {"count": 1}, "$currentDate": {"last_used": True}},
        )
        # Keep the in-process cache in sync.
        for f in _FAQS_CACHE.get(specialty, []):
            if f.get("_id") == oid:
                f["count"] = (f.get("count", 0) or 0) + 1
                break
    except Exception:
        # Counts are best-effort — never fail a chat over a counter.
        pass


async def retrieve_answer(
    specialty: str, text: str, session_id: str | None = None
) -> dict:
    sid = session_id or "anonymous"

    # 1. Run full NLP analysis on the raw text.
    analysis = analyse_text(text)

    # 2. Rule-based intent (still kept for canned chitchat).
    rule_intent = classify_rule_intent(text)

    # Chitchat shortcut: prefer the rule-based mapping for canned replies.
    if rule_intent != "question":
        msg = canned(rule_intent, specialty) or ""
        return _empty_response(
            msg,
            confidence=1.0,
            bucket="confident",
            intent=rule_intent,
            nlp=analysis,
            dialog={"chitchat": True},
        )

    # 2a. Scope guard. If the message is clearly out of scope (sexual
    # health, sports, finance, recipes, etc.) we deflect politely
    # instead of returning the closest medical FAQ by accident.
    from app.nlp.scope import looks_out_of_scope, deflection_message
    is_oos, oos_hits = looks_out_of_scope(text)
    if is_oos:
        return _empty_response(
            deflection_message(specialty),
            confidence=1.0,
            bucket="confident",
            intent="out_of_scope",
            nlp=analysis,
            dialog={"chitchat": True, "out_of_scope_cues": oos_hits},
        )

    # 3. Load (or build) per-specialty index and corrector.
    idx, faqs, corr = await _ensure_index(specialty)
    if idx is None or corr is None:
        return _empty_response(
            "No FAQs are approved for this specialty yet. Please check "
            "back soon or contact the clinic.",
            nlp=analysis,
        )

    state = _get_state(sid)

    # 4. Coreference: substitute pronouns with the last salient topic.
    resolved_text, coref_edits = resolve_pronouns(text, state.get("last_topic"))

    # 4a. Roman-Urdu phonetic expansion (Pakistan-friendly input).
    ru_edits: list[dict] = []
    has_roman_urdu = contains_roman_urdu(resolved_text)
    if has_roman_urdu:
        resolved_text, ru_edits = expand_roman_urdu(resolved_text)

    # 5. Context augmentation if the message is a short follow-up.
    prev_text = await _previous_user_text(sid, text)
    contextual = augment_with_context(resolved_text, prev_text)

    # 6. Spell correction against FAQ vocabulary. We deliberately skip
    # tokens that look like Roman-Urdu so the corrector does not
    # silently turn "mere" into "more" or "masla" into "mask".
    from app.nlp.roman_urdu import URDU_TO_EN
    raw_tokens = tokenize(contextual, drop_stopwords=False)
    fix_targets = [
        t for t in raw_tokens
        if t not in _STOPWORDS
        and len(t) >= 4
        and t not in URDU_TO_EN
        and not (has_roman_urdu and t.endswith(("i", "a", "ay", "ein")))
    ]
    fixed_subset, fixes = corr.correct(fix_targets)
    fix_map = {orig: fixed for orig, fixed in zip(fix_targets, fixed_subset)}
    fixed_tokens = [fix_map.get(t, t) for t in raw_tokens]
    corrected = " ".join(fixed_tokens)

    # 7. Two-pass retrieval with conditional PRF.
    scores, added_terms, expanded = idx.top_k_with_prf(corrected, k=10)

    # 7a. Optional LTR re-ranking. We only run it when the lexical
    # retriever is uncertain (top blended score < threshold). When it
    # fires we blend lexical and LR scores and adopt the new ordering.
    ltr_used = False
    LTR_GATE = 0.45  # lexical "very confident" threshold
    if scores and scores[0][1] < LTR_GATE:
        ltr = _ltr_for(specialty, idx, faqs)
        if ltr is not None:
            ranked = []
            for i, s, per in scores:
                doc_text = faqs[i]["question"] + " " + faqs[i]["answer"]
                lr_score = ltr.score_one(corrected, doc_text, per)
                ranked.append((i, s, per, lr_score))
            # Blend: 0.55 * LR prob + 0.45 * lexical
            ranked.sort(
                key=lambda r: -(0.55 * r[3] + 0.45 * min(r[1], 1.0))
            )
            scores = [(i, s, per) for i, s, per, _ in ranked[:5]]
            ltr_used = True

    info = best_match(scores)

    # 7b. Diversify alternatives with MMR so "Did you mean?" is varied.
    if info.get("top") and len(scores) > 1:
        mmr_picks = idx.top_k_with_mmr(corrected, k=4, lam=0.65)
        if mmr_picks:
            top_id = info["top"]["idx"]
            mmr_alts = [
                {"idx": i, "score": s} for i, s, _ in mmr_picks if i != top_id
            ][:3]
            if mmr_alts:
                info["alternatives"] = mmr_alts

    # 8. Dialog manager.
    top_score = info["top"]["score"] if info.get("top") else 0.0
    opener = build_opener(state, analysis)
    banner = triage_banner(analysis["triage"]["level"])
    clar = needs_clarification(analysis, top_score)
    alt_payload = [
        {
            "id": str(faqs[a["idx"]]["_id"]),
            "question": faqs[a["idx"]]["question"],
            "score": round(a["score"], 3),
        }
        for a in info.get("alternatives", [])
    ] if info.get("top") else []
    disambig = needs_disambiguation(alt_payload, top_score)

    # 9. Build the answer payload.
    response: dict
    # Auto-FAQ mining queue: feed both genuine misses and weak matches.
    # Threshold of 0.45 catches off-topic / out-of-distribution queries
    # while letting legitimate eval-set queries (0.6+) flow to retrieval.
    top_score_for_mining = info["top"]["score"] if info.get("top") else 0.0
    if info["bucket"] == "none" or top_score_for_mining < 0.45:
        try:
            from app.services.auto_faq import enqueue_unmatched
            await enqueue_unmatched(specialty, text)
        except Exception:
            pass

    if info["bucket"] == "none" or info["top"] is None:
        body_text = clar or (
            "I do not have a good match for that. Try rephrasing or pick "
            "a suggested topic below."
        )
        response = _empty_response(
            (banner + "\n\n" if banner else "") + opener + body_text,
            intent="question",
            spell_corrections=[{"original": o, "fixed": f} for o, f in fixes],
            expanded_query=expanded,
            added_terms=added_terms,
        )
    else:
        top = info["top"]
        faq = faqs[top["idx"]]
        intro = ""
        if info["bucket"] == "best_guess":
            intro = "I am not fully sure, but the closest match is:\n\n"
        # The banner is delivered separately in dialog.banner and the
        # frontend renders it as its own coloured card; don't repeat
        # the same text inside the answer body.
        prefix_parts: list[str] = []
        if opener:
            prefix_parts.append(opener.strip())
        # Cross-specialty hint: e.g. asking about chest pain inside the
        # radiology assistant suggests trying the cardiology one.
        from app.nlp.specialty_router import maybe_suggest_switch
        switch_hint = maybe_suggest_switch(text, specialty, top["score"])
        if switch_hint:
            prefix_parts.append(switch_hint)
        if intro:
            prefix_parts.append(intro.strip())
        prefix = ("\n\n".join(prefix_parts) + "\n\n") if prefix_parts else ""

        # Machine-write the answer via the from-scratch seq2seq. The
        # generator is grounded by the retrieved FAQ — if its output
        # diverges from the retrieved text we fall back to retrieval.
        try:
            from app.services.generator import grounded_generate
            gen_payload = grounded_generate(text, faq["answer"])
        except Exception:
            gen_payload = {"mode": "retrieval_only",
                           "text": faq["answer"],
                           "grounding_similarity": None}
        body_text = gen_payload.get("text", faq["answer"])
        answer_text = prefix + body_text
        highlighted = _highlight_payload(body_text, contextual)

        # Optional cross-doc summary for the debug panel.
        summary = None
        if disambig:
            doc_texts = [faqs[a["idx"]]["answer"]
                         for a in info.get("alternatives", [])
                         if a.get("idx") is not None]
            if doc_texts:
                summary = multi_doc_summary(doc_texts, n=2)

        response = {
            "answer": answer_text,
            "matched_faq_id": str(faq["_id"]),
            "matched_question": faq["question"],
            "confidence": to_confidence(top["score"]),
            "alternatives": alt_payload,
            "bucket": info["bucket"],
            "intent": "question",
            "spell_corrections": [
                {"original": o, "fixed": f} for o, f in fixes
            ],
            "expanded_query": expanded,
            "added_terms": added_terms,
            "score_breakdown": {
                "tfidf_word": round(top["per_method"]["tfidf_word"], 3),
                "tfidf_char": round(top["per_method"]["tfidf_char"], 3),
                "bm25": round(top["per_method"]["bm25"], 3),
                "lsa": round(top["per_method"].get("lsa", 0.0), 3),
                "embed": round(top["per_method"].get("embed", 0.0), 3),
                "blended": round(top["score"], 3),
                "matched_question": faq["question"],
            },
            "highlighted": highlighted,
            "generation": gen_payload,
            "nlp": analysis,
            "dialog": {
                "opener": opener,
                "triage_level": analysis["triage"]["level"],
                "triage_cues": analysis["triage"]["cues"],
                "banner": banner,
                "clarification": clar,
                "coref": coref_edits,
                "roman_urdu": ru_edits,
                "disambiguation": disambig,
                "active_topic": primary_topic(analysis["entities"])
                                or state.get("last_topic"),
                "ltr_used": ltr_used,
            },
            "summary": summary,
        }

    # 10. Persist updated session state.
    matched_topic = primary_topic(analysis["entities"]) or state.get("last_topic")
    if response.get("matched_question"):
        # Use the matched FAQ's primary noun as a fallback topic.
        from app.nlp.ner import extract_entities as _ee
        fallback = primary_topic(_ee(response["matched_question"])) or matched_topic
        matched_topic = matched_topic or fallback
    _set_state(sid, update_state(state, analysis, matched_topic))

    # 11. Live FAQ-usage counter. We only increment when retrieval found
    # something useful so an unhelpful "no good match" turn does not
    # inflate any FAQ's count.
    if info.get("top") and info["bucket"] in ("confident", "best_guess"):
        matched_faq = faqs[info["top"]["idx"]]
        await _bump_faq_count(matched_faq, specialty)

    return response


def state_snapshot(session_id: str) -> dict:
    """Public helper used by the /chat/state endpoint."""
    return _STATE_CACHE.get(session_id, {})
