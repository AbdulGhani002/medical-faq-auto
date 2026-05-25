# Retrieval evaluation report

| Metric | Value |
|---|---:|
| Precision@1 | **0.929** |
| MRR | **0.941** |
| Recall@5 | **0.955** |
| Median latency | 101.0 ms |
| p95 latency | 136.0 ms |
| Queries | 156 |


## Per-specialty breakdown

| Specialty | n | P@1 | Recall@5 | MRR |
|---|---:|---:|---:|---:|
| cardiovascular | 60 | 0.917 | 0.950 | 0.933 |
| physiotherapy | 50 | 0.980 | 0.980 | 0.980 |
| radiology | 46 | 0.891 | 0.935 | 0.908 |

## Failed queries (rank > 1)

| Query | Expected | Matched | Rank |
|---|---|---|---:|
| pet scan | `positron` | What is a PET-CT scan? | — |
| when to take bp meds | `once a day` | What is white coat hypertension? | — |
| what if i miss my hypertension dose | `miss` | What is white coat hypertension? | 2 |
| hold breath during scan why | `movement` | Why do I have to hold my breath during a scan? | — |
| exercise through pain ok | `pain` | — | — |
| flying after heart attack | `fly` | What is post-MI rehabilitation? | 2 |
| home bp measurement method | `5 minutes` | What is white coat hypertension? | — |
| vq scan what is it | `ventilation` | What is a PET scan? | 4 |
| abdominal ultrasound prep | `fast` | Can I have a scan if I am pregnant? | — |
| mrcp duration | `MRCP` | How long does an MRI take? | 2 |
| herbs interfere with heart meds | `interact` | What is pulmonary hypertension? | — |