# Reproducing the numbers of the supplement (S11)

Python 3.13. Everything below runs inside this folder; nothing needs the network or an API key unless it says so.

## 1. Table S11-2 (per-entry F1, precision, recall of prompt version 6)
```
python3.13 scripts/recompute_table_s11_2.py      # standard library only
python3.13 scripts/check_table_s11_2.py          # README table against the table in docs/Supplement_S11_manual_annotation_comparison.docx
```
`recompute_table_s11_2.py` reads `results/runs.csv` (one row per scored run, data snapshot 2026-10-08 12:05), keeps `general prompt v6` on the five entries, averages the repeats of each cell, and compares every printed cell of `results/v6/table_S11-2.csv` with the recomputed text. A failed run counts 0. The rows shown are marked in `results/v6/model_label_map.csv`. Table S11-1: `results/v6/sampling_parameters.json`.

## 2. The statements of the text
```
python3.13 scripts/recompute_statements.py      # standard library only -> results/statements.csv
```
Recomputes from `results/all_configurations.csv` (mean F1 per entry of every model x prompt x input configuration): (1) per prompt version, the mean change of F1 against prompt version 6 of the same model on the same entries ("version 6 scored highest on average"), (2) the mean change by figure additions and by the traceable (evidence-quote) prompts against the matching text-only run ("neither improved the average scores"), (3) the number of prompt versions (`benchmarking_versions/prompts/`). It checks its numbers against `results/delta_vs_baseline.csv`. `scripts/build_run_table.py` writes `results/runs.csv` and `results/entries.csv` from the run folders of the study and is not runnable here.

## 3. Agreement of the two manual annotations
```
python3.13 scripts/score_agreement.py          # numpy, scipy, openpyxl
```
scores annotation A of the bacteriophage entry against annotation B and the reverse with the scorer of the study and compares with `datasets/manual_annotations/agreement_A_vs_B.csv`.

## 4. What is not reproducible offline
* The scores of single runs from the run folders (`llm.json`, assay spreadsheet): the run folders (546 runs) are not part of the repository. `results/runs.csv` holds the scores of 431 of them (410 text-only runs of the five entries plus 21 runs of the spot assay with PDF-derived text; the 115 figure-addition runs are only in `results/all_configurations.csv` and `image_addition/`); `scripts/28_score_extraction.py` and `scripts/verify_scores.py` document how the scores were computed and need the run folders.
* The runs themselves: they need the model endpoints (Claude and Kimi Code subscriptions, hosted APIs, OpenRouter, a GPU cluster, local models) and an API key where applicable; model answers are not deterministic.
* The images of the figures are not in this section; `image_addition/captions/` holds the generated descriptions.
