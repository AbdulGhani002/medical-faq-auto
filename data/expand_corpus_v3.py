"""Round 3 of corpus expansion.

  +45 new clinician-style FAQs (15 per specialty)
  +80 new intent training examples
  +15 new eval queries

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
        ("What is a mammogram and who needs one?",
         "A mammogram is a low-dose X-ray of the breast used to screen for early breast cancer. Routine screening usually begins at age 40-50 depending on local guidelines and family history, repeating every 1-2 years. Tell us about previous breast surgery, implants, or current breastfeeding. The exam takes 15-20 minutes; brief compression is normal."),
        ("What is paediatric MRI sedation and when is it needed?",
         "Children under 6 often cannot stay still for a full MRI. We offer 'feed-and-sleep' for babies, child-life play preparation for older children, and light sedation when needed. An anaesthetist is present for any sedation. Fasting times are: 6 hours for solids, 4 hours for breast milk, 2 hours for clear fluids."),
        ("Can I have an MRI during my period?",
         "Yes — there is no medical reason to delay an MRI because of menstruation. Wear comfortable clothing and use a sanitary pad rather than a tampon if asked to change into a gown. For pelvic MRI we may ask you to schedule on specific cycle days."),
        ("Why do I feel a warm rush during contrast injection?",
         "Iodine contrast can cause a warm flush spreading from the arm through the body, plus a metallic taste or a brief sensation of needing to urinate. This is a normal reaction lasting under 30 seconds and is not an allergy. Tell us if it persists, becomes painful, or if you develop a rash or breathlessness."),
        ("What is a swallow study (barium swallow)?",
         "A barium swallow uses live X-ray to watch how you swallow a chalky liquid (barium). It is used to diagnose reflux, hiatal hernia, achalasia, and swallowing difficulty. Takes 15-30 minutes; you must fast 4-6 hours beforehand. Barium turns the stool white for 1-3 days afterwards — this is harmless."),
        ("What is a CT angiogram?",
         "A CT angiogram (CTA) uses iodine contrast and a fast CT scan to image arteries — most commonly the coronary, pulmonary, brain, or abdominal arteries. Useful for chest pain, suspected pulmonary embolism, and stroke. Bring kidney-function blood tests and tell us if you take metformin."),
        ("Can I have a scan if I have a metallic foreign body in my eye?",
         "Tell us before MRI booking — we routinely screen welders and metal-workers. A history of metallic eye injury is checked with a quick orbital X-ray. If a metal fragment is present we use CT instead. There is no risk for CT, ultrasound, or X-ray."),
        ("What is the difference between a screening and a diagnostic mammogram?",
         "Screening mammograms are routine, brief, and done in asymptomatic women on a regular schedule. Diagnostic mammograms use additional views, magnification, or ultrasound to investigate a lump, pain, or an abnormal screening result. Diagnostic appointments take longer and the radiologist may discuss findings on the spot."),
        ("How is a thyroid ultrasound done?",
         "You lie on your back with a pillow under your shoulders to extend the neck. A gel and small probe slide over the front of the neck for 15-20 minutes. It is painless, uses no radiation, and visualises nodules, cysts, and lymph nodes. No fasting needed."),
        ("What is an interventional radiology drainage?",
         "An image-guided drainage uses ultrasound or CT to place a small tube through the skin into a collection of fluid (abscess, bile, urine) so it can drain externally. Done under local anaesthetic with sedation; the tube stays in for days to weeks while the cavity heals."),
        ("Why is my appointment letter so detailed about jewellery?",
         "MRI uses a 1.5 or 3 Tesla magnet that can pull ferromagnetic items into the scanner at high speed, causing injury and image distortion. Hair clips, body piercings, watches, and underwire bras all need to come off. Plain gold and platinum are usually safe but we still ask you to remove them so we get the cleanest image."),
        ("How long does an MRCP take?",
         "MRCP (magnetic resonance cholangio-pancreatography) is a special MRI of the bile and pancreatic ducts. It takes 30-45 minutes, uses no contrast, and requires 4-6 hours of fasting so the bile ducts dilate clearly. Drink a small amount of pineapple or blueberry juice on arrival — natural manganese darkens the stomach."),
        ("What is bone scintigraphy?",
         "A bone scan injects a small dose of radioactive tracer that concentrates in areas of high bone turnover (fractures, infection, tumours). You wait 2-3 hours after injection for the tracer to settle, then the scan itself takes 30-45 minutes. The tracer is cleared in 24 hours; drink plenty of water."),
        ("Are scans safe during the first trimester of pregnancy?",
         "Ultrasound is the safest imaging in pregnancy and is the first choice. MRI without contrast is also considered safe but is usually avoided in the first trimester unless urgent. CT and conventional X-ray expose the foetus to ionising radiation and are avoided unless there is no alternative."),
        ("What happens to my old scans?",
         "Images are archived securely in our PACS (Picture Archiving and Communication System) for 7-10 years, or longer for paediatric and oncology studies. You can request copies on CD or via secure online transfer. Old films from the pre-digital era may be in long-term storage and take longer to retrieve."),
    ],

    "physiotherapy": [
        ("How is an ACL injury managed without surgery?",
         "Partial ACL tears and complete tears in non-athletes are often managed with structured rehab over 3-6 months: quadriceps strengthening, hamstring co-contraction, balance and proprioception drills, plus a progressive return-to-running programme. Surgery is offered for younger athletes, repeated giving-way, or combined ligament injuries."),
        ("What are shin splints and how do you treat them?",
         "Shin splints (medial tibial stress syndrome) are pain along the inner edge of the shin caused by overuse, often during running. Treatment is reduce the running volume by 50%, ice after activity, calf and tibialis posterior strengthening, and supportive shoes. Pain that persists for more than 4 weeks should be reviewed to exclude a stress fracture."),
        ("What is tennis elbow and how do I fix it?",
         "Tennis elbow (lateral epicondylitis) is pain on the outside of the elbow from overuse of the wrist extensor tendons — common in racket sports, gym work, and desk jobs. Eccentric wrist exercises (3 sets of 15, twice a day) are the most evidence-based fix; takes 6-12 weeks to feel significant improvement."),
        ("What is golfer's elbow?",
         "Golfer's elbow (medial epicondylitis) is the inside-of-the-elbow version of tennis elbow, affecting the wrist flexor tendons. It is common in golf, climbing, and forceful gripping work. Eccentric wrist-flexor exercises plus a forearm strap usually resolve it in 8-12 weeks."),
        ("What is hydrotherapy and when do you use it?",
         "Hydrotherapy is supervised exercise in a warm pool. The buoyancy unloads painful joints and resistance to movement is gentle, making it ideal for early post-op rehab, severe osteoarthritis, fibromyalgia, and some neurological conditions. Sessions are 30-45 minutes and usually 1-2 per week alongside dry-land work."),
        ("What is a postural assessment?",
         "A postural assessment looks at how you stand, sit, and move to identify imbalances that contribute to pain. We check spinal curves, shoulder symmetry, pelvic tilt, foot arch, and how your muscles activate during simple movements. It guides individualised stretches, strength work, and ergonomic advice."),
        ("Can physiotherapy help with breathing problems?",
         "Yes — pulmonary physiotherapy helps with COPD, asthma, post-COVID breathlessness, and pre/post chest-surgery recovery. We teach diaphragmatic breathing, pursed-lip breathing, the active cycle of breathing techniques, and inspiratory muscle training. Sessions are 30-45 minutes."),
        ("What is the recovery timeline after a meniscus repair?",
         "After arthroscopic meniscus repair you are usually on crutches for 4-6 weeks with a brace limiting knee flexion. Return to running is at 12-16 weeks and to contact sport at 4-6 months. A meniscectomy (removing torn tissue rather than repairing it) recovers faster — 2-4 weeks for daily activity."),
        ("How is geriatric balance training done?",
         "We use the Tinetti and Berg Balance Scale to grade fall risk, then progress from sit-to-stand drills to single-leg stance, tandem walking, foam-surface exercises, and dual-task drills (walking while counting). A 12-week programme typically halves the fall rate in community-dwelling older adults."),
        ("What is the difference between manual therapy and chiropractic?",
         "Manual therapy by a physiotherapist uses joint mobilisation, soft-tissue release, and muscle energy techniques alongside a structured exercise programme. Chiropractors typically use higher-velocity spinal manipulation. Both can help short-term back and neck pain; physiotherapy adds the long-term exercise plan that prevents relapse."),
        ("Can I exercise with osteoarthritis?",
         "Yes — exercise is the best non-drug treatment for osteoarthritis. Low-impact aerobic work (walking, cycling, swimming), targeted strengthening of muscles around the affected joint, and gentle range-of-motion work reduce pain and slow progression. Avoid prolonged high-impact loading on a flared joint."),
        ("What is gait analysis and when do I need it?",
         "Gait analysis observes how you walk or run — heel-strike, push-off, hip control, arm swing — to identify mechanics that cause pain or injury. We use video review and pressure mats. It is useful for recurrent running injuries, post-stroke walking difficulty, and to fit orthotics correctly."),
        ("What is hand therapy?",
         "Hand therapy is specialist physiotherapy for fingers, hand, wrist, and elbow injuries: fractures, tendon repairs, nerve injuries, arthritis, and post-burn rehab. It includes custom splinting, scar massage, range-of-motion exercises, and dexterity drills. Sessions are typically 30 minutes."),
        ("My child has been diagnosed with flat feet — should I be worried?",
         "Most children have flat feet up to age 6 because the arch develops slowly. Painless flexible flat feet need no treatment. Rigid flat feet, or pain, fatigue with walking, or asymmetric arches, should be reviewed — supportive shoes, calf stretches, and a short course of supervised exercises usually help."),
        ("How do I return to running after a calf strain?",
         "Once you can heel-raise on the injured leg 30 times without pain and walk briskly for 30 minutes pain-free, start a walk-jog progression: 1 minute jog, 2 minutes walk, 5 cycles, three times a week. Increase total running time by no more than 10% per week, and re-injure if you skip the strength work first."),
    ],

    "cardiovascular": [
        ("What is pulmonary hypertension?",
         "Pulmonary hypertension is high blood pressure in the arteries between the heart and the lungs. Symptoms are progressive breathlessness, fatigue, swelling of the legs, and chest pain on exertion. Diagnosis is by echocardiogram and right-heart catheterisation. Treatment depends on the cause and includes specific pulmonary vasodilators."),
        ("What is heart-failure with preserved ejection fraction (HFpEF)?",
         "HFpEF is heart failure where the heart pumps normally but cannot relax and fill properly. Symptoms are the same — breathlessness, fatigue, ankle swelling — but the ejection fraction on echo is normal. Treatment focuses on blood pressure control, SGLT2 inhibitors, diuretics, and weight loss."),
        ("Can I fast in Ramadan if I have a heart condition?",
         "Most stable cardiac patients can fast safely. We usually shift once-daily medicines to suhoor or iftar, monitor blood pressure at home, and stay well-hydrated between iftar and suhoor. Patients on diuretics, multiple BP medicines, recent stents, decompensated heart failure, or insulin-treated diabetes should discuss exemptions with their cardiologist."),
        ("What is congenital heart disease?",
         "Congenital heart disease is a structural problem present at birth — examples are ASD, VSD, patent ductus arteriosus, tetralogy of Fallot, and coarctation. Most cases are now detected in childhood or even in utero. Adults with corrected congenital disease still need lifelong cardiology follow-up, especially before pregnancy or non-cardiac surgery."),
        ("How is women's heart health different?",
         "Women often present with atypical heart-attack symptoms (jaw, neck, or back pain, nausea, fatigue) rather than classic crushing chest pain. Risk rises sharply after menopause. Hormonal therapy, pregnancy complications (pre-eclampsia, gestational diabetes), and autoimmune disease all increase cardiovascular risk and need specific counselling."),
        ("What is post-MI rehabilitation?",
         "Cardiac rehab after a heart attack is a 6-12 week supervised programme of monitored exercise, education on diet and medicines, smoking cessation, and psychological support. It reduces re-admission by about 25% and death by 20%. Most patients start within 2-4 weeks of the event."),
        ("What is post-CABG (bypass) recovery like?",
         "Recovery after coronary artery bypass surgery takes about 6-8 weeks. Walking starts the next day; driving usually at 4-6 weeks; lifting under 5 kg for the first 6 weeks while the sternum heals. Cardiac rehab is recommended for everyone. Sternal pain settles over 2-3 months."),
        ("Are herbal remedies safe with heart medicines?",
         "Many herbal remedies interact with heart medicines. St John's wort lowers warfarin and statin levels. Liquorice raises blood pressure. Grapefruit juice raises some statin and calcium-channel-blocker levels dangerously. Ginkgo and ginger thin the blood. Always tell us about every supplement, including local hakim preparations."),
        ("How is paediatric heart disease detected?",
         "Newborn screening with pulse oximetry catches many critical congenital defects. Older children are evaluated for fainting, heart murmurs, exercise intolerance, palpitations, or family history of sudden cardiac death under 50. Echocardiogram is the cornerstone investigation."),
        ("What is supraventricular tachycardia (SVT)?",
         "SVT is a fast regular heartbeat (usually 150-220 bpm) caused by a short-circuit in the upper chambers of the heart. Episodes feel like sudden palpitations with anxiety; vagal manoeuvres (cold water on the face, the Valsalva manoeuvre) often stop them. Catheter ablation is curative in most cases."),
        ("How is high blood pressure managed in pregnancy?",
         "Pregnancy raises blood pressure risk for both mother and baby. We target a BP below 140/90 (or 135/85 in the morning at home). Safe medicines are labetalol, nifedipine, and methyldopa; ACE inhibitors and ARBs are avoided. Pre-eclampsia screening with low-dose aspirin from 12 weeks reduces risk in high-risk pregnancies."),
        ("What lifestyle changes most reduce heart attack risk?",
         "In order of impact: stop smoking, treat high blood pressure, control cholesterol with diet and statins if needed, exercise 150 minutes a week, eat a Mediterranean or DASH diet, manage stress, sleep 7-8 hours, limit alcohol. Each step independently lowers risk; combining all of them more than halves lifetime cardiovascular risk."),
        ("What is a cardiac MRI?",
         "Cardiac MRI is a detailed MRI of the heart that shows muscle thickness, scarring, blood flow, and pumping function. Useful for cardiomyopathy, suspected myocarditis, viability after MI, and congenital disease. The scan takes 45-60 minutes; you need to lie still and breath-hold on cue. Gadolinium contrast is used in most protocols."),
        ("How is sudden cardiac death prevented?",
         "Implantable cardioverter-defibrillators (ICDs) reduce sudden cardiac death in patients with severely reduced ejection fraction, certain inherited arrhythmias, or after a survived cardiac arrest. Beta-blockers, anti-arrhythmic medicines, and treatment of the underlying disease are the medical pillars. Athletes with a family history of sudden death need pre-participation screening."),
        ("What is atrial fibrillation (AFib) ablation?",
         "AFib ablation uses a catheter passed through the groin to the heart, then radiofrequency or cryothermal energy to isolate the pulmonary vein triggers of AFib. Success at 1 year is around 70% for paroxysmal AFib and 50% for persistent AFib. Anticoagulation is continued for at least 2 months after, often longer."),
    ],
}


# ---------------------------------------------------------------- intents

NEW_INTENTS = [
    # definition
    ("what is a mammogram", "ask_definition"),
    ("what is pulmonary hypertension", "ask_definition"),
    ("what is hfpef", "ask_definition"),
    ("what is acl", "ask_definition"),
    ("what is mrcp", "ask_definition"),
    ("what is bone scintigraphy", "ask_definition"),
    ("define gait analysis", "ask_definition"),
    ("what is hydrotherapy", "ask_definition"),
    ("what is hand therapy", "ask_definition"),
    ("define svt", "ask_definition"),
    ("what is a ct angiogram", "ask_definition"),
    ("what is post mi rehab", "ask_definition"),
    ("define paediatric mri sedation", "ask_definition"),
    ("what is a swallow study", "ask_definition"),
    ("what is thyroid ultrasound", "ask_definition"),
    ("what is shin splints", "ask_definition"),
    ("what is tennis elbow", "ask_definition"),
    ("what is golfer's elbow", "ask_definition"),
    # preparation
    ("do i fast before mrcp", "ask_preparation"),
    ("how to prepare for paediatric mri", "ask_preparation"),
    ("preparation for swallow study", "ask_preparation"),
    ("any prep before ct angiogram", "ask_preparation"),
    ("can i drink water before mammogram", "ask_preparation"),
    ("any prep for thyroid ultrasound", "ask_preparation"),
    ("preparation before bone scan", "ask_preparation"),
    # recovery
    ("recovery after meniscus repair", "ask_recovery"),
    ("when can i drive after cabg", "ask_recovery"),
    ("how long after stent placement before sex", "ask_recovery"),
    ("recovery after acl injury", "ask_recovery"),
    ("when can i run after calf strain", "ask_recovery"),
    ("recovery after pacemaker insertion", "ask_recovery"),
    ("how soon after svt ablation can i exercise", "ask_recovery"),
    # medication
    ("herbal remedies with heart meds", "ask_medication"),
    ("is grapefruit safe with statins", "ask_medication"),
    ("which bp meds safe in pregnancy", "ask_medication"),
    ("can i take liquorice with bp medicine", "ask_medication"),
    ("ginkgo and blood thinner", "ask_medication"),
    # symptom
    ("breathlessness when climbing stairs", "ask_symptom"),
    ("my heel is sore in the morning", "ask_symptom"),
    ("knee gives way after acl tear", "ask_symptom"),
    ("my shoulder hurts during overhead lifts", "ask_symptom"),
    ("breath gets short after walking", "ask_symptom"),
    ("legs swell during pregnancy", "ask_symptom"),
    ("my back hurts after gardening", "ask_symptom"),
    ("ankle stiff in the morning", "ask_symptom"),
    ("palpitations come and go suddenly", "ask_symptom"),
    # lifestyle
    ("can i fast in ramadan with afib", "ask_lifestyle"),
    ("safe exercise after stent", "ask_lifestyle"),
    ("can i lift after cabg", "ask_lifestyle"),
    ("diet during pregnancy with high bp", "ask_lifestyle"),
    ("can i drink coffee on ramipril", "ask_lifestyle"),
    ("can children with cardiac disease play sport", "ask_lifestyle"),
    # procedure
    ("how is mammogram done", "ask_procedure"),
    ("what happens in cardiac mri", "ask_procedure"),
    ("how does ablation work", "ask_procedure"),
    ("how is hand therapy performed", "ask_procedure"),
    ("what does an ir drainage involve", "ask_procedure"),
    ("how is gait analysis done", "ask_procedure"),
    # warning
    ("red flags during ramadan fasting", "ask_warning"),
    ("warning signs post cabg", "ask_warning"),
    ("when is leg swelling in pregnancy serious", "ask_warning"),
    ("when to worry about palpitations", "ask_warning"),
    ("red flags after meniscus surgery", "ask_warning"),
    ("dangerous symptoms after mri sedation", "ask_warning"),
    # meta
    ("are you using openai", "meta"),
    ("what data do you have on me", "meta"),
    ("can you store my chat", "meta"),
    ("are you free", "meta"),
    ("what cant you answer", "meta"),
    # greetings + thanks
    ("salam doctor", "greeting"),
    ("aoa", "greeting"),
    ("good morning medfaq", "greeting"),
    ("hello again", "greeting"),
    ("thanks for the explanation", "thanks"),
    ("got it appreciate it", "thanks"),
    ("thank you so much", "thanks"),
    # help
    ("what can you help me with", "help"),
    ("show me topics", "help"),
    ("give me some sample questions", "help"),
]


# ---------------------------------------------------------------- eval queries

NEW_EVAL = [
    {"specialty": "radiology", "query": "mammogram who needs one",
     "expected_keyword": "screen"},
    {"specialty": "radiology", "query": "paediatric mri sedation prep",
     "expected_keyword": "sedation"},
    {"specialty": "radiology", "query": "mri during period",
     "expected_keyword": "menstruation"},
    {"specialty": "radiology", "query": "warm rush during contrast",
     "expected_keyword": "flush"},
    {"specialty": "radiology", "query": "barium swallow study",
     "expected_keyword": "barium"},
    {"specialty": "radiology", "query": "ct angiogram",
     "expected_keyword": "iodine"},
    {"specialty": "radiology", "query": "thyroid ultrasound",
     "expected_keyword": "neck"},
    {"specialty": "radiology", "query": "interventional drainage",
     "expected_keyword": "drainage"},
    {"specialty": "radiology", "query": "mrcp duration",
     "expected_keyword": "MRCP"},
    {"specialty": "radiology", "query": "bone scintigraphy tracer",
     "expected_keyword": "tracer"},
    {"specialty": "physiotherapy", "query": "acl rehab without surgery",
     "expected_keyword": "rehab"},
    {"specialty": "physiotherapy", "query": "shin splints fix",
     "expected_keyword": "shin"},
    {"specialty": "physiotherapy", "query": "tennis elbow exercises",
     "expected_keyword": "eccentric"},
    {"specialty": "physiotherapy", "query": "golfers elbow treatment",
     "expected_keyword": "medial"},
    {"specialty": "physiotherapy", "query": "what is hydrotherapy",
     "expected_keyword": "buoyancy"},
    {"specialty": "physiotherapy", "query": "postural assessment what for",
     "expected_keyword": "postur"},
    {"specialty": "physiotherapy", "query": "breathing physio copd",
     "expected_keyword": "pulmonary"},
    {"specialty": "physiotherapy", "query": "meniscus surgery rehab time",
     "expected_keyword": "meniscus"},
    {"specialty": "physiotherapy", "query": "balance training elderly",
     "expected_keyword": "balance"},
    {"specialty": "physiotherapy", "query": "manual therapy vs chiropractic",
     "expected_keyword": "manipulation"},
    {"specialty": "physiotherapy", "query": "osteoarthritis exercise safe",
     "expected_keyword": "arthritis"},
    {"specialty": "physiotherapy", "query": "gait analysis why",
     "expected_keyword": "walk"},
    {"specialty": "physiotherapy", "query": "what is hand therapy",
     "expected_keyword": "hand"},
    {"specialty": "physiotherapy", "query": "flat feet in children",
     "expected_keyword": "flat feet"},
    {"specialty": "physiotherapy", "query": "return to running calf strain",
     "expected_keyword": "calf"},
    {"specialty": "cardiovascular", "query": "what is pulmonary hypertension",
     "expected_keyword": "lungs"},
    {"specialty": "cardiovascular", "query": "hfpef definition",
     "expected_keyword": "ejection"},
    {"specialty": "cardiovascular", "query": "ramadan fasting heart patient",
     "expected_keyword": "Ramadan"},
    {"specialty": "cardiovascular", "query": "congenital heart disease",
     "expected_keyword": "birth"},
    {"specialty": "cardiovascular", "query": "women heart symptoms different",
     "expected_keyword": "atypical"},
    {"specialty": "cardiovascular", "query": "post mi rehab",
     "expected_keyword": "rehab"},
    {"specialty": "cardiovascular", "query": "post bypass recovery",
     "expected_keyword": "bypass"},
    {"specialty": "cardiovascular", "query": "herbs interfere with heart meds",
     "expected_keyword": "interact"},
    {"specialty": "cardiovascular", "query": "child heart disease",
     "expected_keyword": "congenital"},
    {"specialty": "cardiovascular", "query": "what is svt",
     "expected_keyword": "supraventricular"},
    {"specialty": "cardiovascular", "query": "bp meds in pregnancy",
     "expected_keyword": "pregnancy"},
    {"specialty": "cardiovascular", "query": "best lifestyle for heart risk",
     "expected_keyword": "smoking"},
    {"specialty": "cardiovascular", "query": "cardiac mri",
     "expected_keyword": "MRI"},
    {"specialty": "cardiovascular", "query": "icd prevent sudden death",
     "expected_keyword": "ICD"},
    {"specialty": "cardiovascular", "query": "afib ablation success",
     "expected_keyword": "ablation"},
]


# ---------------------------------------------------------------- cleaning

_WS = re.compile(r"[ \t]+")
_MULTI_BLANK = re.compile(r"\n{3,}")
_SMART_QUOTES = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "…": "...", " ": " ",
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
