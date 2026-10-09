#!/usr/bin/env python3
"""Agreement of the two manual annotations of the bacteriophage entry: annotation A (study authors) and annotation B (curator), scored against each other
with the scorer of the study (28_score_extraction.py in this folder). Writes nothing; prints precision, recall and F1 in both directions and compares them with
datasets/manual_annotations/agreement_A_vs_B.csv.
    python3 scripts/score_agreement.py          (needs numpy, scipy, openpyxl)
Direction: 'scored' is used like an AI answer, 'reference' like the manual annotation of an entry; precision and recall swap with the direction, F1 does not."""
import csv
import importlib.util
import sys
from pathlib import Path

SECTION = Path(__file__).resolve().parents[1]
sys.argv = [sys.argv[0], "phage"]                                                  # the scorer reads the entry name from argv at import time
spec = importlib.util.spec_from_file_location("scorer", SECTION / "scripts/28_score_extraction.py")
scorer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer)

A = SECTION / "datasets/manual_annotations/phage_manual_annotation_A_authors.xlsx"
B = SECTION / "datasets/manual_annotations/phage_manual_annotation_B_curator.xlsx"
facts = {x: scorer.facts(x) for x in (A, B)}
records = {x: scorer.records(x) for x in (A, B)}
expected = {(r["annotation_scored"], r["annotation_used_as_reference"]): r for r in csv.DictReader(open(SECTION / "datasets/manual_annotations/agreement_A_vs_B.csv")) if r["case"] == "phage"}
bad = 0
for name, scored, reference in (("manual annotation A", A, B), ("manual annotation B", B, A)):
    ref_name = "manual annotation B" if reference is B else "manual annotation A"
    r = scorer.full_score(scored, reference, facts[reference], records[reference])["record"]["all"]
    row = expected[(name, ref_name)]
    same = all(abs(r[k] - float(row[k])) < 5e-5 for k in ("precision", "recall", "f1"))
    bad += not same
    print(f"{name} scored against {ref_name}: precision {r['precision']:.4f} recall {r['recall']:.4f} F1 {r['f1']:.4f}   (csv: {row['precision']} {row['recall']} {row['f1']}) {'OK' if same else 'DIFFERENT'}")
sys.exit(1 if bad else 0)
