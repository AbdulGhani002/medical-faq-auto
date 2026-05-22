# Retrieval evaluation report

| Metric | Value |
|---|---:|
| Precision@1 | **0.931** |
| MRR | **0.938** |
| Recall@5 | **0.948** |
| Median latency | 22.0 ms |
| p95 latency | 36.0 ms |
| Queries | 116 |


## Per-specialty breakdown

| Specialty | n | P@1 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| cardiovascular | 45 | 0.956 | 0.978 | 0.967 |
| physiotherapy | 35 | 0.971 | 0.971 | 0.971 |
| radiology | 36 | 0.861 | 0.889 | 0.870 |

## Failed queries (rank > 1)

| Query | Expected | Matched | Rank |
|---|---|---|---:|
| wat is mri vs ct | `magnetic` | What is the difference between an MRI and a CT scan? | — |
| pet scan | `positron` | What is a PET-CT scan? | — |
| when to take bp meds | `once a day` | What is white coat hypertension? | — |
| what if i miss my hypertension dose | `miss` | What is white coat hypertension? | 2 |
| hold breath during scan why | `movement` | Why do I have to hold my breath during a scan? | — |
| exercise through pain ok | `pain` | — | — |
| vq scan what is it | `ventilation` | What is a PET scan? | 3 |
| abdominal ultrasound prep | `fast` | Can I have a scan if I am pregnant? | — |