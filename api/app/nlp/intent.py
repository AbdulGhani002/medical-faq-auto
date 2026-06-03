"""Rule-based intent classifier.

Recognises chitchat / meta intents we never want routed through the
retrieval pipeline: ``greeting``, ``thanks``, ``frustration``,
``help``, ``meta`` (questions about the assistant itself), and falls
through to ``question`` for actual medical queries.
"""
import re

_GREETINGS = {
    "hi", "hello", "hey", "hiya", "yo", "salaam", "salam", "assalam",
    "good morning", "good afternoon", "good evening", "good night",
    "hi there", "hey there", "howdy", "greetings",
}

_THANKS = {
    "thanks", "thank you", "thx", "thankyou", "ty", "appreciate it",
    "appreciated", "much appreciated", "shukria", "shukriya", "cheers",
    "jazak allah", "many thanks",
}

_FRUSTRATION = {
    "wtf", "wth", "ugh", "ffs", "useless", "stupid", "garbage",
    "this sucks", "this is bad", "rubbish", "useless bot",
    "you suck", "lame", "boring",
}

_HELP = {
    "help", "what can you do", "what do you do", "menu", "options",
    "topics", "categories",
}

# Questions about the assistant itself, not about medicine. The
# retriever has no FAQ for "who are you" so without this guard it
# matches the closest clinical question by similarity, which is
# almost always wrong.
_META_PHRASES = (
    "who are you", "what are you", "what is medfaq", "what's medfaq",
    "whats medfaq", "what is your name", "what's your name",
    "whats your name", "your name", "who made you", "who built you",
    "who created you", "who developed you", "who designed you",
    "tell me about yourself", "introduce yourself", "are you a robot",
    "are you a bot", "are you ai", "are you a human", "are you human",
    "are you a doctor", "are you a real doctor", "are you real",
    "what model are you", "are you chatgpt", "are you gpt",
    "are you claude", "are you a language model",
)


def _normalise(text: str) -> str:
    t = (text or "").lower().strip().rstrip("?!.,")
    return re.sub(r"\s+", " ", t)


# Medical keywords that, if they appear ANYWHERE in the message, mean
# the user is asking a real medical question and the greeting / thanks /
# help shortcuts must not fire. Otherwise "hi i am feeling pain in my
# heart" matches greeting and the user never gets a real reply.
_MEDICAL_HINTS = {
    "pain", "ache", "hurt", "hurts", "hurting", "sore", "sick", "ill",
    "fever", "cough", "blood", "swelling", "swollen", "dizzy",
    "vomit", "vomiting", "nausea", "breath", "breathless", "breathing",
    "rash", "wound", "burn", "bleed", "bleeding", "numb",
    "heart", "chest", "head", "back", "knee", "leg", "arm", "stomach",
    "neck", "shoulder", "hip", "ankle", "wrist", "throat", "eye",
    "ear", "tooth", "ribs", "lung", "kidney", "liver", "skin",
    "mri", "ct", "scan", "x-ray", "xray", "ultrasound", "ecg", "ekg",
    "echo", "biopsy", "stent", "angiogram", "physio", "rehab",
    "bp", "cholesterol", "diabetes", "hypertension", "stroke",
    "afib", "angina", "asthma",
    "medicine", "medication", "drug", "tablet", "pill", "dose",
    "appointment", "report",
    # Roman-Urdu
    "dard", "dil", "sar", "kamar", "pet", "khansi", "bukhar",
    "ghutna", "ghutne", "seenay", "saans", "kharish",
}


def _has_medical_hint(text: str) -> bool:
    toks = set(re.findall(r"[a-z]+", text.lower()))
    return bool(toks & _MEDICAL_HINTS)


def classify(text: str) -> str:
    t = _normalise(text)
    if not t:
        return "question"

    # Meta questions about the bot itself never get suppressed.
    if any(phrase in t for phrase in _META_PHRASES):
        return "meta"

    # If the message contains any medical hint, route to retrieval no
    # matter how it starts. "hi i am feeling pain in my heart" must
    # never be filed as a greeting.
    if _has_medical_hint(t):
        return "question"

    # Greeting / thanks / help only fire on short messages that are
    # truly nothing more than that greeting plus optional politeness.
    tokens = re.findall(r"[a-z]+", t)
    short = len(tokens) <= 5

    if short and any(t == g or t.startswith(g + " ") for g in _GREETINGS):
        return "greeting"
    if short and any(t == g or t.startswith(g + " ") for g in _THANKS):
        return "thanks"
    if any(t == g or g in t for g in _FRUSTRATION):
        return "frustration"
    if short and any(t == g or t.startswith(g) for g in _HELP):
        return "help"
    return "question"


CANNED_REPLIES = {
    "greeting": (
        "Hi. I am the MedFAQ {specialty} assistant. Ask me anything about "
        "preparation, recovery, medications, or general care. I will look "
        "up a clinician-reviewed answer for you."
    ),
    "thanks": (
        "You are welcome. If you have another question on {specialty}, "
        "just ask."
    ),
    "frustration": (
        "Sorry that did not help. I only return real, clinician-reviewed "
        "answers and never invent text. Try rephrasing the question, or "
        "pick one of the suggested topics below. For anything urgent, "
        "please contact the clinic directly."
    ),
    "help": (
        "I can answer common {specialty} questions — for example: "
        "preparation before procedures, what to expect, medication timing, "
        "warning signs, and recovery. Try a phrase like 'how long does it "
        "take' or 'what should I avoid'."
    ),
    "meta": (
        "I'm MedFAQ — a {specialty} assistant built as a university "
        "semester project. I do not use any large language model. Every "
        "reply you see comes from an approved, clinician-reviewed FAQ "
        "selected by an in-house classical-NLP retriever (TF-IDF + BM25 + "
        "LSA + PPMI + Naive Bayes intent + medical NER, all written from "
        "scratch in numpy). I am not a doctor and cannot give individual "
        "medical advice — please contact a clinician for anything "
        "specific to your case."
    ),
}


def canned(intent: str, specialty: str) -> str | None:
    tpl = CANNED_REPLIES.get(intent)
    if tpl is None:
        return None
    return tpl.format(specialty=specialty)
