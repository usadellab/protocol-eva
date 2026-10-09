#!/usr/bin/env python3
"""Recompute Table S11-2 (prompt version 6, text-only, per entry F1 mean ± sd (n), precision / recall, row means) from the per-run scores in results/runs.csv
and compare every printed cell with results/v6/table_S11-2.csv. Standard library only.
    python3 scripts/recompute_table_s11_2.py
A failed run (ok = 0) scores 0 for precision, recall and F1 (already 0 in runs.csv); a row is recomputed for every model label of results/v6/model_label_map.csv (the models of the table)."""
import csv
import statistics as st
import sys
from pathlib import Path

SECTION = Path(__file__).resolve().parents[1]
CASES = ["phage", "sdy1", "ux511", "biolector034", "pux782"]
PROMPT = "general prompt v6"

labels = {r["model_label_in_csv_files"]: r for r in csv.DictReader(open(SECTION / "results/v6/model_label_map.csv"))}
runs = {}                                                                         # model label -> case -> [(precision, recall, f1, failed)]
for r in csv.DictReader(open(SECTION / "results/runs.csv")):
    if r["prompt"] == PROMPT and r["case"] in CASES:
        runs.setdefault(r["model"], {}).setdefault(r["case"], []).append((float(r["precision"]), float(r["recall"]), float(r["f1"]), r["ok"] != "1"))

computed = {}
for model, by_case in runs.items():
    info = labels.get(model)
    if not info:
        continue
    cells, p_means, r_means, f1_means, n_runs, n_failed = [], [], [], [], 0, 0
    for c in CASES:
        rs = by_case[c]
        f1 = [x[2] for x in rs]
        sd = f"{st.mean(f1):.2f}" if len(f1) == 1 else f"{st.mean(f1):.2f} ± {st.stdev(f1):.2f}"
        failed = sum(x[3] for x in rs)
        cells.append(f"{sd} ({len(rs)}){'*' if failed else ''} / {st.mean(x[0] for x in rs):.2f} / {st.mean(x[1] for x in rs):.2f}")
        p_means.append(st.mean(x[0] for x in rs)); r_means.append(st.mean(x[1] for x in rs)); f1_means.append(st.mean(f1)); n_runs += len(rs); n_failed += failed
    computed[(info["row_in_table_S11-2"], info["route"])] = [*cells, f"{st.mean(f1_means):.2f}", f"{st.mean(p_means):.2f}", f"{st.mean(r_means):.2f}", str(len(CASES)), str(n_runs), str(n_failed)]

printed = list(csv.reader(open(SECTION / "results/v6/table_S11-2.csv")))
header, rows = printed[0], printed[1:]
bad = 0
for row in rows:
    got = computed.get((row[0], row[1]))
    if got is None:
        print("not recomputed:", row[0], row[1]); bad += 1; continue
    for h, a, b in zip(header[2:], row[2:], got):
        if a != b:
            print(f"DIFFERENT {row[0]} / {row[1]} / {h}: printed {a!r}, recomputed {b!r}"); bad += 1
print(f"{len(rows)} rows x {len(header) - 2} value columns compared; {bad} differences")
sys.exit(1 if bad else 0)
