# s11-manual-annotation: elab2arc extraction benchmarked against manual annotations

How well can a large language model convert an eLabFTW protocol entry into an ISA assay table with the elab2arc extraction prompt? This section of protocol-eva complements the automatic benchmark on protocols.io protocols (`../datasets`, `../results`) with a benchmark against **manual annotations** of five real eLabFTW entries. It holds the material behind Supplement S11 of the elab2arc publication (`docs/Supplement_S11_manual_annotation_comparison.docx`) and the experiments that are not part of the supplement. All numbers come from the data snapshot 2026-10-08 12:05.

## Check the supplement in five minutes
| Item of the supplement | Where | Command |
|---|---|---|
| Table S11-2 (scores per entry and model) | table below, `results/v6/table_S11-2.csv`, per-run scores `results/runs.csv` | `python3.13 scripts/recompute_table_s11_2.py`, `python3.13 scripts/check_table_s11_2.py` |
| Table S11-1 (access route, sampling) | `results/v6/sampling_parameters.json`, `results/v6/params/`, `results/v6/model_label_map.csv` | |
| Statements of the text (prompt versions, figures, traceable prompts) | `results/statements.csv`, `benchmarking_versions/`, `traceable/`, `image_addition/` | `python3.13 scripts/recompute_statements.py` |
| Second manual annotation, agreement of A and B | `datasets/manual_annotations/agreement_A_vs_B.csv` | `python3.13 scripts/score_agreement.py` |
| Prompt version 6 as the model receives it | `benchmarking_versions/prompts/prompt_v6_as_sent.txt` | |
| What cannot be reproduced offline | `docs/REPRODUCE.md` | |

