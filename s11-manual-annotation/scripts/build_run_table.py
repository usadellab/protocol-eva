#!/opt/homebrew/bin/python3.13
"""One row per scored run (annotation B, five entries, text-only conditions, ALL prompts) -> results/runs.csv, and one row per entry with input/annotation size -> results/entries.csv.
Run table columns: case, model, prompt, rep, ok, precision, recall, f1, tp, cells_ai, cells_human, rows_ai, rows_human, rows_aligned, steps_written (protocols in the answer), tables_human (process tables of the annotation), input_words.
The scores are read from scores.json (written by scripts/28_score_extraction.py), the step counts from each run's llm.json."""
import csv, importlib.util, json, re, sys, glob
from pathlib import Path
import openpyxl
ROOT = Path(__file__).resolve().parents[1]                  # root of the section; the run folders (work/eval*/) are not part of it
OUT = ROOT / "results"
CASES = ["sdy1", "phage", "ux511", "biolector034", "pux782", "sdy1_pdfinput"]
REF = {"sdy1": "*SDY1*", "phage": "*bacteriophage*", "ux511": "*UX511*", "biolector034": "*BioLector*", "pux782": "*pUX782*", "sdy1_pdfinput": "*SDY1*"}
spec = importlib.util.spec_from_file_location("s", ROOT / "scripts/28_score_extraction.py")
def load(case):
    sys.argv = ["x", case if case in ("sdy1", "phage", "ux511", "biolector034", "pux782") else "sdy1_pdfinput"]
    S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S); return S
rows = []
for case in CASES:
    S = load(case)
    scores = json.loads((ROOT / S.CASES[case]["eval"] / "scores.json").read_text()) if case in S.CASES else {}
    for label, run in S.discover(case).items():
        if re.search(r", \+ ", label): continue                      # caption / image conditions are not part of this analysis
        v = scores.get(f"{label} | vs manual annotation B")
        if not v: continue
        r = v["record"]["all"]; ok = v.get("status", "ok") == "ok"
        steps = None
        try:
            j = json.loads((run["dir"] / "llm.json").read_text()); steps = len(j["llmData"]["protocols"]) if j.get("llmData") else None
        except Exception: pass
        rows.append({"case": case, "model": run["model"], "prompt": run["prompt"], "rep": run["rep"], "ok": int(ok), "precision": r["precision"], "recall": r["recall"], "f1": r["f1"], "tp": r["tp"], "cells_ai": r["predicted"], "cells_human": r["annotation"],
                     "rows_ai": r.get("records_predicted"), "rows_human": r.get("records_annotation"), "rows_aligned": r.get("records_aligned"), "steps_written": steps})
def tables_human(case):
    f = glob.glob(str(ROOT / "curator/2026-10-01_delivery" / (REF[case] + "assay.xlsx")))[0]
    wb = openpyxl.load_workbook(f, read_only=True)
    return sum(1 for s in wb.sheetnames if s != "isa_assay" and len(list(wb[s].iter_rows(max_row=2))) > 1)
IN = {"sdy1": "work/eval_sdy1/input", "phage": "work/eval_phage/input", "ux511": "work/eval_ux511/input", "biolector034": "work/eval_biolector034/input", "pux782": "work/eval_pux782/input", "sdy1_pdfinput": "work/eval_sdy1_pdfinput/input"}
ent = []
for case in CASES:
    md = next((ROOT / IN[case]).glob("*.md"), None)
    t = md.read_text() if md else ""
    annotation = next((r["cells_human"] for r in rows if r["case"] == case), None); recs = next((r["rows_human"] for r in rows if r["case"] == case), None)
    ent.append({"case": case, "input_words": len(t.split()), "input_chars": len(t), "table_cells_in_input": len(re.findall(r"<td", t)), "numbers_in_input": len(re.findall(r"\d+(?:[.,]\d+)?", t)), "cells_human": annotation, "rows_human": recs, "tables_human": tables_human(case)})
for r in rows: r["tables_human"] = next(e["tables_human"] for e in ent if e["case"] == r["case"]); r["input_words"] = next(e["input_words"] for e in ent if e["case"] == r["case"])
for name, data in (("runs.csv", rows), ("entries.csv", ent)):
    with open(OUT / name, "w", newline="") as fh: w = csv.DictWriter(fh, fieldnames=list(data[0])); w.writeheader(); w.writerows(data)
print(len(rows), "runs;"); [print(e) for e in ent]
