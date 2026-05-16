"""Curated medical-vocabulary synonym dictionary used for query expansion.

Each canonical term maps to a list of equivalents. Expansion is symmetric:
the indexer also tries the canonical form when an alias appears in a doc.
This is a classical lexical resource, not a model.
"""

SYNONYMS: dict[str, list[str]] = {
    # Imaging
    "mri": ["magnetic resonance imaging", "mr scan"],
    "ct": ["computed tomography", "cat scan"],
    "xray": ["x ray", "radiograph", "plain film"],
    "ultrasound": ["sonography", "us scan", "echo"],
    "scan": ["imaging", "study"],
    "contrast": ["dye", "gadolinium", "iodine"],
    "report": ["result", "findings"],

    # Cardiology
    "bp": ["blood pressure"],
    "hbp": ["high blood pressure", "hypertension"],
    "hypertension": ["high blood pressure", "hbp"],
    "ldl": ["bad cholesterol"],
    "hdl": ["good cholesterol"],
    "mi": ["heart attack", "myocardial infarction"],
    "heart attack": ["mi", "cardiac arrest", "myocardial infarction"],
    "afib": ["atrial fibrillation", "a fib"],
    "ecg": ["ekg", "electrocardiogram"],
    "ekg": ["ecg", "electrocardiogram"],
    "echo": ["echocardiogram"],
    "stroke": ["cva", "brain attack"],
    "chf": ["heart failure", "congestive heart failure"],
    "angina": ["chest pain", "cardiac pain"],
    "palpitation": ["palpitations", "racing heart", "heart racing"],

    # Physiotherapy
    "physio": ["physiotherapy", "physical therapy", "pt"],
    "rehab": ["rehabilitation"],
    "sore": ["soreness", "ache", "tender"],
    "pain": ["ache", "hurts", "hurt"],
    "stretch": ["stretching", "stretches"],
    "exercise": ["workout", "exercises", "training"],

    # General
    "med": ["medicine", "medication", "drug", "pill", "tablet"],
    "meds": ["medicines", "medications", "drugs", "pills", "tablets"],
    "preg": ["pregnant", "pregnancy"],
    "pregnant": ["pregnancy", "preg"],
    "kid": ["child", "children", "kids"],
    "doc": ["doctor", "dr", "physician", "clinician"],
    "side effect": ["side effects", "adverse effect"],

    # Common medical concepts
    "diet": ["food", "eating", "nutrition"],
    "salt": ["sodium", "salty"],
    "smoke": ["smoking", "tobacco"],
    "drink": ["alcohol", "beer", "wine"],
    "sleep": ["sleeping", "rest"],
    "exercise": ["workout", "activity", "physical activity"],

    # Symptoms
    "dizzy": ["dizziness", "light headed", "lightheaded"],
    "tired": ["fatigue", "fatigued", "weak", "weakness"],
    "swell": ["swelling", "swollen", "oedema", "edema"],
    "breathless": ["short of breath", "shortness of breath", "sob"],
}


def expand_term(token: str) -> list[str]:
    """Return the original token plus any known synonyms."""
    out = [token]
    if token in SYNONYMS:
        out.extend(SYNONYMS[token])
    return out
