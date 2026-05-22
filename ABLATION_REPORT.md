# Retrieval-channel ablation study

Baseline weights: `{"tfidf_word": 0.2, "tfidf_char": 0.45, "bm25": 0.25, "lsa": 0.05, "embed": 0.05}`. Each row zeroes one channel and re-runs the 50 eval queries. **ΔP@1** is the absolute drop relative to the baseline.

| Variant | P@1 | ΔP@1 | MRR | ΔMRR | Recall@5 |
|---|---:|---:|---:|---:|---:|
| baseline (all channels) | 0.960 | +0.000 | 0.980 | +0.000 | 1.000 |
|  baseline − tfidf_word | 0.960 | +0.000 | 0.980 | +0.000 | 1.000 |
|  baseline − tfidf_char | 0.940 | -0.020 | 0.970 | -0.010 | 1.000 |
|  baseline − bm25 | 0.980 | +0.020 | 0.990 | +0.010 | 1.000 |
|  baseline − lsa | 0.960 | +0.000 | 0.980 | +0.000 | 1.000 |
|  baseline − embed | 0.960 | +0.000 | 0.980 | +0.000 | 1.000 |
|  tfidf_word only | 0.940 | -0.020 | 0.970 | -0.010 | 1.000 |
|  tfidf_char only | 0.980 | +0.020 | 0.990 | +0.010 | 1.000 |
|  bm25 only | 0.940 | -0.020 | 0.970 | -0.010 | 1.000 |
|  lsa only | 0.860 | -0.100 | 0.922 | -0.058 | 1.000 |
|  embed only | 0.800 | -0.160 | 0.869 | -0.111 | 0.980 |

## Interpretation

- Removing **tfidf_char** causes the largest drop (P@1 → 0.940, a fall of 0.020), confirming that channel is the most informative.
- The strongest **single channel in isolation** is **tfidf_char** (P@1 = 0.980).
- The weakest single channel is **embed** (P@1 = 0.800); on this corpus it is useful only as part of the ensemble.