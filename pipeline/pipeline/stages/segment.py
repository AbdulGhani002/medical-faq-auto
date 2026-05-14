"""Stage 2: split sessions into turns and identify user questions.

A turn dict from this stage looks like:
    {"session_id", "specialty", "user_text", "agent_text", "user_idx"}

`agent_text` is the bot reply that followed the user question (if any).
This is what gets selected as the canonical answer for the cluster later.
"""


_QUESTION_STARTERS = (
    "what", "why", "how", "when", "where",
    "can", "should", "do", "does", "is", "are",
    "kya", "kab", "kaise", "kaisa", "kahan",  # Urdu starters in Roman script
)


def _looks_like_question(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    if "?" in t:
        return True
    return any(t.startswith(w + " ") for w in _QUESTION_STARTERS)


def run(sessions: list[dict]) -> list[dict]:
    out: list[dict] = []
    for sess in sessions:
        turns = sess.get("turns", [])
        for i, turn in enumerate(turns):
            if turn.get("role") != "user":
                continue
            text = turn.get("text", "")
            if not _looks_like_question(text):
                continue

            # Find the bot reply that followed this user turn.
            agent_text = ""
            for j in range(i + 1, min(i + 4, len(turns))):
                if turns[j].get("role") == "bot":
                    agent_text = turns[j].get("text", "")
                    break

            out.append(
                {
                    "session_id": sess["session_id"],
                    "specialty": sess["specialty"],
                    "user_text": text,
                    "agent_text": agent_text,
                    "user_idx": i,
                }
            )
    return out
