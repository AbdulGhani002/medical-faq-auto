"""Append new hand-written FAQs and JSONL training data.

Run once to grow the corpus. Idempotent: duplicates by `question` are
skipped, so re-running is safe.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent


# ---------------- new FAQs ----------------

NEW_FAQS = {
    "radiology": [
        ("How is an ultrasound performed?",
         "A gel is applied to the area being scanned and a small handheld probe is moved over the skin. The probe sends and receives high-frequency sound waves and the computer builds a live image. It is painless, uses no radiation, and takes 15-30 minutes. You may be asked to drink water beforehand for a pelvic scan, or fast for an abdominal scan."),
        ("What is a PET-CT scan?",
         "A PET-CT combines a CT scan (anatomy) with a PET scan (function). A small radioactive sugar tracer is injected and areas using a lot of sugar — often tumours or infection — light up. The scan takes 30-60 minutes including a 60-minute uptake wait. Tell us if you have diabetes; we may adjust the protocol."),
        ("What is interventional radiology?",
         "Interventional radiology uses imaging (ultrasound, fluoroscopy, CT) to guide minimally invasive procedures such as biopsies, drainages, angioplasty, and stent placement. Most procedures are done under local anaesthetic through a small skin nick, so recovery is faster than open surgery."),
        ("Why must I remove all metal before an MRI?",
         "The MRI uses a very strong magnet. Loose metal can be pulled into the bore and cause injury, and metal on the body distorts the images. Remove jewellery, watches, hairpins, coins, and metal-rimmed glasses. Tell us in advance about implants, pacemakers, cochlear devices, or recent surgery with clips."),
        ("How much radiation does a CT scan use?",
         "A typical chest CT delivers about 7 mSv, similar to 2-3 years of natural background radiation. A head CT is around 2 mSv. The benefit of a needed scan greatly outweighs the small risk, but we still use the lowest dose that gives a diagnostic image."),
        ("Can I drive after a contrast scan?",
         "Yes, you can drive immediately after most contrast scans. If you were given a sedative for claustrophobia, do not drive for 24 hours. If you feel light-headed or unwell after contrast, wait until you feel normal and tell our staff."),
        ("What is a bone-density scan (DEXA)?",
         "DEXA uses a very low dose of X-rays to measure how dense your bones are at the hip and spine. The scan takes about 10 minutes, is painless, and you stay fully clothed (no metal). We use the result to assess osteoporosis risk and the need for treatment."),
        ("What is a fluoroscopy?",
         "Fluoroscopy is a real-time moving X-ray, used to watch swallowing, bowel motion, or to guide a needle into a joint. The exam takes 10-30 minutes. You may be asked to drink contrast (barium) or have it injected, depending on the test."),
        ("My report says 'incidental finding' — should I be worried?",
         "Incidental findings are things picked up by chance that were not the reason for the scan. Most are benign (cysts, small nodules, age-related changes) and only need observation. Your referring doctor will explain whether the finding needs any follow-up imaging or testing."),
        ("Will the radiology team discuss my results with me?",
         "Radiologists send a written report to your referring doctor, who will discuss results with you in context. For interventional procedures the radiologist will speak with you directly before and after. If you have questions about the report itself, your referring doctor can request a clarification."),
        ("Why do I have to hold my breath during a scan?",
         "Holding your breath stops the chest and upper abdomen from moving, which makes the image sharper. We will guide you with a recording or hand signals — usually 10-20 seconds for CT and slightly longer for MRI. Practice slow deep breaths before the scan to make it easier."),
        ("What is the gadolinium contrast and when do you use it?",
         "Gadolinium is a contrast agent used in MRI to highlight blood vessels, inflammation, and tumours. It is given through a small IV cannula. It is safe for most patients but is avoided in advanced kidney disease and used cautiously in pregnancy."),
        ("Can I breastfeed after I receive contrast?",
         "Yes. Both iodine (CT) and gadolinium (MRI) contrasts are excreted in only tiny amounts in breast milk and current guidelines say you can continue breastfeeding normally. If you prefer, you can express milk before the scan and use it for the next feed."),
        ("My child is having an MRI — what should I expect?",
         "Young children may need a feed-and-sleep protocol or light sedation to lie still. Bring favourite blankets, dummies, and a change of clothes. We will explain everything to you and your child, and one parent can usually stay in the scan room."),
        ("Can I keep my insulin pump on during the scan?",
         "Insulin pumps must be removed and kept outside the MRI room as they contain metal and electronics. For a CT it is usually fine to keep the pump on, but tell the technologist so they can avoid the device in the field of view."),
    ],

    "physiotherapy": [
        ("What is dry needling?",
         "Dry needling uses thin acupuncture-style needles to release trigger points in tight muscles. It is different from acupuncture (it follows musculoskeletal anatomy, not meridians) and can produce a brief twitch and soreness lasting 24-48 hours. Many patients find it useful for chronic neck, shoulder, and back pain."),
        ("Should I use heat or ice on my injury?",
         "Use ice for the first 48 hours after a fresh injury — 15 minutes at a time, wrapped in a cloth — to reduce swelling. Use heat for stiff or chronic pain to relax muscles before exercises. If swelling is severe or pain is sharp and increasing, do not heat; book a review instead."),
        ("Is bed rest okay for back pain?",
         "More than 1-2 days of bed rest usually makes back pain worse. Stay as active as you can: walk, change positions often, and gently move the spine. Pain medication for the first 2-3 days plus a graded exercise plan gives the best results for most acute back pain."),
        ("How long should a stretch be held?",
         "For flexibility, hold each static stretch for 20-30 seconds and repeat 2-3 times per side. Do not bounce. You should feel a gentle pull, not pain. Warm up with light activity first; stretching cold muscles can cause strains."),
        ("How do I prevent back pain at my desk?",
         "Set the chair so feet are flat and hips are slightly higher than knees. Top of the monitor at eye level. Keep the keyboard close so elbows are at 90 degrees. Stand up and walk for 1-2 minutes every 30-40 minutes. A small lumbar roll can help maintain the natural curve of the lower back."),
        ("Why does my knee click during exercises?",
         "Painless clicking is common and is usually fluid or tendons moving over bony surfaces. Clicking with pain, locking, or giving way needs review. Keep doing your exercises as long as they are pain-free and tell your physiotherapist at the next session."),
        ("What is the best sleep position for lower back pain?",
         "Sleep on your back with a pillow under the knees, or on your side with a pillow between the knees. Avoid sleeping on your stomach as it strains the lower back and neck. A medium-firm mattress is generally best."),
        ("What is plantar fasciitis and what shoes help?",
         "Plantar fasciitis is inflammation of the band of tissue under the foot, often felt as sharp heel pain in the morning. Shoes with cushioned heels, arch support, and a small heel-to-toe drop help most. Avoid walking barefoot on hard floors and add calf and plantar fascia stretches."),
        ("What is a frozen shoulder?",
         "Frozen shoulder is gradual stiffness and pain that limits both active and passive movement. It typically passes through three phases (pain, stiff, recovery) over 12-30 months. Physiotherapy, a steroid injection, or hydrodilatation are the main treatments — surgery is rarely needed."),
        ("How long does a physio session usually last?",
         "A first appointment usually takes 45-60 minutes (history, assessment, initial treatment, and home plan). Follow-up sessions are 30-45 minutes. Tell us if you need a longer slot for complex pain or post-surgical work."),
        ("Should I do exercises through pain?",
         "Some discomfort up to about 4 out of 10 is acceptable and may be necessary to make progress. Pain above that level or sharp pain means stop and contact us. The pain should settle within 24 hours of exercise; if it lingers, the load was too high."),
        ("What is sciatica?",
         "Sciatica is pain, tingling, or weakness that travels down one leg from the lower back, caused by irritation of the sciatic nerve. Most cases improve in 4-6 weeks with a graded exercise plan, posture coaching, and pain management. Red flags (loss of bladder/bowel control, numbness in the saddle area) need urgent review."),
        ("Can physio help vertigo?",
         "Yes — vestibular physiotherapy uses head-position manoeuvres (such as Epley for BPPV) and gaze-stabilisation exercises. Most patients with positional vertigo improve in 1-3 sessions. Vertigo with hearing loss, neurological signs, or severe imbalance needs medical review first."),
    ],

    "cardiovascular": [
        ("What is a Holter monitor?",
         "A Holter is a small portable ECG that records every heartbeat for 24-48 hours while you go about normal activity. It is used to find intermittent arrhythmias, link symptoms (palpitations, fainting) to rhythm changes, and assess pacemaker function. Keep a diary of symptoms while wearing it."),
        ("What is a stress test?",
         "A stress test records your ECG while you walk on a treadmill or pedal a bike, with the workload increasing every 3 minutes. It looks for reduced blood flow to the heart and checks your exercise tolerance. The test takes 30-45 minutes. Wear comfortable shoes and avoid heavy meals and caffeine for 4 hours before."),
        ("What is an angiogram?",
         "A coronary angiogram is an X-ray of the arteries supplying the heart. A thin tube is passed through a small puncture in the wrist or groin and contrast dye is injected. The cardiologist watches the dye flow live and can also place a stent if a blockage is found. The procedure takes 30-60 minutes."),
        ("What is a stent?",
         "A stent is a small mesh tube placed inside a narrowed artery to keep it open. Modern stents are coated with medication to reduce re-narrowing. After a stent you take dual antiplatelet medication (aspirin + clopidogrel/ticagrelor) for at least 6-12 months — do not stop without our advice."),
        ("Can I fly after a heart attack or stent?",
         "Most people can fly 1-2 weeks after an uncomplicated heart attack or stent. We may advise longer if there were complications. Take your medications in hand luggage, walk in the aisle every hour to reduce clot risk, and drink water (avoid alcohol). A travel insurance review is worth it."),
        ("What is rheumatic heart disease?",
         "Rheumatic heart disease is heart-valve damage caused by an immune reaction to streptococcal throat infections in childhood. It is still common in Pakistan and can cause shortness of breath, palpitations, and ankle swelling. Long-term penicillin prophylaxis and timely valve treatment prevent progression."),
        ("What blood tests do I need for heart disease?",
         "We typically check a lipid profile (LDL, HDL, triglycerides), HbA1c (diabetes), kidney function, thyroid, and a complete blood count. Tests are best done fasting if the lipid profile is included. We may add specialised tests such as BNP for heart failure or troponin during chest pain."),
        ("What is heart-rate variability and does it matter?",
         "Heart-rate variability is the small beat-to-beat change in your pulse, measured by ECG. Higher variability usually means better cardiac autonomic health. It is interesting as a wellness metric but is not used to diagnose disease. Stay active, sleep well, and manage stress to improve it."),
        ("How do I read a blood-pressure machine at home?",
         "Sit quietly for 5 minutes with your back supported, feet flat on the floor, arm at heart height. Take two readings 1 minute apart, morning and evening for one week. Bring the diary to your appointment. A reading of 135/85 or higher on a home average is considered high."),
        ("Is salt the only thing I need to watch?",
         "Salt is important but not the only thing. Aim for under 5 g/day (1 teaspoon). Also reduce sugary drinks, deep-fried food, and processed meat. Increase vegetables, fruit, whole grains, beans, and oily fish. Add 150 minutes of moderate exercise a week."),
        ("How dangerous is high cholesterol?",
         "High LDL cholesterol drives the build-up of fatty plaques in arteries, which is the main cause of heart attack and stroke. Most people with high cholesterol have no symptoms, so blood tests are important. Diet, exercise, and — if needed — statins lower LDL safely."),
        ("Can young people have a heart attack?",
         "Yes, although it is uncommon. The usual causes in people under 40 are heavy smoking, cocaine or amphetamine use, severe lipid disorders, or a strong family history. Chest pain with sweating or breathlessness needs emergency review regardless of age."),
        ("What is heart failure 'with preserved ejection fraction'?",
         "HFpEF is heart failure where the heart pumps normally but cannot relax and fill properly. Symptoms are the same as other heart failure (breathlessness, swelling) but treatment is different — we focus on blood pressure, salt, fluid, exercise, and SGLT2 inhibitors."),
        ("My ECG report says 'left bundle branch block' — what does that mean?",
         "Left bundle branch block means the electrical signal takes a slower path to one half of the heart. It can be benign or a marker of underlying heart disease. Your cardiologist will usually request an echocardiogram and a careful review of your medications."),
        ("How does smoking cessation help my heart?",
         "Within 20 minutes blood pressure drops, within a day the carbon-monoxide level normalises, within a year the risk of heart attack falls by about half, and within 5 years the stroke risk approaches that of a non-smoker. Nicotine replacement, varenicline, or counselling all improve quit rates."),
    ],
}


# ---------------- new intent examples ----------------

NEW_INTENTS = [
    # greeting
    ("salaam alaykum", "greeting"), ("how do you do", "greeting"),
    ("hi medfaq", "greeting"), ("hello there assistant", "greeting"),
    ("good evening doctor", "greeting"),
    # thanks
    ("jazak allah", "thanks"), ("really appreciate it", "thanks"),
    ("you saved my evening", "thanks"), ("thanks heaps", "thanks"),
    # frustration
    ("you are wrong", "frustration"), ("worst chatbot ever", "frustration"),
    ("not what i asked", "frustration"),
    # help
    ("what services do you provide", "help"),
    ("list of specialties please", "help"),
    ("what categories are there", "help"),
    # definition
    ("what is rheumatic heart disease", "ask_definition"),
    ("define plantar fasciitis", "ask_definition"),
    ("what does interventional radiology mean", "ask_definition"),
    ("explain a stress test", "ask_definition"),
    ("define hfpef", "ask_definition"),
    ("what is dry needling", "ask_definition"),
    ("what does dexa scan stand for", "ask_definition"),
    ("define holter monitor", "ask_definition"),
    # preparation
    ("any prep for dexa", "ask_preparation"),
    ("do i fast before stress test", "ask_preparation"),
    ("preparation before ultrasound", "ask_preparation"),
    ("what to wear for pet ct", "ask_preparation"),
    ("can i drink water before angiogram", "ask_preparation"),
    # recovery
    ("how long bed rest after angiogram", "ask_recovery"),
    ("when can i go back to gym after stent", "ask_recovery"),
    ("recovery after rheumatic valve surgery", "ask_recovery"),
    ("how soon can i drive after sedation", "ask_recovery"),
    # medication
    ("how to take dual antiplatelet", "ask_medication"),
    ("can i stop ticagrelor", "ask_medication"),
    ("any concern with paracetamol and blood thinner", "ask_medication"),
    ("missed two days of statin", "ask_medication"),
    ("safe painkiller in heart failure", "ask_medication"),
    # symptom
    ("my heel hurts in the morning", "ask_symptom"),
    ("i hear clicking in my knee", "ask_symptom"),
    ("my shoulder is frozen", "ask_symptom"),
    ("my legs go numb after walking", "ask_symptom"),
    ("dizzy when i bend down", "ask_symptom"),
    ("chest pain when i lie down", "ask_symptom"),
    ("breath gets short on stairs", "ask_symptom"),
    ("woke up at night with palpitations", "ask_symptom"),
    # lifestyle
    ("can heart patients fast in ramadan", "ask_lifestyle"),
    ("safe exercises after stent", "ask_lifestyle"),
    ("good diet for fatty liver", "ask_lifestyle"),
    ("can i drive long distance after surgery", "ask_lifestyle"),
    ("smoking quit support", "ask_lifestyle"),
    # procedure
    ("how does a fluoroscopy work", "ask_procedure"),
    ("what happens during a dexa", "ask_procedure"),
    ("how long does a holter take", "ask_procedure"),
    ("what is a tilt table test", "ask_procedure"),
    ("how is interventional radiology done", "ask_procedure"),
    # warning
    ("when is chest pain a red flag", "ask_warning"),
    ("red flags after a stent", "ask_warning"),
    ("post procedure danger signs", "ask_warning"),
    ("emergency signs of stroke", "ask_warning"),
    ("signs of clot in leg", "ask_warning"),
    ("when to call ambulance for palpitations", "ask_warning"),
]


# ---------------- new NER examples ----------------

NEW_NER_SENTS = [
    "my heel hurts after walking",
    "the cardiologist recommended a beta blocker",
    "she needs a holter monitor for one day",
    "stent placement requires dual antiplatelet therapy",
    "the radiologist found an incidental finding on the CT",
    "rheumatic heart disease is common in pakistan",
    "my chest feels tight at night",
    "i have severe back pain after the gym",
    "the doctor said i need an echocardiogram next week",
    "i missed two doses of atorvastatin",
    "the dexa scan showed mild osteoporosis",
    "my mother is on warfarin for atrial fibrillation",
    "i felt dizzy this morning when i stood up",
    "my neck has been stiff for a week",
    "her angiogram showed a 70 percent blockage",
    "the patient suffered a stroke at 55 years old",
    "i hear a clicking in my left knee",
    "my child has a fever and a cough",
    "the ultrasound was painless and quick",
    "his ankle is swollen after the fall",
]


# ---------------- new eval queries ----------------

NEW_EVAL = [
    # radiology
    {"specialty": "radiology", "query": "what is ultrasound",
     "expected_keyword": "sound waves"},
    {"specialty": "radiology", "query": "what does dexa measure",
     "expected_keyword": "dense"},
    {"specialty": "radiology", "query": "is pet ct safe with diabetes",
     "expected_keyword": "diabetes"},
    {"specialty": "radiology", "query": "incidental finding mean",
     "expected_keyword": "incidental"},
    {"specialty": "radiology", "query": "why no metal in mri",
     "expected_keyword": "magnet"},
    {"specialty": "radiology", "query": "drive after contrast",
     "expected_keyword": "drive"},
    {"specialty": "radiology", "query": "ct radiation dose",
     "expected_keyword": "mSv"},
    {"specialty": "radiology", "query": "fluoroscopy what is it",
     "expected_keyword": "real-time"},
    {"specialty": "radiology", "query": "interventional radiology procedures",
     "expected_keyword": "minimally invasive"},
    {"specialty": "radiology", "query": "breastfeed after gadolinium",
     "expected_keyword": "breast"},
    {"specialty": "radiology", "query": "child mri sedation",
     "expected_keyword": "sedation"},
    {"specialty": "radiology", "query": "hold breath during scan why",
     "expected_keyword": "movement"},
    # physiotherapy
    {"specialty": "physiotherapy", "query": "what is dry needling",
     "expected_keyword": "trigger"},
    {"specialty": "physiotherapy", "query": "heat or ice for sprain",
     "expected_keyword": "ice"},
    {"specialty": "physiotherapy", "query": "bed rest for back",
     "expected_keyword": "bed rest"},
    {"specialty": "physiotherapy", "query": "how long to hold a stretch",
     "expected_keyword": "20"},
    {"specialty": "physiotherapy", "query": "prevent back pain at desk",
     "expected_keyword": "desk"},
    {"specialty": "physiotherapy", "query": "knee clicking pain",
     "expected_keyword": "click"},
    {"specialty": "physiotherapy", "query": "best sleep position back",
     "expected_keyword": "sleep"},
    {"specialty": "physiotherapy", "query": "plantar fasciitis shoes",
     "expected_keyword": "plantar"},
    {"specialty": "physiotherapy", "query": "frozen shoulder treatment",
     "expected_keyword": "frozen"},
    {"specialty": "physiotherapy", "query": "duration of physio session",
     "expected_keyword": "session"},
    {"specialty": "physiotherapy", "query": "exercise through pain ok",
     "expected_keyword": "pain"},
    {"specialty": "physiotherapy", "query": "sciatica recovery",
     "expected_keyword": "sciatic"},
    {"specialty": "physiotherapy", "query": "vertigo physio help",
     "expected_keyword": "vestibular"},
    # cardiovascular
    {"specialty": "cardiovascular", "query": "what is a holter",
     "expected_keyword": "ECG"},
    {"specialty": "cardiovascular", "query": "stress test what to expect",
     "expected_keyword": "treadmill"},
    {"specialty": "cardiovascular", "query": "angiogram procedure",
     "expected_keyword": "dye"},
    {"specialty": "cardiovascular", "query": "what is a stent",
     "expected_keyword": "narrowed"},
    {"specialty": "cardiovascular", "query": "flying after heart attack",
     "expected_keyword": "fly"},
    {"specialty": "cardiovascular", "query": "rheumatic heart disease",
     "expected_keyword": "valve"},
    {"specialty": "cardiovascular", "query": "blood tests heart",
     "expected_keyword": "lipid"},
    {"specialty": "cardiovascular", "query": "heart rate variability",
     "expected_keyword": "variability"},
    {"specialty": "cardiovascular", "query": "home bp measurement method",
     "expected_keyword": "5 minutes"},
    {"specialty": "cardiovascular", "query": "salt limit per day",
     "expected_keyword": "5"},
    {"specialty": "cardiovascular", "query": "high cholesterol dangers",
     "expected_keyword": "plaque"},
    {"specialty": "cardiovascular", "query": "young person heart attack",
     "expected_keyword": "young"},
    {"specialty": "cardiovascular", "query": "preserved ejection fraction",
     "expected_keyword": "relax"},
    {"specialty": "cardiovascular", "query": "left bundle branch block",
     "expected_keyword": "electrical"},
    {"specialty": "cardiovascular", "query": "benefits of quitting smoking",
     "expected_keyword": "quit"},
]


# ---------------- new chat-log sessions ----------------

NEW_CHAT_LOGS = [
    {
        "session_id": "log-rad-004",
        "specialty": "radiology",
        "turns": [
            {"role": "user", "text": "how is an ultrasound done"},
            {"role": "bot", "text": "A gel is applied and a small probe..."},
            {"role": "user", "text": "is there any radiation"},
            {"role": "bot", "text": "No, ultrasound uses no ionising radiation."},
        ],
    },
    {
        "session_id": "log-rad-005",
        "specialty": "radiology",
        "turns": [
            {"role": "user", "text": "my report says incidental finding"},
            {"role": "bot", "text": "Incidental findings are picked up by chance..."},
        ],
    },
    {
        "session_id": "log-phy-004",
        "specialty": "physiotherapy",
        "turns": [
            {"role": "user", "text": "what is dry needling"},
            {"role": "bot", "text": "Dry needling uses thin needles to release trigger points..."},
            {"role": "user", "text": "will it hurt"},
            {"role": "bot", "text": "Brief twitch and 24-48h soreness are common."},
        ],
    },
    {
        "session_id": "log-phy-005",
        "specialty": "physiotherapy",
        "turns": [
            {"role": "user", "text": "frozen shoulder how long"},
            {"role": "bot", "text": "Typically 12-30 months across three phases..."},
        ],
    },
    {
        "session_id": "log-cv-006",
        "specialty": "cardiovascular",
        "turns": [
            {"role": "user", "text": "what is a stent"},
            {"role": "bot", "text": "A small mesh tube placed inside a narrowed artery..."},
            {"role": "user", "text": "how long do i take antiplatelet"},
            {"role": "bot", "text": "At least 6-12 months, do not stop without advice."},
        ],
    },
    {
        "session_id": "log-cv-007",
        "specialty": "cardiovascular",
        "turns": [
            {"role": "user", "text": "can i fast in ramadan after stent"},
            {"role": "bot", "text": "Most patients can fast with adjusted medication timing..."},
        ],
    },
    {
        "session_id": "log-cv-008",
        "specialty": "cardiovascular",
        "turns": [
            {"role": "user", "text": "rheumatic heart disease in pakistan"},
            {"role": "bot", "text": "Still common; prevention with penicillin prophylaxis is key."},
        ],
    },
]


# ---------------- writers ----------------


def _load(name: str) -> list[dict]:
    p = HERE / name
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save(name: str, data: list[dict]) -> None:
    p = HERE / name
    p.write_text(
        "[\n" + ",\n".join(
            json.dumps(d, ensure_ascii=False) for d in data
        ) + "\n]\n",
        encoding="utf-8",
    )


def expand_faqs() -> int:
    added = 0
    for spec, items in NEW_FAQS.items():
        name = f"faqs_{spec}.json"
        existing = _load(name)
        seen = {(it["question"] or "").strip().lower() for it in existing}
        for q, a in items:
            if q.strip().lower() in seen:
                continue
            existing.append({
                "specialty": spec, "question": q,
                "answer": a, "approved": True,
            })
            seen.add(q.strip().lower())
            added += 1
        _save(name, existing)
    return added


def append_jsonl(name: str, records: list[dict],
                 dedup_key: str | None = None) -> int:
    p = HERE / name
    existing: list[dict] = []
    seen: set[str] = set()
    if p.is_file():
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    existing.append(rec)
                    if dedup_key and dedup_key in rec:
                        seen.add(str(rec[dedup_key]).strip().lower())
                except json.JSONDecodeError:
                    continue
    added = 0
    for rec in records:
        if dedup_key:
            k = str(rec.get(dedup_key, "")).strip().lower()
            if k and k in seen:
                continue
            if k:
                seen.add(k)
        existing.append(rec)
        added += 1
    with p.open("w", encoding="utf-8") as f:
        for rec in existing:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return added


def main() -> None:
    print(f"FAQs added: {expand_faqs()}")
    # The other JSONLs are regenerated by build_jsonl.py, so the new
    # NEW_INTENTS/NEW_NER/NEW_EVAL/NEW_CHAT_LOGS are integrated through
    # the build script by importing this module — see build_jsonl.py.


if __name__ == "__main__":
    main()
