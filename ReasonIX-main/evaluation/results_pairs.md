# Pair-judge evaluation

45 hand-labeled claim pairs (15 contradiction, 15 agreement, 15 neutral). Metrics are macro-averaged over the 3 classes.

| Judge | Accuracy | Macro-F1 | Contradiction F1 | Agreement F1 | Neutral F1 | s / pair | No answer |
|---|---|---|---|---|---|---|---|
| Majority-class baseline | 33.3% | 0.167 | 0.00 | 0.50 | 0.00 | 0.00 | 0 |
| openai/gpt-oss-20b | 97.8% | 0.978 | 1.00 | 0.97 | 0.97 | 0.18 | 0 |
| openai/gpt-oss-120b | 100.0% | 1.000 | 1.00 | 1.00 | 1.00 | 0.13 | 0 |
| NLI cross-encoder/nli-deberta-v3-base | 93.3% | 0.933 | 0.91 | 1.00 | 0.89 | 5.59 | 0 |

## Confusion matrices (rows = true label, columns = predicted)

**openai/gpt-oss-20b**

| true \ pred | contradiction | agreement | neutral |
|---|---|---|---|
| contradiction | 15 | 0 | 0 |
| agreement | 0 | 15 | 0 |
| neutral | 0 | 1 | 14 |

**openai/gpt-oss-120b**

| true \ pred | contradiction | agreement | neutral |
|---|---|---|---|
| contradiction | 15 | 0 | 0 |
| agreement | 0 | 15 | 0 |
| neutral | 0 | 0 | 15 |

**NLI cross-encoder/nli-deberta-v3-base**

| true \ pred | contradiction | agreement | neutral |
|---|---|---|---|
| contradiction | 15 | 0 | 0 |
| agreement | 0 | 15 | 0 |
| neutral | 3 | 0 | 12 |
