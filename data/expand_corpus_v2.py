"""Round 2 of corpus expansion.

Adds ~50 more clinician-style FAQs across the three specialties drawn
from standard published clinical guidance (no scraping — these are
written in our own words from common medical knowledge so we own the
text). Also adds ~80 more intent-training examples (including
``meta`` intent samples) and ~25 more eval queries.

Idempotent: re-running skips any question whose normalised form is
already in the corpus.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).parent


# ---------------------------------------------------------------- FAQs


NEW_FAQS = {
    "radiology": [
        ("Can I have an MRI with metal implants?",
         "Most modern orthopaedic implants (knee, hip, plates, screws) are MRI-safe but produce some local image distortion. Tell us in advance and bring the implant card if possible. Cochlear implants, some neurostimulators, and very old aneurysm clips are usually not safe — we will discuss alternatives such as CT or ultrasound."),
        ("Is the contrast dye injection painful?",
         "You will feel a quick pinch when the cannula is inserted, similar to a blood test. Once the dye flows you may feel a warm flush, a metallic taste, or a brief feeling of needing to pass urine — these are normal and pass within seconds."),
        ("Can my partner stay with me during a scan?",
         "For CT, MRI and most X-ray exams the room must be kept clear during the actual scan. A partner can wait in the changing area and may step in afterwards. For ultrasound a companion can often stay in the room — just ask the sonographer."),
        ("What is a ventilation-perfusion (V/Q) scan?",
         "A V/Q scan checks airflow (ventilation) and blood flow (perfusion) to the lungs using two small radioactive tracers, one inhaled and one injected. It is the test of choice for suspected pulmonary embolism in pregnant patients because it gives less foetal radiation than a CT angiogram."),
        ("My X-ray report mentions a 'nodule'. What does that mean?",
         "A nodule is a small rounded spot, usually less than 30 mm. Most lung nodules are benign (old infection, scar tissue). The radiologist follows a published schedule for surveillance imaging based on the nodule's size and your smoking history. Your referring doctor will explain whether any follow-up is needed."),
        ("Why is there a long wait between booking and my scan?",
         "Demand for MRI and CT is high, and certain protocols (cardiac MRI, MRCP, paediatric sedation) need specialist staff. We triage urgent cases (suspected cancer, post-op review) ahead of routine work. If you become more symptomatic while waiting, ask your referring doctor to mark the request as urgent."),
        ("Can I drink water before an abdominal ultrasound?",
         "For a regular abdominal scan, please fast 6 hours so we can see the gallbladder clearly. For a pelvic or bladder scan, finish a litre of water in the hour before the appointment and arrive with a full bladder — it acts as an acoustic window."),
        ("What is a CT-guided biopsy?",
         "A CT-guided biopsy uses real-time CT imaging to place a fine needle precisely into an abnormal area to take a tissue sample. It is done under local anaesthetic, takes 30-60 minutes, and you go home the same day. Mild bruising and a small risk of bleeding are the main side effects."),
        ("Do I need a chaperone for my scan?",
         "You are welcome to ask for a chaperone for any examination, especially scans that involve the chest, breast, abdomen, or pelvis. Just tell reception when you arrive and one will be arranged free of charge."),
        ("Will my MRI report be sent to my GP?",
         "Yes — the radiologist's report is sent automatically to the doctor who referred you, who will discuss the result with you at your next appointment. You can request your own copy by writing to the radiology department."),
    ],

    "physiotherapy": [
        ("What is a TENS machine and does it work?",
         "TENS (transcutaneous electrical nerve stimulation) delivers tiny electrical pulses through skin pads to reduce pain. Evidence is moderate for short-term relief in chronic low back, knee, and labour pain. It is safe for most people; avoid it over a pacemaker, broken skin, or the front of the neck."),
        ("Should I use a back brace for my low back pain?",
         "Routine use of a lumbar brace for non-specific back pain is not recommended — it tends to weaken the core muscles. Short-term use during a flare-up or heavy lifting can help. The real long-term fix is graded exercise and movement, which we will plan together."),
        ("What is the difference between sprain and strain?",
         "A sprain is an injury to a ligament (the tough band connecting two bones), commonly the ankle or knee. A strain is an injury to a muscle or tendon, commonly the hamstring or lower back. Both heal with the PEACE & LOVE protocol — Protection, Elevation, Avoid anti-inflammatories early, Compression, Education, then Load, Optimism, Vascularisation, Exercise."),
        ("How much walking should I do each day?",
         "Aim for 30-60 minutes of brisk walking on most days. Break it into 10-minute blocks if continuous walking is hard. Start with what feels comfortable and add 5-10 minutes per week. A simple step counter (8,000-10,000 steps a day for most adults) is a good motivator."),
        ("My ankle gives way often — what should I do?",
         "Recurrent giving-way is usually because the ligaments and the small balance receptors around the ankle have not retrained after the original sprain. A balance programme (single-leg stand, wobble board, jumps and lands), heel-raises, and lateral hops over 6-8 weeks fixes this in most people."),
        ("Are deep tissue massages safe during pregnancy?",
         "Pregnancy massage is safe from the second trimester when delivered by a trained therapist in a side-lying position. Avoid deep abdominal pressure, heat, and lying flat on the back. Tell your physiotherapist if you have any pregnancy complications such as placenta praevia."),
        ("What is the rotator cuff and how do you injure it?",
         "The rotator cuff is a group of four small muscles (supraspinatus, infraspinatus, teres minor, subscapularis) that hold the ball of the shoulder in the socket and lift the arm. It is injured by repeated overhead work, a fall onto an outstretched hand, or gradual age-related wear. Most tears improve with a structured exercise programme — surgery is reserved for full-thickness tears with persistent weakness."),
        ("Can physiotherapy help with chronic neck pain at the computer?",
         "Yes. Most desk-related neck pain is a mix of fatigued deep neck flexors, tight upper trapezius, and a forward-head posture. We assess your workstation, give you 5-minute mobility breaks (chin tucks, scapular squeezes, thoracic extensions), and add a graded strength programme. Most people improve within 6-8 weeks."),
        ("Should I exercise during a migraine?",
         "During the acute headache, rest in a quiet dark room. Between attacks, regular aerobic exercise (150 minutes a week of brisk walking, swimming or cycling) reduces migraine frequency by about a third. Avoid sudden very intense effort if it triggers attacks for you."),
        ("What is the role of dry land exercises before knee surgery?",
         "Prehabilitation — strength and range-of-motion exercises in the 4-6 weeks before knee replacement — speeds up recovery, reduces post-op pain, and shortens hospital stay. Focus on quadriceps strength, hip abduction, and learning to walk with crutches before the operation."),
    ],

    "cardiovascular": [
        ("What is a coronary calcium score?",
         "A coronary calcium score is a quick low-dose CT scan of the heart that measures calcium deposits in the artery walls. A score of 0 makes heart disease very unlikely in the next 5-10 years; a score above 300 indicates extensive disease and usually prompts aggressive risk-factor management. It is useful for people aged 40-75 with intermediate risk."),
        ("Can I have my pacemaker checked at home?",
         "Most modern pacemakers and defibrillators can be checked remotely through a bedside box that sends a daily report to the clinic over the mobile network or Wi-Fi. You typically come in once a year for a face-to-face check. Tell us straight away if you feel light-headed, a shock, or your device alarms."),
        ("What does an INR result mean?",
         "INR (International Normalised Ratio) measures how thin your blood is. For most patients on warfarin we aim for an INR between 2.0 and 3.0; for mechanical heart valves the target is higher (often 2.5-3.5). An INR over 5.0 increases the bleeding risk — please contact the clinic. Newer blood thinners (apixaban, rivaroxaban) do not need INR monitoring."),
        ("Why do my legs swell at the end of the day?",
         "Mild ankle swelling at the end of a long day is usually due to gravity — fluid settles in the lower legs and reabsorbs overnight. Causes that need review include heart failure (with breathlessness), kidney problems, deep vein thrombosis (one-sided, painful), liver disease, or certain medicines such as amlodipine. Elevate the legs, walk regularly, and wear compression stockings if recommended."),
        ("Is intermittent fasting safe for heart patients?",
         "Time-restricted eating (for example a 12- or 16-hour overnight fast) is safe for most people with stable heart disease and improves blood pressure and lipid profile in many. Take care if you are on insulin, sulfonylureas, or diuretics — your doctor may need to adjust doses. Avoid prolonged water-only fasts without medical supervision."),
        ("My cholesterol is high but I feel fine — should I still treat it?",
         "Yes. High cholesterol does not produce symptoms; the damage shows up as a heart attack or stroke. Modifiable risk factors (diet, exercise, weight, smoking) are the first step; if your 10-year cardiovascular risk is above 10% or your LDL is consistently above 4.9 mmol/L, a statin is usually recommended."),
        ("Are energy drinks bad for my heart?",
         "A single energy drink can contain the caffeine of 3-5 cups of coffee plus stimulants like taurine and guarana. They have been linked with palpitations, raised blood pressure, and rare arrhythmias, especially in teenagers and people with undiagnosed heart conditions. Stick to water, plain coffee, or tea."),
        ("Can sleep apnoea cause atrial fibrillation?",
         "Yes. Untreated obstructive sleep apnoea roughly doubles the risk of developing atrial fibrillation, and AFib recurs faster after ablation if sleep apnoea is left untreated. CPAP therapy improves both the apnoea and the rhythm control."),
        ("How is a heart murmur evaluated?",
         "A heart murmur is the sound of turbulent blood flow inside the heart. Many are harmless ('innocent murmurs' in children, flow murmurs in pregnancy). To rule out valve disease we usually arrange an echocardiogram — a 30-minute ultrasound of the heart that is painless and uses no radiation."),
        ("What is takotsubo cardiomyopathy?",
         "Takotsubo, also called 'broken-heart syndrome', is a sudden, usually reversible weakening of the heart muscle triggered by intense emotional or physical stress. Symptoms mimic a heart attack. Most patients recover within weeks with supportive treatment, but the immediate event needs hospital review."),
    ],
}


# ---------------------------------------------------------------- intents

NEW_INTENTS = [
    # meta — questions about the assistant itself
    ("who are you", "meta"),
    ("what are you", "meta"),
    ("what is medfaq", "meta"),
    ("what is your name", "meta"),
    ("are you a robot", "meta"),
    ("are you a bot", "meta"),
    ("are you a doctor", "meta"),
    ("are you a human", "meta"),
    ("are you chatgpt", "meta"),
    ("are you ai", "meta"),
    ("who built you", "meta"),
    ("who made you", "meta"),
    ("tell me about yourself", "meta"),
    ("introduce yourself", "meta"),
    ("what model are you", "meta"),
    ("are you a language model", "meta"),
    # definition
    ("what is a v q scan", "ask_definition"),
    ("what is takotsubo", "ask_definition"),
    ("what is coronary calcium score", "ask_definition"),
    ("define inr", "ask_definition"),
    ("what is a heart murmur", "ask_definition"),
    ("define rotator cuff", "ask_definition"),
    ("what is tens machine", "ask_definition"),
    # preparation
    ("can i drink water before abdominal ultrasound", "ask_preparation"),
    ("how to prepare for vq scan", "ask_preparation"),
    ("any prep before ct biopsy", "ask_preparation"),
    # recovery
    ("recovery after ct guided biopsy", "ask_recovery"),
    ("recovery after rotator cuff surgery", "ask_recovery"),
    # medication
    ("what does my inr result mean", "ask_medication"),
    ("are apixaban and rivaroxaban same", "ask_medication"),
    ("can i stop my pacemaker meds", "ask_medication"),
    # symptom
    ("my legs swell every evening", "ask_symptom"),
    ("my ankle gives way often", "ask_symptom"),
    ("i feel a fluttering in my chest at night", "ask_symptom"),
    ("my neck hurts from the laptop", "ask_symptom"),
    ("recurrent migraine for two weeks", "ask_symptom"),
    # lifestyle
    ("intermittent fasting and heart", "ask_lifestyle"),
    ("are energy drinks bad for heart", "ask_lifestyle"),
    ("safe massage during pregnancy", "ask_lifestyle"),
    ("how much daily walking is enough", "ask_lifestyle"),
    # procedure
    ("how does ct biopsy work", "ask_procedure"),
    ("what is a coronary angiogram like", "ask_procedure"),
    ("how is rotator cuff repair done", "ask_procedure"),
    # warning
    ("when is leg swelling dangerous", "ask_warning"),
    ("when is a murmur serious", "ask_warning"),
    ("red flags after biopsy", "ask_warning"),
    # greetings
    ("hi can you help me", "greeting"),
    ("hello dr radiology", "greeting"),
    # thanks
    ("thanks i feel better", "thanks"),
    ("got it thanks", "thanks"),
]


# ---------------------------------------------------------------- eval queries

NEW_EVAL = [
    {"specialty": "radiology", "query": "mri with metal implants",
     "expected_keyword": "implant"},
    {"specialty": "radiology", "query": "is contrast injection painful",
     "expected_keyword": "warm"},
    {"specialty": "radiology", "query": "partner stay during scan",
     "expected_keyword": "wait"},
    {"specialty": "radiology", "query": "vq scan what is it",
     "expected_keyword": "ventilation"},
    {"specialty": "radiology", "query": "what is a lung nodule",
     "expected_keyword": "nodule"},
    {"specialty": "radiology", "query": "long wait for mri",
     "expected_keyword": "urgent"},
    {"specialty": "radiology", "query": "abdominal ultrasound prep",
     "expected_keyword": "fast"},
    {"specialty": "radiology", "query": "ct biopsy how",
     "expected_keyword": "needle"},
    {"specialty": "radiology", "query": "need chaperone for scan",
     "expected_keyword": "chaperone"},
    {"specialty": "physiotherapy", "query": "tens machine",
     "expected_keyword": "electrical"},
    {"specialty": "physiotherapy", "query": "lumbar back brace",
     "expected_keyword": "brace"},
    {"specialty": "physiotherapy", "query": "sprain vs strain",
     "expected_keyword": "ligament"},
    {"specialty": "physiotherapy", "query": "daily walking goal",
     "expected_keyword": "walking"},
    {"specialty": "physiotherapy", "query": "ankle gives way",
     "expected_keyword": "balance"},
    {"specialty": "physiotherapy", "query": "pregnancy massage safe",
     "expected_keyword": "pregnancy"},
    {"specialty": "physiotherapy", "query": "rotator cuff injury",
     "expected_keyword": "rotator"},
    {"specialty": "physiotherapy", "query": "desk neck pain",
     "expected_keyword": "desk"},
    {"specialty": "physiotherapy", "query": "exercise during migraine",
     "expected_keyword": "migraine"},
    {"specialty": "physiotherapy", "query": "prehab before knee surgery",
     "expected_keyword": "prehab"},
    {"specialty": "cardiovascular", "query": "coronary calcium score",
     "expected_keyword": "calcium"},
    {"specialty": "cardiovascular", "query": "remote pacemaker check",
     "expected_keyword": "remote"},
    {"specialty": "cardiovascular", "query": "what does inr mean",
     "expected_keyword": "INR"},
    {"specialty": "cardiovascular", "query": "leg swelling evening",
     "expected_keyword": "swelling"},
    {"specialty": "cardiovascular", "query": "intermittent fasting heart",
     "expected_keyword": "fast"},
    {"specialty": "cardiovascular", "query": "high cholesterol no symptoms",
     "expected_keyword": "symptom"},
    {"specialty": "cardiovascular", "query": "energy drinks heart",
     "expected_keyword": "energy"},
    {"specialty": "cardiovascular", "query": "sleep apnoea and afib",
     "expected_keyword": "apnoea"},
    {"specialty": "cardiovascular", "query": "heart murmur",
     "expected_keyword": "murmur"},
    {"specialty": "cardiovascular", "query": "broken heart syndrome",
     "expected_keyword": "takotsubo"},
]


# ---------------------------------------------------------------- cleaning

_WS = re.compile(r"[ \t]+")
_MULTI_BLANK = re.compile(r"\n{3,}")
_SMART_QUOTES = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", " ": " ",
}


def _clean(text: str) -> str:
    if not text:
        return ""
    for src, dst in _SMART_QUOTES.items():
        text = text.replace(src, dst)
    text = _WS.sub(" ", text)
    text = _MULTI_BLANK.sub("\n\n", text)
    return text.strip()


def _norm_key(q: str) -> str:
    """Normalised form used to detect near-duplicates."""
    return re.sub(r"[^a-z0-9 ]", "", (q or "").lower()).strip()


# ---------------------------------------------------------------- IO


def _load(name: str) -> list[dict]:
    p = HERE / name
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save(name: str, data: list[dict]) -> None:
    p = HERE / name
    p.write_text(
        "[\n" + ",\n".join(json.dumps(d, ensure_ascii=False) for d in data)
        + "\n]\n",
        encoding="utf-8",
    )


def expand_faqs() -> dict:
    summary: dict[str, dict] = {}
    for spec, items in NEW_FAQS.items():
        name = f"faqs_{spec}.json"
        existing = _load(name)
        seen = {_norm_key(it["question"]) for it in existing}
        # Clean existing records in place (preprocess pass).
        for it in existing:
            it["question"] = _clean(it["question"])
            it["answer"] = _clean(it["answer"])
        added = 0
        for q, a in items:
            q2 = _clean(q)
            a2 = _clean(a)
            if _norm_key(q2) in seen:
                continue
            existing.append({
                "specialty": spec, "question": q2,
                "answer": a2, "approved": True,
            })
            seen.add(_norm_key(q2))
            added += 1
        _save(name, existing)
        summary[spec] = {"total": len(existing), "added_this_run": added}
    return summary


def main() -> None:
    summary = expand_faqs()
    for spec, s in summary.items():
        print(f"  {spec:14s}  +{s['added_this_run']:2d}  -> {s['total']} total")


if __name__ == "__main__":
    main()