## Layout
| Folder | Content |
|---|---|
| `docs/` | The supplement (docx and pdf), `docs/METHODS.md`, `docs/REPRODUCE.md` |
| `results/` | `runs.csv` (one row per scored run of the models of Table S11-2, 431 runs of all prompts), `entries.csv` (size of the manual annotations), `statements.csv`; `v6/`: Table S11-2 as csv, scores of prompt version 6 per row of the table, label map, sampling parameters; `all_configurations.csv`: every model × prompt × input; `delta_vs_baseline.csv`: change of mean F1 against the baseline configuration on the same entries |
| `benchmarking_versions/` | All prompt versions (`prompts/`), their scores, the Kimi-assisted prompt-writing workflow |
| `traceable/` | Prompts that ask for a verbatim evidence quote per value, the quote-location code, the scores |
| `image_addition/` | Figure descriptions or images added to the prompt: code, descriptions, scores |
| `scripts/` | Extraction harness, scorer and verifier, CLI and cluster routes (script numbers are those of the study's script folder, so they have gaps) |
| `datasets/` | The five entries as the application converts them (`protocol_inputs/`) and the manual annotations (`manual_annotations/`), de-identified |

## Terms
* **Manual annotation**: the assay table (ISA assay spreadsheet) that a person wrote for an entry. **B**: made independently by a DataPLANT curator for all five entries; the reference of every score. **A**: made by the study authors, who also wrote the extraction prompt.
* **Row** (record): a row of any table of the assay. **Cell**: one non-empty value cell (columns Characteristic, Parameter, Factor, Comment, Date); a value and its unit count once. **Cell human**: number of cells in annotation B of an entry; **cell AI**: number of cells in the answer of a model.
* **Precision, recall, F1** are record-level and counted in cells: rows are paired one-to-one across all tables, the cells of each pair are compared after normalising their format; all cells of an unpaired row are errors. A **failed run** (invalid or truncated JSON, no usable answer) scores 0; an **endpoint error** (rate limit, quota, server down) is not a model failure and was repeated. Details: `docs/METHODS.md`.

## Entries and manual annotations
Five entries: Bacteriophage sequencing (cell human 266), Spot assay (cell human 934), Strain generation (cell human 2631), BioLector cultivation (cell human 634), Plasmid generation (cell human 1085). Annotation B exists for all five. Annotation A exists for **one of the five entries** (bacteriophage sequencing, in `datasets/manual_annotations/`). Agreement of A and B (`datasets/manual_annotations/agreement_A_vs_B.csv`; F1 does not depend on the direction, precision and recall swap):

| Entry | Scored (as an answer) | Used as reference | Precision | Recall | F1 |
|---|---|---|---|---|---|
| Bacteriophage sequencing | manual annotation A | manual annotation B | 0.476 | 0.759 | 0.586 |
| Bacteriophage sequencing | manual annotation B | manual annotation A | 0.759 | 0.476 | 0.586 |

On the bacteriophage entry, 5 of the 10 rows of Table S11-2 have a mean F1 of 0.5855 (the agreement of A and B) or more; the highest is Gemma-4-31B (Mac, LM Studio, GGUF Q4_K_M, 0.629). The reference of the scores is one annotation, B, and the agreement of A and B is the only estimate of how much two annotations of the same entry differ.

## Prompt version 6 on all models (Table S11-2)
Identical to Table S11-2 of `docs/Supplement_S11_manual_annotation_comparison.docx` (checked cell by cell by `scripts/check_table_s11_2.py`). First line of each cell: F1 as mean ± sd over the n runs in brackets (no sd for a single run); * marks a mean that includes a failed run, scored as 0. Second line: mean precision / mean recall, failed runs as 0. Mean F1, P and R are the means of the five entry values. Rows are sorted by mean F1.

<!-- table-s11-2 -->
| Model | Route | Bacteriophage sequencing | Spot assay | Strain generation | BioLector cultivation | Plasmid generation | Mean F1 | Mean P | Mean R | Entries | Runs | Failed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Claude Opus 5.5 | Claude CLI, print mode | 0.61 (1)<br>0.53 / 0.71 | 0.72 (1)<br>0.71 / 0.73 | 0.49 (1)<br>0.74 / 0.37 | 0.48 (1)<br>0.47 / 0.50 | 0.65 (1)<br>0.75 / 0.57 | 0.59 | 0.64 | 0.58 | 5 | 5 | 0 |
| Claude Sonnet 5.5 | Claude CLI, print mode | 0.58 ± 0.01 (3)<br>0.51 / 0.67 | 0.42 ± 0.13 (3)<br>0.58 / 0.34 | 0.50 ± 0.03 (3)<br>0.78 / 0.37 | 0.23 ± 0.03 (3)<br>0.17 / 0.36 | 0.37 ± 0.01 (3)<br>0.63 / 0.26 | 0.42 | 0.53 | 0.40 | 5 | 15 | 0 |
| dots-3-note-preview | OpenRouter free tier | 0.62 (1)<br>0.63 / 0.60 | 0.33 (1)<br>0.31 / 0.35 | 0.25 (1)<br>0.41 / 0.18 | 0.22 (1)<br>0.17 / 0.29 | 0.45 (1)<br>0.54 / 0.38 | 0.37 | 0.41 | 0.36 | 5 | 5 | 0 |
| Gemma-4-31B | Mac, LM Studio, GGUF Q4_K_M | 0.63 ± 0.07 (3)<br>0.74 / 0.55 | 0.41 ± 0.07 (3)<br>0.76 / 0.28 | 0.16 ± 0.02 (3)<br>0.71 / 0.09 | 0.27 ± 0.02 (3)<br>0.23 / 0.31 | 0.21 ± 0.04 (3)<br>0.72 / 0.12 | 0.33 | 0.64 | 0.27 | 5 | 15 | 0 |
| Gemma-4-31B | GPU cluster, vLLM, QAT w4a16 | 0.56 ± 0.08 (3)<br>0.78 / 0.43 | 0.36 ± 0.00 (3)<br>0.88 / 0.22 | 0.12 ± 0.05 (3)<br>0.72 / 0.06 | 0.43 ± 0.01 (3)<br>0.57 / 0.34 | 0.19 ± 0.07 (3)<br>0.66 / 0.11 | 0.33 | 0.72 | 0.24 | 5 | 15 | 0 |
| Nemotron-3-Ultra-550B | OpenRouter free tier | 0.41 (1)<br>0.37 / 0.45 | 0.47 (1)<br>0.50 / 0.44 | 0.31 (1)<br>0.66 / 0.20 | 0.00 (1)*<br>0.00 / 0.00 | 0.36 (1)<br>0.32 / 0.42 | 0.31 | 0.37 | 0.30 | 5 | 5 | 1 |
| MiniMax-M3-4bit | Mac, oMLX, 4-bit | 0.60 ± 0.05 (3)<br>0.51 / 0.75 | 0.36 ± 0.32 (3)*<br>0.37 / 0.35 | 0.12 ± 0.20 (3)*<br>0.17 / 0.09 | 0.08 ± 0.13 (3)*<br>0.06 / 0.12 | 0.35 ± 0.01 (3)<br>0.53 / 0.26 | 0.30 | 0.33 | 0.31 | 5 | 15 | 5 |
| DeepSeek-V4.1-Flash | hosted API | 0.53 ± 0.07 (3)<br>0.44 / 0.66 | 0.18 ± 0.13 (3)<br>0.39 / 0.14 | 0.12 ± 0.21 (3)*<br>0.23 / 0.08 | 0.25 ± 0.03 (3)<br>0.21 / 0.32 | 0.32 ± 0.00 (3)<br>0.50 / 0.24 | 0.28 | 0.36 | 0.29 | 5 | 15 | 2 |
| GLM-4.7-Flash | Mac, LM Studio, MLX 6-bit | 0.33 ± 0.03 (3)<br>0.41 / 0.28 | 0.09 ± 0.12 (3)*<br>0.28 / 0.06 | 0.25 ± 0.02 (3)<br>0.46 / 0.21 | 0.31 ± 0.05 (3)<br>0.39 / 0.26 | 0.32 ± 0.09 (3)<br>0.41 / 0.32 | 0.26 | 0.39 | 0.23 | 5 | 15 | 1 |
| Kimi-K3 | Kimi Code CLI (agent harness) | 0.60 ± 0.02 (3)<br>0.54 / 0.67 | 0.04 ± 0.07 (3)*<br>0.11 / 0.02 | 0.00 ± 0.00 (3)*<br>0.00 / 0.00 | 0.28 ± 0.08 (3)<br>0.25 / 0.34 | 0.30 ± 0.28 (3)*<br>0.41 / 0.24 | 0.24 | 0.26 | 0.26 | 5 | 15 | 6 |
<!-- /table-s11-2 -->

The section holds the runs of the models of this table only (`results/v6/model_label_map.csv`); the scores of prompt version 6 per row with the entries, runs and failed runs are in `results/v6/v6_scores_per_row.csv`. Routes and quantisations differ between rows, so comparisons across routes are approximate; 3 of the 10 rows are single runs on every entry and have no spread.

## Other experiments (details in the sub-folders; every number is computed from the csv files)
* `benchmarking_versions/`: prompt versions other than 6 against prompt version 6 of the same model on the same entries: 33 configurations have a baseline on at least one common entry (common entries per configuration: 1 to 5); mean F1 over the common entries is lower than the baseline in 26, higher in 7.
* `traceable/`: prompts v7 to v10 ask for an evidence quote per value. 29 configurations have a baseline on at least one common entry (common entries per configuration: 1 to 5); mean F1 over the common entries is lower than the baseline in 24, higher in 5. The traceable share (predicted cells whose quote was located in the entry text and contains the value) is between 0.643 and 0.999 over 29 configurations (0.813 to 0.999 over the 19 with five entries). The share does not say that a value is correct.
* `image_addition/`: figure descriptions written by a vision model, or the images themselves, added to the prompt. 11 configurations have a baseline on at least one common entry (common entries per configuration: 3 to 5); mean F1 over the common entries is lower than the baseline in 7, higher in 4. Real images were tested only with Gemma-4-31B (local), on 3 entries. On the spot assay entry the precision changed by -0.595 to +0.189 (lower in 10 of 11 configurations).

## Limits
* Five entries; the scores of an entry depend on the entry (text type, size of the annotation), and entry and size are confounded.
* All scores are against one person's annotation B. The only measure of annotation uncertainty is the agreement of A and B on one entry (F1 0.5855). A was made by the study authors, who also wrote the prompt.
* Rows are routes, not independent models: Gemma-4-31B appears twice (Mac, cluster) with the same weights. Quantisation, sampling and number of repeats differ between rows.
* Open-weight is an assumption for the free-tier OpenRouter rows (the served weights and quantisation are not known).

## Further material
A trend analysis of the same runs (figure, correlations, permutation tests) is kept on the branch `s11-trend-analysis` and is not part of Supplement S11.

## Reproducing
`docs/REPRODUCE.md`. The run folders of the study are not part of the repository; the scripts in `scripts/` document how the scores were produced.
