# Naive Bayes intent classifier evaluation

Stratified 80/20 split of `data/intents.jsonl`. Trained on 160 examples, evaluated on 39. **Macro-F1 = 0.650** across 12 classes.

## Per-class metrics

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| ask_warning | 1.000 | 1.000 | 1.000 | 3 |
| ask_definition | 0.800 | 1.000 | 0.889 | 4 |
| greeting | 0.667 | 1.000 | 0.800 | 4 |
| help | 1.000 | 0.667 | 0.800 | 3 |
| ask_recovery | 0.600 | 1.000 | 0.750 | 3 |
| ask_symptom | 0.750 | 0.750 | 0.750 | 4 |
| ask_preparation | 0.667 | 0.667 | 0.667 | 3 |
| frustration | 0.667 | 0.667 | 0.667 | 3 |
| ask_lifestyle | 0.500 | 0.667 | 0.571 | 3 |
| ask_medication | 1.000 | 0.333 | 0.500 | 3 |
| thanks | 0.500 | 0.333 | 0.400 | 3 |
| ask_procedure | 0.000 | 0.000 | 0.000 | 3 |

## Confusion matrix

| true ↓ / pred → | ask_definition | ask_lifestyle | ask_medication | ask_preparation | ask_procedure | ask_recovery | ask_symptom | ask_warning | frustration | greeting | help | thanks |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **ask_definition** | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **ask_lifestyle** | 0 | 2 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| **ask_medication** | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **ask_preparation** | 0 | 0 | 0 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **ask_procedure** | 1 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| **ask_recovery** | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| **ask_symptom** | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 1 | 0 | 0 |
| **ask_warning** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| **frustration** | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 2 | 0 | 0 | 0 |
| **greeting** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 |
| **help** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 1 |
| **thanks** | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 |

## Misclassifications

| text | true | predicted |
|---|---|---|
| waste of time | frustration | ask_recovery |
| i feel tired all day | ask_symptom | greeting |
| super helpful | thanks | frustration |
| what does a physiotherapist do | ask_procedure | ask_definition |
| which painkiller is safe with my bp meds | ask_medication | ask_lifestyle |
| how long is the mri appointment | ask_procedure | ask_recovery |
| help | help | thanks |
| is coffee bad for my heart | ask_lifestyle | ask_symptom |
| how to prepare for a ct scan | ask_preparation | ask_procedure |
| steps of a stress test | ask_procedure | ask_preparation |
| shukria | thanks | greeting |
| painkillers safe with my heart | ask_medication | ask_lifestyle |