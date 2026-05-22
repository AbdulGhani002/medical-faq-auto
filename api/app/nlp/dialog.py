"""Dialog state manager.

Holds per-session state in memory (with a Mongo-backed mirror via
`services.dialog_store`). The state machine implements multi-turn
behaviour without any LLM:

  - track the active topic (last matched FAQ + last detected entity)
  - carry slots across turns
  - decide when to ask a clarifying question
  - decide when to ask a disambiguation question
  - build a stylistic opener (empathy / urgency)

This module is the "brain" that decides what the bot does next given the
NLP analysis of the user turn.
"""
from __future__ import annotations

from typing import Optional


def _empathic_opener(sentiment_label: str, urgency_level: int) -> str:
    if urgency_level >= 3:
        return ""  # The triage banner already handles this.
    if urgency_level == 2:
        return "Thanks for telling me. "
    if sentiment_label == "negative":
        return "Sorry you are dealing with this. "
    return ""


def _wh_opener(qtype: str) -> str:
    return ""  # We intentionally keep clinical answers verbatim.


def build_opener(state: dict, analysis: dict) -> str:
    """Return a short empathetic / contextual opener prefix."""
    return _empathic_opener(
        analysis["sentiment"]["label"],
        analysis["triage"]["level"],
    )


def needs_clarification(analysis: dict, top_score: float) -> Optional[str]:
    """If the best score is mediocre and a slot is missing, ask for it."""
    if top_score >= 0.18:
        return None
    slots = analysis["slots"]
    qtype = analysis["question_type"]
    if qtype in ("yes_no", "what", "why", "how"):
        if not slots.get("body_part") and not slots.get("condition") and not slots.get("procedure") and not slots.get("drug"):
            # Truly under-specified; ask for the topic word.
            return (
                "Could you tell me which body part, condition, or "
                "procedure you are asking about? That will help me find "
                "the right FAQ."
            )
    return None


def needs_disambiguation(alternatives: list[dict], top_score: float) -> Optional[list[dict]]:
    """If 2-3 alternatives are within 30% of the top score, offer them."""
    if not alternatives:
        return None
    near = [a for a in alternatives if a.get("score", 0.0) >= top_score * 0.7]
    if len(near) >= 1 and top_score < 0.35:
        return near[:3]
    return None


def update_state(state: dict, analysis: dict, matched_topic: str | None) -> dict:
    """Return a new state with carried-over and refreshed values."""
    return {
        "last_topic": matched_topic or state.get("last_topic"),
        "last_entities": [
            e["text"] for e in analysis["slots"]["entities"][:5]
        ] or state.get("last_entities", []),
        "last_intent": analysis["intent"]["label"],
        "last_qtype": analysis["question_type"],
        "turn_count": state.get("turn_count", 0) + 1,
        "slots": analysis["slots"],
    }
