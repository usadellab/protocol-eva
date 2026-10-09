#!/usr/bin/env python3
"""Recompute the numeric statements of the text of Supplement S11 from results/all_configurations.csv (mean F1 per entry of every model x prompt x input configuration; standard library only):
  (1) "version 6 scored highest on average": per prompt version, the mean change of F1 against prompt version 6 of the same model on the same entries;
  (2) "adding figure descriptions or the images did not improve the scores" and "(prompts that requested verbatim evidence quotes) neither improved the average scores":
      the mean change of F1 by figure additions against the same model and prompt without figures, and by the evidence prompts (v7 to v10) against prompt version 6 of the same model;
  (3) "more than 10 prompt versions, all published": the prompt files of benchmarking_versions/prompts/.
    python3 scripts/recompute_statements.py        -> prints the numbers and writes results/statements.csv; checks them against results/delta_vs_baseline.csv"""
import csv
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

SECTION = Path(__file__).resolve().parents[1]
CASES = ["phage", "sdy1", "ux511", "biolector034", "pux782"]
ALIAS = {"Gemma-4-31B (local)": "Gemma-4-31B (local LM Studio)"}                # model string of the figure-addition runs
V6 = "general prompt v6"

configs = {}
for r in csv.DictReader(open(SECTION / "results/all_configurations.csv")):
    configs[(r["model"], r["prompt"], r["input"])] = {c: float(r[f"f1_{c}"]) for c in CASES if r[f"f1_{c}"] != ""}


def change(key):
    """(kind, baseline key) of a configuration, or None for the baseline itself."""
    model, prompt, inp = key
    if inp != "text only":
        return "figure addition", (ALIAS.get(model, model), prompt, "text only")
    if prompt == V6:
        return None
    return ("evidence prompt" if prompt.startswith("evidence prompt") else "other prompt version"), (model, V6, "text only")


rows = []
for key, f1 in configs.items():
    c = change(key)
    if c is None or c[1] not in configs:
        continue
    kind, base = c
    common = [e for e in CASES if e in f1 and e in configs[base]]
    if common:
        rows.append({"kind": kind, "model": key[0], "prompt": key[1], "input": key[2], "entries": len(common),
                     "delta": st.mean(f1[e] for e in common) - st.mean(configs[base][e] for e in common)})

version = lambda prompt: (re.search(r"prompt (v[\d.]+)", prompt) or re.match(r"(deployed) prompt", prompt)).group(1)
out = []


def line(statement, group, rs):
    d = [r["delta"] for r in rs]
    out.append({"statement": statement, "group": group, "configurations": len(d), "mean_change_f1": f"{st.mean(d):+.4f}", "lower": sum(x < 0 for x in d), "higher": sum(x > 0 for x in d)})
    print(f"{statement:46s} {group:44s} n={len(d):3d}  mean change of F1 {st.mean(d):+.4f}  lower {sum(x < 0 for x in d):2d}  higher {sum(x > 0 for x in d):2d}")


text = [r for r in rows if r["kind"] != "figure addition"]
line("(1) version 6 scored highest on average", "all other prompt versions, same model and entries", text)
by_version = defaultdict(list)
for r in text:
    by_version[version(r["prompt"])].append(r)
for v, rs in sorted(by_version.items(), key=lambda x: [float(y) for y in re.findall(r"\d+(?:\.\d+)?", x[0])] or [0]):
    line("(1) version 6 scored highest on average", f"prompt version {v}", rs)
line("(2) neither improved the average scores", "figure additions (descriptions or images)", [r for r in rows if r["kind"] == "figure addition"])
line("(2) neither improved the average scores", "evidence prompts (traceable extraction)", [r for r in rows if r["kind"] == "evidence prompt"])
n_prompts = len(list((SECTION / "benchmarking_versions/prompts").glob("prompt_*.txt"))) - 1               # without prompt_v6_as_sent.txt
out.append({"statement": "(3) more than 10 prompt versions, all published", "group": "prompt files in benchmarking_versions/prompts/", "configurations": n_prompts, "mean_change_f1": "", "lower": "", "higher": ""})
print(f"(3) more than 10 prompt versions, all published: {n_prompts} prompt files in benchmarking_versions/prompts/")
with open(SECTION / "results/statements.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)

bad = 0                                                                                                      # the same changes as in results/delta_vs_baseline.csv (computed there from unrounded scores; here from the 4-decimal means)
stored = {(r["model"], r["prompt"], r["input"]): float(r["delta_f1"]) for r in csv.DictReader(open(SECTION / "results/delta_vs_baseline.csv"))}
mine = {(r["model"], r["prompt"], r["input"]): r["delta"] for r in rows}
if set(stored) != set(mine) or any(abs(stored[k] - mine[k]) > 5e-4 for k in stored):
    bad = 1
print(f"{len(mine)} changes compared with results/delta_vs_baseline.csv: {'DIFFERENT' if bad else 'identical within 5e-4 (rounding of the means)'}")
sys.exit(bad)
