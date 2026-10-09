# Traceable extraction

Prompts v7 to v10 ask the model for the verbatim passage of the entry that each value was read from (`evidence`). `scripts/32_resolve_evidence.js` locates every passage in the entry text (classes: exact, fuzzy, value not in quote, unresolved, missing). The **traceable share** is the share of predicted cells whose quote was located and contains the value; it says that the quote exists in the text, not that the value is correct.
`scripts/31_annotation_evidence.py` locates the cells of the manual annotation in the text; the **grounding F1** scores how well the quotes of an answer cover the annotation cells that can be located. `34_evidence_feedback.py <run-dir> [--annotation]` reads the evidence file of one run and writes `<run-dir>/feedback.json` and `<run-dir>/feedback.md` without an LLM: a class for every cell that is not exact or fuzzy (missing, table paraphrase, not in source, number changed, derived label), the coverage of the numeric tokens of the entry by the quotes (per section and overall), structure heuristics, and with `--annotation` the annotation cells whose source place no quote overlaps; `--control` runs its controls (they need run folders of the study). `35_prompt_feedback.py` turns these classes into feedback for prompt proposals (its own `--control` also needs run folders).

## Result
29 configurations have a baseline on at least one common entry (common entries per configuration: 1 to 5); mean F1 over the common entries is lower than the baseline in 24, higher in 5. Per model (change of mean F1 against prompt version 6 on the same entries):

| model | configurations | common entries | lowest change | highest change |
|---|---|---|---|---|
| Claude Opus | 3 | 5–5 | −0.169 (v9) | −0.078 (v7.5) |
| Claude Sonnet 5.5 | 3 | 5–5 | −0.118 (v9.1) | −0.004 (v10) |
| DeepSeek-V4.1-Flash | 1 | 4–4 | +0.113 (v7) | +0.113 (v7) |
| GLM-4.7-Flash (local LM Studio) | 3 | 2–4 | −0.073 (v7.5) | +0.025 (v7.1) |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | 10 | 5–5 | −0.070 (v7.1) | −0.029 (v10) |
| Gemma-4-31B (local LM Studio) | 5 | 3–5 | −0.056 (v7.1) | +0.018 (v9) |
| Kimi-K3 (Kimi Code) | 3 | 1–5 | −0.058 (v9) | +0.215 (v7.1) |
| MiniMax-M3-4bit (local oMLX) | 1 | 4–4 | −0.137 (v7) | −0.137 (v7) |

Traceable share over the 29 configurations with evidence: 0.643 to 0.999 (median 0.898); over the 19 configurations with five entries 0.813 to 0.999. Grounding F1: 0.186 to 0.664 over 29 configurations.
Evidence prompts are not part of the supplement. Scores of every configuration: `evidence_prompts_text_only.csv` (columns `traceable_share_mean`, `grounding_f1_mean`, `entries`).

| Model | Prompt | Entries | Runs | Failed | Mean F1 | Δ F1 vs v6 | Traceable share | Grounding F1 |
|---|---|---|---|---|---|---|---|---|
| Claude Opus | evidence prompt v10 | 5 | 5 | 0 | 0.511 | −0.080 | 0.974 | 0.554 |
| Claude Opus | evidence prompt v7.5 | 5 | 5 | 0 | 0.512 | −0.078 | 0.965 | 0.540 |
| Claude Opus | evidence prompt v9 | 5 | 5 | 0 | 0.421 | −0.169 | 0.939 | 0.481 |
| Claude Sonnet 5.5 | evidence prompt v10 | 5 | 5 | 0 | 0.414 | −0.004 | 0.846 | 0.457 |
| Claude Sonnet 5.5 | evidence prompt v9 | 5 | 5 | 0 | 0.397 | −0.022 | 0.972 | 0.458 |
| Claude Sonnet 5.5 | evidence prompt v9.1 | 5 | 5 | 1 | 0.301 | −0.118 | 0.999 | 0.514 |
| DeepSeek-V4.1-Flash | evidence prompt v7 | 4 | 6 | 0 | 0.385 | +0.113 | 0.930 | 0.506 |
| GLM-4.7-Flash (local LM Studio) | evidence prompt v7 | 4 | 6 | 0 | 0.218 | −0.028 | 0.643 | 0.186 |
| GLM-4.7-Flash (local LM Studio) | evidence prompt v7.1 | 4 | 12 | 1 | 0.272 | +0.025 | 0.824 | 0.299 |
| GLM-4.7-Flash (local LM Studio) | evidence prompt v7.5 | 2 | 6 | 0 | 0.249 | −0.073 | 0.782 | 0.280 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v10 | 5 | 15 | 0 | 0.300 | −0.029 | 0.884 | 0.372 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v7 | 5 | 15 | 0 | 0.276 | −0.054 | 0.929 | 0.333 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v7.1 | 5 | 15 | 1 | 0.259 | −0.070 | 0.834 | 0.303 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v7.4 | 5 | 15 | 0 | 0.299 | −0.030 | 0.833 | 0.365 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v7.5 | 5 | 15 | 0 | 0.273 | −0.056 | 0.893 | 0.336 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v7.6 | 5 | 15 | 0 | 0.295 | −0.034 | 0.849 | 0.358 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v7.7 | 5 | 15 | 0 | 0.286 | −0.043 | 0.954 | 0.367 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v8 | 5 | 15 | 0 | 0.270 | −0.059 | 0.939 | 0.341 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v9 | 5 | 15 | 0 | 0.295 | −0.034 | 0.952 | 0.375 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v9.1 | 5 | 15 | 0 | 0.276 | −0.053 | 0.875 | 0.348 |
| Gemma-4-31B (local LM Studio) | evidence prompt v7 | 4 | 8 | 0 | 0.312 | −0.054 | 0.770 | 0.341 |
| Gemma-4-31B (local LM Studio) | evidence prompt v7.1 | 4 | 12 | 1 | 0.310 | −0.056 | 0.915 | 0.366 |
| Gemma-4-31B (local LM Studio) | evidence prompt v7.4 | 4 | 12 | 0 | 0.321 | −0.046 | 0.878 | 0.356 |
| Gemma-4-31B (local LM Studio) | evidence prompt v7.5 | 5 | 15 | 1 | 0.290 | −0.044 | 0.813 | 0.331 |
| Gemma-4-31B (local LM Studio) | evidence prompt v9 | 3 | 9 | 0 | 0.229 | +0.018 | 0.982 | 0.324 |
| Kimi-K3 (Kimi Code) | evidence prompt v7.1 | 1 | 3 | 1 | 0.256 | +0.215 | 0.987 | 0.539 |
| Kimi-K3 (Kimi Code) | evidence prompt v7.5 | 5 | 5 | 1 | 0.397 | +0.155 | 0.960 | 0.569 |
| Kimi-K3 (Kimi Code) | evidence prompt v9 | 5 | 5 | 3 | 0.185 | −0.058 | 0.898 | 0.664 |
| MiniMax-M3-4bit (local oMLX) | evidence prompt v7 | 4 | 4 | 2 | 0.152 | −0.137 | 0.776 | 0.345 |
