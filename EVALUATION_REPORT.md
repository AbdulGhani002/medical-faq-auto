# Retrieval evaluation report

| Metric | Value |
|---|---:|
| Precision@1 | **0.920** |
| MRR | **0.925** |
| Recall@5 | **0.931** |
| Median latency | 30.0 ms |
| p95 latency | 49.0 ms |
| Queries | 87 |


## Per-specialty breakdown

| Specialty | n | P@1 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| cardiovascular | 35 | 0.943 | 0.971 | 0.957 |
| physiotherapy | 25 | 0.920 | 0.920 | 0.920 |
| radiology | 27 | 0.889 | 0.889 | 0.889 |

## Failed queries (rank > 1)

| Query | Expected | Matched | Rank |
|---|---|---|---:|
| wat is mri vs ct | `magnetic` | What is the difference between an MRI and a CT scan? | — |
| pet scan | `positron` | What is a PET-CT scan? | — |
| when to take bp meds | `once a day` | What is white coat hypertension? | — |
| what if i miss my hypertension dose | `miss` | What is white coat hypertension? | 2 |
| hold breath during scan why | `movement` | Why do I have to hold my breath during a scan? | — |
| exercise through pain ok | `pain` | — | — |
| sciatica recovery | `sciatic` | What is a frozen shoulder? | — |