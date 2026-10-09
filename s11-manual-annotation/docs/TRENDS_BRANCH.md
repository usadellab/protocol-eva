# Branch s11-trend-analysis

This branch is the section `s11-manual-annotation` of the main branch plus **additional material that is not part of Supplement S11**: a trend analysis of the same runs and the full evidence-feedback script. Nothing on this branch is used by a statement or a table of the supplement; the numbers of the analysis may change when runs are added.

| Path | Content |
|---|---|
| `analysis/` | `analyze.py` (all tests -> `trends.json`), `make_figure.py` (-> `fig_trends.png`), `verify_trends.py` (second implementation of the headline statistics), `classify_failures.py` (cause of every failed v6 run -> `failures_v6.json`, needs the run folders of the study), `README.md` (what it is, how to run, the result table) |
| `traceable/scripts/34_evidence_feedback.py` | the full script: besides the resolution classes and the source coverage of a run it has `--validate`, which correlates the annotation-free signals (source coverage, share of values not in the quote) with recall and precision (Pearson, Spearman) as a validation of the signal. Main has the script without this part. |

The analysis reads `results/runs.csv` and `results/entries.csv` of the main section (the runs of the models of Table S11-2 only) and runs from inside `analysis/`. `--validate` and `classify_failures.py` need the run folders of the study, which are not part of the repository; the control (`python3.13 traceable/scripts/34_evidence_feedback.py --control`) needs them as well.
