#!/opt/homebrew/bin/python3.13
"""Score assay xlsx files (LLM conversions) against manual annotation assay xlsx files: precision, recall, F1,
plus a leaderboard with run cost. Design borrowed from ExtractBench (github.com/run-llama/ExtractBench): records
aligned one-to-one before cells are compared, failed runs score zero instead of being dropped, cost reported next
to accuracy, repeats averaged, entries weighted equally.

Naming differs between annotators (our `2025-12-01_WT_preculture` vs manual annotation B's `R01_WT_overnight` vs whatever
an LLM invents), and so does the table granularity (24 vs 7 protocol tables). So the score compares the
*information* in the tables, as facts, not the names:

  facts    every value cell of a Characteristic / Parameter / Factor / Comment / Date column, in the
           `samples` sheet and every process sheet, is ONE fact, compared as a whole cell (no digits counted
           separately). The annotation cells are the standard. TP = an API output cell that matches an annotation cell, FP = an
           API output cell that matches no annotation cell (an error), FN = an annotation cell no API output cell matches (missing).
           Normalised form of a cell ("as written"): tokens joined by spaces -
             - dates (dd.mm.yy, dd.mm.yyyy, dd/mm/yyyy, yyyy-mm-dd) -> ISO date, e.g. 2025-12-01
             - numbers -> canonical decimal (decimal comma -> point, trailing zeros dropped: 0,0400 -> 0.04)
             - words -> lower case; punctuation ignored ("LB + Amp" == "LB+Amp"), except a dash between two
               numbers, kept as "-" so a range "15-16" differs from a list "15, 16"
           Lint form (formatting only), when the cell carries a unit: durations "26h30min" / "68 hrs 44 mins" ->
           decimal hours; a number with a unit (inline, or the column's Unit cell when the cell is that one
           number) -> value in a base unit (volume l, time h, molar M, mass g, mass concentration g/l). So
           "6" mL == "6000" µl and "68 hrs 44 mins" == "4124" minute.
           Matching: a maximum one-to-one matching (Kuhn's algorithm, so TP does not depend on iteration order)
           over three compatibility rules: (1) same normalised cell - refused only when both cells carry lint forms
           that differ, i.e. the units prove different quantities ("5" µl vs "5" min); (2) same lint
           form; (3) leading quantity: two cells match when one of them holds a single quantity and
           it equals the other cell's first quantity (value and, if both have one, dimension), so
           "26h30min (450 loops)" == "26.5" hour. A range is one quantity ("15-16" never matches "15"). Each
           matched pair is one TP; the number of pass-3 matches is reported as "tp_leading". Quantities are
           compared in both forms (as written and lint form), so "62.5" == "62.5" µM.
           Simple lint cases handled everywhere: letter case, whitespace and punctuation ("LB + Amp" == "LB+Amp"),
           decimal comma and trailing zeros ("0,0400" == "0.04"), date formats, unit spelling via the lint form
           (µL/µl/ul/microliter, mL/ml/milliliter, h/hrs/hour, min/mins/minute), durations, and codes written in
           digit groups ("97 613 732" == "97613732").
           Hash cells (sha256) are skipped. STRICT=1 switches the lint form off. Input/Output names, Protocol
           REF/Uri and Term Source/Accession columns are ignored.
  modes    record    (headline) every row of every sheet is a record: the bag of its value cells, constants
                     included. Records are aligned one-to-one across ALL tables (table names and granularity
                     differ between annotators) by the Hungarian method, maximising the matched cells; within an
                     aligned pair, cells match by the rules above. TP = matched cells inside aligned pairs; the
                     cells of an unaligned record are all FP (predicted) or FN (annotation). A value on the wrong row
                     (a GA/GO label swap), a missing row or an invented row is an error here even when the same
                     value exists elsewhere in the column. Also reported: records aligned with at least one
                     matched cell, and unaligned predicted / annotation records (invented / dropped rows).
           distinct  the set of cells: which values were captured at all
           per-row   a column whose cells are all equal counts once; otherwise every row counts (multiset).
           column-distinct  each distinct cell of a column counts once (multiset over columns): per-culture
                     differences count, duplicated rows do not; blind to row assignment and row count.
  metrics  precision = TP / API output cells, recall = TP / annotation cells, F1 = 2PR / (P + R).
           Reported for cells with digits ("numbers"), cells without ("text") and both together.
           fp_in_source = unmatched predicted cells whose numbers/dates all occur in the source text
           (candidates for "correct, but this manual annotation does not record it"; a coincidental number is
           possible, so it is a count to inspect, not a correction of P).
  runs     every directory work/eval[_<case>]/<model>_<prompt>_r<n>/ is a run. A run with an LLM output file
           but no usable result (error, no protocols, unparsable JSON, no xlsx) is FAILED and scores 0 in every
           mode - it is kept, not dropped, so a model cannot gain by failing on the hard entries. A directory
           without llm.json is still running and is listed as incomplete. Run cost (calls, prompt/completion
           tokens, seconds, USD) is read from whatever the runner recorded: 26_llm_extraction.js (usage, else the
           usage chunk of the raw stream), claude -p (cli_output.json).

Controls (run every time, the script stops if one fails): each annotation scores 1.0 against itself in every mode; a
annotation with its second half of process sheets removed keeps precision 1.0 and loses recall; an annotation with two rows'
values swapped in one column keeps column-distinct at 1.0 and loses record F1; a failed run scores 0.

Usage: 28_score_extraction.py [phage|sdy1|biolector034|ux511|pux782|all]   (default all)
       -> work/eval[_<case>]/scores.md + scores.json per case; work/eval/leaderboard.csv + leaderboard.md (all cases)
"""
import csv
import functools
import json
import os
import re
import statistics
import sys
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import openpyxl
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parent.parent
CASES = {
    "phage": {"title": "BAS33 phage sequencing, eLabFTW 85318", "eval": ROOT / "work/eval_phage",
              "annotations": {"manual annotation A": ROOT / "output/EXP001_BAS33_bacteriophage_sequencing/isa.assay.xlsx",
                        "manual annotation B": ROOT / "curator/annotator/20260924_bacteriophage-sequencing_isa.assay.xlsx"}},
    "sdy1": {"title": "SDY1 phenotyping SSD1, eLabFTW 51585 (.eln input)", "eval": ROOT / "work/eval_sdy1",
             "annotations": {"manual annotation B": ROOT / "curator/example3/20260924_SDY1_phenotyping_SSD1_isa.assay.xlsx"}},
    # Archive: SDY1 with the old PDF-derived input (flattened text, Date/Status header) - runs kept, scored separately
    "sdy1_pdfinput": {"title": "SDY1 phenotyping SSD1, OLD input (PDF-derived text), archive", "eval": ROOT / "work/eval_sdy1_pdfinput",
                      "annotations": {"manual annotation B": ROOT / "curator/example3/20260924_SDY1_phenotyping_SSD1_isa.assay.xlsx"}},
    # Delivery 2026-10-01 (curator/2026-10-01_delivery): one annotation each, no second curator; input = the .eln HTML body
    "biolector034": {"title": "BioLector-034 Pima1 Malt/Glc, eLabFTW 73918", "eval": ROOT / "work/eval_biolector034",
                     "annotations": {"manual annotation B": ROOT / "curator/2026-10-01_delivery/20260928_BioLector-034_Pima1_Malt_Glc_isa.assay.xlsx"}},
    "ux511": {"title": "Generation of UX511-523, eLabFTW 72729", "eval": ROOT / "work/eval_ux511",
              "annotations": {"manual annotation B": ROOT / "curator/2026-10-01_delivery/20260930_Generation_of_UX511-523_isa.assay.xlsx"}},
    # No JSON/.eln export exists for this entry: the input is the body HTML copied from the rendered eLabFTW page + link URLs from the PDF annotations, through the app's turndown (INPUT_FORMAT.md). Not in the leaderboard.
    "pux782": {"title": "Generation of pUX782-787, eLabFTW 71968 - input from the RENDERED-PAGE HTML (no JSON/.eln export)", "eval": ROOT / "work/eval_pux782",
               "annotations": {"manual annotation B": ROOT / "curator/2026-10-01_delivery/20260928_Generation_of_pUX782-787_isa.assay.xlsx"}},
}
HEADLINE_ANNOTATION = "manual annotation B"  # the independent human standard; the only one that exists for every entry
MODELS = {"claude-opus": "Claude Opus", "kimicode-k3": "Kimi-K3 (Kimi Code)",
          "deepseek-v41": "DeepSeek-V4.1-Flash", "minimax-m3": "MiniMax-M3-4bit (local oMLX)",
          "glm47flash-lms": "GLM-4.7-Flash (local LM Studio)", "gemma4-31b-lms": "Gemma-4-31B (local LM Studio)",
          "kimicode-k3-capguided": "Kimi-K3 (Kimi Code), + guided image descriptions", "claude-opus-capgeneric": "Claude Opus, + generic image descriptions",
          "claude-opus-capguided": "Claude Opus, + guided image descriptions", "gemma4-31b-lms-imgint": "Gemma-4-31B (local), + images interleaved",
          "or-nemotron3ultra-capgeneric": "Nemotron-3-Ultra-550B (OpenRouter free), + generic image descriptions", "or-dots3-capgeneric": "dots-3-note-preview (OpenRouter free), + generic image descriptions",
          "kimicode-k3-capgeneric": "Kimi-K3 (Kimi Code), + generic image descriptions", "claude-opus-capbrief": "Claude Opus, + short descriptions (v8 captioner)",
          "kimicode-k3-capbrief": "Kimi-K3 (Kimi Code), + short descriptions (v8 captioner)", "gemma4-31b-lms-capbrief": "Gemma-4-31B (local), + short descriptions (v8 captioner)",
          "claude-sonnet55": "Claude Sonnet 5.5", "or-nemotron3ultra": "Nemotron-3-Ultra-550B (OpenRouter free)",
          "or-dots3": "dots-3-note-preview (OpenRouter free)", "gemma4-31b-vllm": "Gemma-4-31B (cluster vLLM, QAT w4a16)",
          "gemma4-31b-lms-capguided": "Gemma-4-31B (local), + guided image descriptions", "gemma4-31b-lms-capgeneric": "Gemma-4-31B (local), + generic image descriptions"}
PROMPTS = {"deployed": "deployed prompt", "v1": "per-row prompt v1", "v2": "general prompt v2",
           "v3": "general prompt v3", "v4": "general prompt v4", "v5": "general prompt v5", "v6": "general prompt v6",
           "v7": "evidence prompt v7", "v71": "evidence prompt v7.1 (table quoting)"}
PROMPTS.update({f"v7{i}": f"evidence prompt v7.{i} (Kimi-assisted candidate)" for i in range(2, 8)})
PROMPTS["v8"] = "evidence prompt v8 (Kimi: descriptions supplementary)"
PROMPTS["v9"] = "evidence prompt v9 (Kimi rewrite: plain steps, one example)"
PROMPTS["v91"] = "evidence prompt v9.1 (v9 + granularity fix)"
PROMPTS["v10"] = "evidence prompt v10 (Kimi: v6 rules + v9 wording)"


def discover(case):
    """-> {label: run dict} for every run of a case: dir, model, prompt, rep, xlsx, status, reason."""
    runs = {}
    for d in sorted(CASES[case]["eval"].glob("*_r[0-9]*")):
        if not d.is_dir():
            continue
        model, prompt, rep = d.name.rsplit("_", 2)
        label = f"{MODELS.get(model, model)}, {PROMPTS.get(prompt, prompt)}, {rep}"
        runs[label] = {"dir": d, "model": MODELS.get(model, model), "prompt": PROMPTS.get(prompt, prompt), "rep": rep}
    for run in runs.values():
        run["xlsx"] = run["dir"] / "isa.assay.xlsx"
        run["status"], run["reason"] = run_status(run["dir"])
    return runs


def llm_data(raw):
    """elab2arc llmData inside any runner's llm.json (26 / claude -p wrap it, 30 writes it bare)."""
    return raw.get("llmData", raw) if isinstance(raw, dict) and ("llmData" in raw or "protocols" in raw) else None


def is_api_error(text):
    """A response that is one JSON object with an "error" member and no choices: the endpoint refused the request (credit limit, overload)."""
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return False
    return isinstance(obj, dict) and "error" in obj and "choices" not in obj


def run_status(d):
    """-> (status, reason): ok | failed | incomplete."""
    f = d / "llm.json"
    if not f.exists():
        return ("ok", "") if (d / "isa.assay.xlsx").exists() else ("incomplete", "no llm.json yet")
    try:
        raw = json.loads(f.read_text())
    except json.JSONDecodeError as e:
        return "failed", f"llm.json unreadable: {e}"
    data = llm_data(raw)
    if not data or not data.get("protocols"):
        raws = [p.read_text() for p in sorted(d.glob("llm.raw*.txt"))]
        if raws and all(t.lstrip().lower().startswith(("<!doctype html", "<html")) for t in raws):
            return "failed", f"endpoint error: all {len(raws)} responses are HTML error pages, no model output (rerun)"
        if raws and all(is_api_error(t) for t in raws):
            return "failed", f"endpoint error: all {len(raws)} responses are API error objects (e.g. credit limit), no model output (rerun)"
        err = raw.get("error") if isinstance(raw, dict) else None
        return "failed", err or "no protocols in the LLM output (unparsable or empty answer)"
    if not (d / "isa.assay.xlsx").exists():
        return "failed", "no isa.assay.xlsx (27_llm_to_xlsx.js did not produce one)"
    return "ok", ""


def stream_usage(text):
    """Last usage object of an OpenAI-style SSE stream, or None."""
    for line in reversed(text.splitlines()):
        if line.startswith("data: {") and '"usage"' in line:
            usage = json.loads(line[6:]).get("usage")
            if usage:
                return usage
    return None


def run_meta(d):
    """Cost of one run: calls, prompt/completion tokens, seconds, USD (None where the runner recorded nothing)."""
    meta = {"calls": None, "prompt_tokens": None, "completion_tokens": None, "seconds": None, "cost_usd": None}
    f = d / "llm.json"
    raw = json.loads(f.read_text()) if f.exists() else {}
    if (d / "cli_output.json").exists():                         # claude -p
        cli = json.loads((d / "cli_output.json").read_text())   # a list of events, or (older runs) the result alone
        result = cli if isinstance(cli, dict) else next((x for x in cli if isinstance(x, dict) and x.get("type") == "result"), {})
        u = result.get("usage", {})
        meta.update({"calls": result.get("num_turns"), "seconds": raw.get("seconds"), "cost_usd": raw.get("cost_usd"),
                     "prompt_tokens": u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                     + u.get("cache_read_input_tokens", 0) if u else None,
                     "completion_tokens": u.get("output_tokens")})
    elif isinstance(raw, dict) and "requests" in raw:              # 26_llm_extraction.js
        usages = [u for u in raw.get("usage") or [] if u]
        if not usages:
            usages = [u for p in sorted(d.glob("llm.raw*.txt")) if (u := stream_usage(p.read_text()))]
        meta.update({"calls": raw.get("requests"), "seconds": raw.get("seconds")})
        if usages:
            meta["prompt_tokens"] = sum(u.get("prompt_tokens", 0) for u in usages)
            meta["completion_tokens"] = sum(u.get("completion_tokens", 0) for u in usages)
    return meta


def table_shape(xlsx):
    """-> (process/sample tables, data rows) of an assay xlsx."""
    wb = openpyxl.load_workbook(xlsx, read_only=True)
    sheets = [s for s in wb.sheetnames if s != "isa_assay"]
    return len(sheets), sum(max(0, (wb[s].max_row or 1) - 1) for s in sheets)


# Module-level single-case view, kept for the scripts that import this module with a case in argv[1]
# (scripts/verify_scores.py).
CASE = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in CASES else "phage"
EVAL = CASES[CASE]["eval"]
ANNOTATIONS = CASES[CASE]["annotations"]
PREDICTIONS = {label: r["xlsx"] for label, r in discover(CASE).items() if r["status"] == "ok"}

VALUE_HEADER = re.compile(r"^(Characteristic|Parameter|Factor|Comment)\b|^Date$")
DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b|\b(\d{1,2})[./](\d{1,2})[./](\d{2}|\d{4})\b")
NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def canonical_number(text):
    value = float(text.replace(",", "."))
    return f"{value:.10f}".rstrip("0").rstrip(".") or "0"


SOURCES = {"phage": ROOT / "work/eval_phage/input/eLabFTW_protocol_85318_EXP001_BAS33_bacteriophage_seq.elab2arc.md",
           "sdy1": ROOT / "work/eval_sdy1/input/eLabFTW_protocol_51585_SDY1_phenotyping_SSD1.elab2arc.md",
           "sdy1_pdfinput": ROOT / "work/eval_sdy1_pdfinput/input/eLabFTW_protocol_51585_SDY1_phenotyping_SSD1.elab2arc.md",
           "biolector034": ROOT / "work/eval_biolector034/input/eLabFTW_protocol_73918_BioLector_034_Pima1_Malt_Glc.elab2arc.md",
           "ux511": ROOT / "work/eval_ux511/input/eLabFTW_protocol_72729_Generation_of_UX511-523.elab2arc.md",
           "pux782": ROOT / "work/eval_pux782/input/eLabFTW_protocol_71968_Generation_of_pUX782-787.elab2arc.md"}
LINT = not __import__("os").environ.get("STRICT")
UNITS = {  # unit -> (dimension, factor to base unit)
    "l": ("vol", 1), "ml": ("vol", 1e-3), "µl": ("vol", 1e-6), "ul": ("vol", 1e-6), "μl": ("vol", 1e-6),
    "microliter": ("vol", 1e-6), "milliliter": ("vol", 1e-3),
    "h": ("time", 1), "hr": ("time", 1), "hrs": ("time", 1), "hour": ("time", 1), "hours": ("time", 1),
    "min": ("time", 1 / 60), "mins": ("time", 1 / 60), "minute": ("time", 1 / 60), "minutes": ("time", 1 / 60),
    "sec": ("time", 1 / 3600), "s": ("time", 1 / 3600), "second": ("time", 1 / 3600),
    "m": ("mol", 1), "mm": ("mol", 1e-3), "µm": ("mol", 1e-6), "um": ("mol", 1e-6), "nm": ("mol", 1e-9),
    "millimolar": ("mol", 1e-3), "micromolar": ("mol", 1e-6), "nanomolar": ("mol", 1e-9),
    "g": ("mass", 1), "mg": ("mass", 1e-3), "µg": ("mass", 1e-6), "ug": ("mass", 1e-6), "ng": ("mass", 1e-9),
    "gram": ("mass", 1), "nanogram": ("mass", 1e-9), "microgram": ("mass", 1e-6),
    "mg/ml": ("mconc", 1), "µg/ml": ("mconc", 1e-3), "ug/ml": ("mconc", 1e-3), "ng/µl": ("mconc", 1e-3),
    "ng/ul": ("mconc", 1e-3), "g/l": ("mconc", 1), "microgram per milliliter": ("mconc", 1e-3),
    "milligram per milliliter": ("mconc", 1), "nanogram per microliter": ("mconc", 1e-3),
    "°c": ("temp", 1), "degree celsius": ("temp", 1), "rpm": ("rpm", 1),
}
UNITS.update({k.replace("\u00b5", "\u03bc"): v for k, v in UNITS.items() if "\u00b5" in k})   # Greek mu: re.I makes it match the micro sign
UNIT_RX = "|".join(sorted((re.escape(u) for u in UNITS), key=len, reverse=True))
DURATION = re.compile(r"(\d+)\s*(?:h|hrs?|hours?)\s*(\d+)\s*(?:min|mins|minutes?)(?![a-zA-Z])", re.I)
WITH_UNIT = re.compile(rf"(\d+(?:[.,]\d+)?)\s*({UNIT_RX})(?![a-zA-Z])", re.I)


def lint(text, column_unit=""):
    """Formatting-only normalisation of one cell: durations -> hours, number + unit -> value in a base unit."""
    text = DURATION.sub(lambda m: f"{int(m.group(1)) + int(m.group(2)) / 60:.12g} h", str(text))
    if column_unit and re.fullmatch(r"\s*\d+(?:[.,]\d+)?\s*", text):
        text = f"{text} {column_unit}"

    def base(m):
        dim, factor = UNITS[m.group(2).lower()]
        return f"{float(m.group(1).replace(',', '.')) * factor:.12g} {dim}"
    return WITH_UNIT.sub(base, text)


HASH = re.compile(r"^(sha256:\s*)?[0-9a-f]{32,}$", re.I)


def _tokens(text):
    """Normalised tokens of a text: ISO dates, canonical numbers, "-" between two numbers, lower-case words."""
    out = []
    if re.fullmatch(r"\s*\d{1,3}(?: \d{3})+\s*", text):   # a code written in digit groups: "97 613 732"
        text = text.replace(" ", "")

    def date(m):
        if m.group(1):
            y, mo, d = m.group(1), m.group(2), m.group(3)
        else:
            d, mo, y = m.group(4), m.group(5), m.group(6)
            y = y if len(y) == 4 else "20" + y
        return f" \x01{y}{int(mo):02d}{int(d):02d} "  # placeholder without a dash: survives the range step
    text = DATE.sub(date, text).lower()
    text = re.sub(r"(?<=\d)\s*[-–]\s*(?=\d)", " \x02 ", text)
    # a token glueing letters and digits ("7mu", "r05", "xl1", "paz276pretb", "m9", "bas33") is one identifier,
    # never a number; a number glued to a unit ("15h", "180µl") also stays one token here - its lint form
    # (number + unit -> base unit) is what makes it comparable
    for tok in re.findall(r"\x01\d{8}|\x02|[a-z0-9äöüßµμ°%]+(?:[.,]\d+)?", text):
        if tok[0] == "\x01":
            out.append(f"{tok[1:5]}-{tok[5:7]}-{tok[7:9]}")
        elif tok == "\x02":
            out.append("-")
        elif re.fullmatch(r"\d+(?:[.,]\d+)?", tok):
            out.append(canonical_number(tok))
        else:
            out.append(tok)
    return " ".join(out)


def atoms(cell, column_unit=""):
    """One cell -> [(kind, normalised cell, lint form)] (empty for an empty or hash cell). kind is 'num' when the
    cell contains digits, 'text' otherwise; the lint form is None when the cell carries no unit."""
    text = str(cell).strip()
    if not text or HASH.match(text):
        return []
    plain = _tokens(text)
    if not plain:
        return []
    lint_form = None
    if LINT:
        unit = str(column_unit or "").strip()
        linted = lint(text, unit if unit.lower() in UNITS else "")
        if linted != text:  # a duration or a number with a known unit was converted
            lint_form = _tokens(linted)
    return [("num" if re.search(r"\d", text) else "text", plain, lint_form)]


def facts(xlsx, keep_sheets=None):
    """-> {'distinct': {kind: set}, 'per-row': {kind: Counter}} for one assay xlsx."""
    wb = openpyxl.load_workbook(xlsx, read_only=True)
    sheets = [s for s in wb.sheetnames if s != "isa_assay"]
    if keep_sheets is not None:
        sheets = keep_sheets(sheets)
    distinct = {"num": set(), "text": set()}
    per_row = {"num": Counter(), "text": Counter()}
    col_distinct = {"num": Counter(), "text": Counter()}
    for name in sheets:
        rows = list(wb[name].iter_rows(values_only=True))
        if len(rows) < 2:
            continue
        header = [str(h or "").strip() for h in rows[0]]
        for j, h in enumerate(header):
            if not VALUE_HEADER.match(h):
                continue
            has_unit = j + 1 < len(header) and header[j + 1] == "Unit"
            cells = []
            for r in rows[1:]:
                value = r[j] if j < len(r) and r[j] is not None else ""
                unit = (r[j + 1] or "") if has_unit and j + 1 < len(r) else ""
                cells.append((str(value), str(unit)))
            per_cell = [atoms(v, u) for v, u in cells]
            for a in per_cell:
                for kind, fact, lint_form in a:
                    distinct[kind].add((fact, lint_form))
            counted = per_cell[:1] if len(set(cells)) == 1 else per_cell
            for a in counted:
                for kind, fact, lint_form in a:
                    per_row[kind][(fact, lint_form)] += 1
            for v, u in set(cells):
                for kind, fact, lint_form in atoms(v, u):
                    col_distinct[kind][(fact, lint_form)] += 1
    return {"distinct": distinct, "per-row": per_row, "column-distinct": col_distinct}


DIMENSIONS = {"vol", "time", "mol", "mass", "mconc", "temp", "rpm"}
ISO = re.compile(r"\d{4}-\d{2}-\d{2}")


@functools.lru_cache(maxsize=None)
def quantities(cell):
    """Quantities of a normalised cell, in order: (value, dimension) - a date, a range "a-b", or a number with
    the dimension word that follows it in lint form ('' if none)."""
    toks, out, k = cell.split(), [], 0
    while k < len(toks):
        t = toks[k]
        if ISO.fullmatch(t):
            out.append((t, "date")); k += 1; continue
        if re.fullmatch(r"\d+(?:\.\d+)?", t):
            if k + 2 < len(toks) and toks[k + 1] == "-" and re.fullmatch(r"\d+(?:\.\d+)?", toks[k + 2]):
                out.append((f"{t}-{toks[k + 2]}", "")); k += 3; continue
            dim = toks[k + 1] if k + 1 < len(toks) and toks[k + 1] in DIMENSIONS else ""
            out.append((t, dim)); k += 2 if dim else 1; continue
        k += 1
    return out


def same_quantity(a, b):
    return a[0] == b[0] and (not a[1] or not b[1] or a[1] == b[1])


def compatible(pk, gk, leading=True):
    """May predicted cell pk and annotation cell gk be one match? Keys are (normalised cell, lint form).
    (1) same cell, unless both lint forms exist and differ; (2) same lint form; (3) leading quantity."""
    if pk[0] == gk[0] and (pk[1] is None or gk[1] is None or pk[1] == gk[1]):
        return True
    if pk[1] is not None and pk[1] == gk[1]:
        return True
    if not leading:
        return False
    return leads_with(pk, gk) or leads_with(gk, pk)


def leads_with(a, b):
    """Rule (3): cell a is exactly one quantity with a unit or a date, and cell b starts with that same
    quantity (same value and dimension), e.g. "26.5" hour vs "26h30min (450 loops)"."""
    qa_cell, qb_cell = a[1] or a[0], b[1] or b[0]
    qa = quantities(qa_cell)
    if len(qa) != 1 or not qa[0][1]:
        return False
    if any(not (re.fullmatch(r"\d+(?:\.\d+)?", t) or ISO.fullmatch(t) or t in DIMENSIONS) for t in qa_cell.split()):
        return False                              # a holds something besides its quantity
    first = qb_cell.split()[:1]
    qb = quantities(qb_cell)
    return bool(first and qb and (re.fullmatch(r"\d+(?:\.\d+)?", first[0]) or ISO.fullmatch(first[0]))
                and qb[0] == qa[0])


def max_matching(pred, annotation, leading=True):
    """Maximum one-to-one matching between predicted and annotation cells (Counters of keys; each count is one
    cell) over the compatible() relation. Kuhn's augmenting paths; the size is unique, so TP does not depend
    on iteration order. -> (TP, unmatched predicted Counter)."""
    p_nodes = [k for k, n in pred.items() for _ in range(n)]
    g_nodes = [k for k, n in annotation.items() for _ in range(n)]
    g_keys = list(annotation)
    ok = {pk: [gk for gk in g_keys if compatible(pk, gk, leading)] for pk in pred}
    slots = {}                                   # annotation key -> indices of its cells in g_nodes
    for idx, gk in enumerate(g_nodes):
        slots.setdefault(gk, []).append(idx)
    owner = [-1] * len(g_nodes)                  # annotation cell -> predicted cell index
    def augment(pi, seen):
        for gk in ok[p_nodes[pi]]:
            for gi in slots.get(gk, []):
                if gi in seen:
                    continue
                seen.add(gi)
                if owner[gi] == -1 or augment(owner[gi], seen):
                    owner[gi] = pi
                    return True
        return False
    sys.setrecursionlimit(max(10000, 4 * len(p_nodes) + 100))
    matched = [False] * len(p_nodes)
    for pi in range(len(p_nodes)):
        matched[pi] = augment(pi, set())
    tp = sum(1 for o in owner if o != -1)
    left = Counter(p_nodes[pi] for pi in range(len(p_nodes)) if pi not in set(owner))
    return tp, left


def match(pred, annotation, stats=None):
    """Matching of cells -> (TP, unmatched predicted Counter); stats["tp_leading"] = matches that need rule (3)."""
    tp, left = max_matching(Counter(pred), Counter(annotation))
    if stats is not None:
        stats["tp_leading"] = tp - max_matching(Counter(pred), Counter(annotation), leading=False)[0]
    return tp, left


def prf(pred, annotation):
    pred = Counter(pred) if isinstance(pred, set) else pred
    annotation = Counter(annotation) if isinstance(annotation, set) else annotation
    stats = {}
    tp, _ = match(pred, annotation, stats)
    np_, ng = sum(pred.values()), sum(annotation.values())
    p = tp / np_ if np_ else 0.0
    r = tp / ng if ng else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"tp": tp, "predicted": np_, "annotation": ng, "precision": p, "recall": r, "f1": f, "tp_leading": stats["tp_leading"]}


def source_atoms(case):
    """Normalised number/date tokens of the source text (also in lint form)."""
    text = SOURCES[case].read_text() if case in SOURCES and SOURCES[case].exists() else ""
    toks = set(_tokens(text).split()) | set(_tokens(lint(text)).split())
    return {t for t in toks if t[0].isdigit()}


def score(pred_facts, annotation_facts, src=frozenset()):
    out = {}
    for mode in ("distinct", "per-row", "column-distinct"):
        pf, gf = pred_facts[mode], annotation_facts[mode]
        both_p = (pf["num"] | pf["text"]) if mode == "distinct" else (pf["num"] + pf["text"])
        both_g = (gf["num"] | gf["text"]) if mode == "distinct" else (gf["num"] + gf["text"])
        out[mode] = {"numbers": prf(pf["num"], gf["num"]), "text": prf(pf["text"], gf["text"]), "all": prf(both_p, both_g)}
        num_p = Counter(pf["num"]) if isinstance(pf["num"], set) else pf["num"]
        num_g = Counter(gf["num"]) if isinstance(gf["num"], set) else gf["num"]
        _, left = match(num_p, num_g)
        in_src = lambda cell: all(t in src for t in cell.split() if t[0].isdigit())
        out[mode]["all"]["fp_in_source"] = sum(n for (fact, lint_form), n in left.items() if in_src(fact))
    return out


def records(xlsx, keep_sheets=None):
    """-> list of records, one per data row of every sheet except isa_assay: the list of (kind, key) of its value
    cells, key = (normalised cell, lint form) exactly as in facts(). Rows without a value cell are skipped."""
    wb = openpyxl.load_workbook(xlsx, read_only=True)
    sheets = [s for s in wb.sheetnames if s != "isa_assay"]
    if keep_sheets is not None:
        sheets = keep_sheets(sheets)
    out = []
    for name in sheets:
        rows = list(wb[name].iter_rows(values_only=True))
        if len(rows) < 2:
            continue
        header = [str(h or "").strip() for h in rows[0]]
        cols = [(j, j + 1 < len(header) and header[j + 1] == "Unit") for j, h in enumerate(header) if VALUE_HEADER.match(h)]
        for r in rows[1:]:
            cells = []
            for j, has_unit in cols:
                value = r[j] if j < len(r) and r[j] is not None else ""
                unit = (r[j + 1] or "") if has_unit and j + 1 < len(r) else ""
                cells += [(kind, (fact, lint_form)) for kind, fact, lint_form in atoms(value, unit)]
            if cells:
                out.append(cells)
    return out


def pair_matching(p_keys, g_keys, ok):
    """Maximum one-to-one matching of the cells of two records -> list of matched predicted cell indices.
    ok[pk] = set of annotation keys compatible with predicted key pk."""
    owner = [-1] * len(g_keys)
    def augment(pi, seen):
        for gi, gk in enumerate(g_keys):
            if gi not in seen and gk in ok[p_keys[pi]]:
                seen.add(gi)
                if owner[gi] == -1 or augment(owner[gi], seen):
                    owner[gi] = pi
                    return True
        return False
    return [pi for pi in range(len(p_keys)) if augment(pi, set())]


def record_score(pred_recs, annotation_recs):
    """Record F1: Hungarian alignment of records on matched cells, then cells matched inside aligned pairs."""
    p_keys = [[k for _, k in rec] for rec in pred_recs]
    g_keys = [[k for _, k in rec] for rec in annotation_recs]
    annotation_distinct = {k for keys in g_keys for k in keys}
    ok = {pk: {gk for gk in annotation_distinct if compatible(pk, gk)} for keys in p_keys for pk in keys}
    weight = np.zeros((len(p_keys), len(g_keys)), dtype=np.int64)
    g_sets = [set(keys) for keys in g_keys]
    for i, keys in enumerate(p_keys):
        reach = set().union(*(ok[k] for k in keys))
        for j, gs in enumerate(g_sets):
            if reach & gs:                       # no compatible cell at all -> weight 0, skip the matching
                weight[i, j] = len(pair_matching(keys, g_keys[j], ok))
    rows, cols = linear_sum_assignment(weight, maximize=True) if weight.size else ([], [])
    tp = {"num": 0, "text": 0}
    aligned = 0
    for i, j in zip(rows, cols):
        if weight[i, j] == 0:
            continue
        aligned += 1
        for pi in pair_matching(p_keys[i], g_keys[j], ok):
            tp[pred_recs[i][pi][0]] += 1
    out = {}
    for kind in ("num", "text", "all"):
        t = tp["num"] + tp["text"] if kind == "all" else tp[kind]
        np_ = sum(1 for rec in pred_recs for c in rec if kind == "all" or c[0] == kind)
        ng = sum(1 for rec in annotation_recs for c in rec if kind == "all" or c[0] == kind)
        p, r = (t / np_ if np_ else 0.0), (t / ng if ng else 0.0)
        out[{"num": "numbers", "text": "text", "all": "all"}[kind]] = {
            "tp": t, "predicted": np_, "annotation": ng, "precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0}
    out["all"].update({"records_aligned": aligned, "records_predicted": len(pred_recs), "records_annotation": len(annotation_recs),
                       "records_unaligned_predicted": len(pred_recs) - aligned, "records_unaligned_annotation": len(annotation_recs) - aligned})
    return out


def full_score(xlsx, annotation_xlsx, annotation_facts, annotation_recs, src=frozenset(), keep_sheets=None):
    s = score(facts(xlsx, keep_sheets), annotation_facts, src)
    s["record"] = record_score(records(xlsx, keep_sheets), annotation_recs)
    return s


def zero_score(annotation_facts, annotation_recs):
    """Score of a failed run: nothing predicted, every annotation cell missed."""
    def zero(ng):
        return {"tp": 0, "predicted": 0, "annotation": ng, "precision": 0.0, "recall": 0.0, "f1": 0.0}
    out = {}
    for mode in ("distinct", "per-row", "column-distinct"):
        gf = annotation_facts[mode]
        n = {k: (len(v) if isinstance(v, set) else sum(v.values())) for k, v in gf.items()}
        both = len(gf["num"] | gf["text"]) if mode == "distinct" else n["num"] + n["text"]
        out[mode] = {"numbers": zero(n["num"]), "text": zero(n["text"]), "all": {**zero(both), "fp_in_source": 0}}
    count = lambda kind: sum(1 for rec in annotation_recs for c in rec if kind is None or c[0] == kind)
    out["record"] = {"numbers": zero(count("num")), "text": zero(count("text")), "all": zero(count(None))}
    return out


def swapped_copy(xlsx):
    """A copy of an annotation xlsx with the values of two rows exchanged in one value column (a label swap) -> path.
    The two rows must also differ in another value column: records carry no names, so swapping the only
    difference between two rows just swaps the rows and changes nothing."""
    wb = openpyxl.load_workbook(xlsx)
    for ws in wb.worksheets:
        if ws.title == "isa_assay":
            continue
        header = [str(c.value or "").strip() for c in ws[1]]
        value_cols = [j for j, h in enumerate(header, start=1) if VALUE_HEADER.match(h)]
        for j in value_cols:
            values = [ws.cell(r, j).value for r in range(2, ws.max_row + 1)]
            distinct = [r for r, v in enumerate(values, start=2) if atoms(v or "")]
            differs_elsewhere = lambda a, b: any(ws.cell(a, k).value != ws.cell(b, k).value for k in value_cols if k != j)
            pair = next(((a, b) for a in distinct for b in distinct if a < b and ws.cell(a, j).value != ws.cell(b, j).value
                         and differs_elsewhere(a, b)), None)
            if pair:
                a, b = pair
                ws.cell(a, j).value, ws.cell(b, j).value = ws.cell(b, j).value, ws.cell(a, j).value
                path = Path(tempfile.mkdtemp()) / "swapped.xlsx"
                wb.save(path)
                return path
    raise RuntimeError(f"no swappable column in {xlsx}")


def controls(case, annotation_facts, annotation_recs):
    for g, p in CASES[case]["annotations"].items():
        s = full_score(p, p, annotation_facts[g], annotation_recs[g])
        assert all(m["f1"] == 1.0 for mode in s.values() for m in mode.values() if m["annotation"]), f"self-score of {g}: {s}"
        half = lambda sh: sh[: 1 + (len(sh) - 1) // 2]
        s = full_score(p, p, annotation_facts[g], annotation_recs[g], keep_sheets=half)
        for mode in ("per-row", "record"):
            assert s[mode]["all"]["precision"] == 1.0 and s[mode]["all"]["recall"] < 1.0, f"truncated {g} {mode}: {s[mode]}"
        sw = swapped_copy(p)
        s = full_score(sw, p, annotation_facts[g], annotation_recs[g])
        assert s["column-distinct"]["all"]["f1"] == 1.0, f"swap control {g}: column-distinct changed"
        assert s["record"]["all"]["f1"] < 1.0, f"swap control {g}: record F1 did not drop"
        z = zero_score(annotation_facts[g], annotation_recs[g])
        assert all(m["f1"] == 0.0 and m["annotation"] > 0 for mode in z.values() for m in mode.values() if m["annotation"]), "failure control"
        ge = annotation_evidence(case, g)
        if ge:   # grounding: the annotation at its own first occurrence is fully grounded; spans moved away ground nothing
            cells = [((c["normalised"], c["lint"]), tuple(tuple(o["char_span"]) for o in c["occurrences"])) for c in ge["cells"]]
            at_first = [(k, occ[0] if occ else None) for k, occ in cells]
            assert located_matching(at_first, cells) == sum(1 for _, occ in cells if occ), f"grounding self-control {g}"
            assert located_matching([(k, (-2, -1) if sp else None) for k, sp in at_first], cells) == 0, f"grounding move-control {g}"
    return (f"controls OK ({case}): annotation vs itself 1.0 in every mode; truncated annotation keeps P 1.0 and loses R; "
            "a two-row value swap keeps column-distinct 1.0 and lowers record F1; a failed run scores 0; "
            "grounding: annotation at its own locations fully grounded, moved locations ground nothing")


def annotation_evidence(case, annotation):
    """31_annotation_evidence.py output for one annotation: every annotation value cell with its occurrences in the LLM input text."""
    f = CASES[case]["eval"] / f"annotation_evidence.{re.sub(r'\W+', '_', annotation.lower()).strip('_')}.json"
    return json.loads(f.read_text()) if f.exists() else None


def predicted_cells(run_dir):
    """Value cells of a run's LLM JSON, each with its resolved source span (32_resolve_evidence.js) or None.
    A scalar parameter counts once per row of its protocol, as in the xlsx. -> (cells, evidence summary, source
    sha256), or None when the run has no evidence.json (prompts before v7)."""
    ev_file = run_dir / "evidence.json"
    if not ev_file.exists():
        return None
    ev = json.loads(ev_file.read_text())
    by_path = {e["field_path"]: e for e in ev["entries"]}
    data = llm_data(json.loads((run_dir / "llm.json").read_text()))
    cells = []

    def add(value, unit, path):
        e = by_path.get(path)
        span = tuple(e["char_span"]) if e and e["status"] in ("exact", "fuzzy") else None
        cells.extend(((fact, lint_form), span) for _, fact, lint_form in atoms("" if value is None else value, unit or ""))
    for i, s in enumerate(data.get("samples") or []):
        for j, c in enumerate(s.get("characteristics") or []):
            add(c.get("value"), c.get("unit"), f"samples[{i}].characteristics[{j}].value")
    for i, p in enumerate(data.get("protocols") or []):
        rows = max(1, len(p.get("inputs") or []))
        for j, prm in enumerate(p.get("parameters") or []):
            base, value = f"protocols[{i}].parameters[{j}].value", prm.get("value")
            if isinstance(value, list):
                for k, v in enumerate(value):
                    add(v, prm.get("unit"), f"{base}[{k}]")
            else:
                for _ in range(rows):
                    add(value, prm.get("unit"), base)
    return cells, ev["summary"], ev.get("source_sha256")


def located_matching(pred, annotation, need_location=True):
    """Maximum one-to-one matching of predicted cells (key, span) to annotation cells (key, occurrence spans): a pair
    needs compatible values (28's rules) and, with need_location, a predicted span overlapping one of the annotation
    value's occurrences. Kuhn's augmenting paths, as in max_matching()."""
    P, G = Counter(pred), Counter(annotation)
    compat = {}
    def ok_pair(pt, gt):
        key = (pt[0], gt[0])
        if key not in compat:
            compat[key] = compatible(pt[0], gt[0])
        return compat[key] and (not need_location or (pt[1] is not None and any(a < pt[1][1] and pt[1][0] < b for a, b in gt[1])))
    ok = {pt: [gt for gt in G if ok_pair(pt, gt)] for pt in P}
    p_nodes = [k for k, n in P.items() for _ in range(n)]
    slots = {}
    for idx, gt in enumerate(k for k, n in G.items() for _ in range(n)):
        slots.setdefault(gt, []).append(idx)
    owner = [-1] * sum(G.values())
    def augment(pi, seen):
        for gt in ok[p_nodes[pi]]:
            for gi in slots[gt]:
                if gi not in seen:
                    seen.add(gi)
                    if owner[gi] == -1 or augment(owner[gi], seen):
                        owner[gi] = pi
                        return True
        return False
    sys.setrecursionlimit(max(10000, 4 * len(p_nodes) + 100))
    return sum(1 for pi in range(len(p_nodes)) if augment(pi, set()))


def grounding_score(run_dir, case, annotation):
    """Traceability of one run against one annotation (None when the run carries no evidence).
    traceable_share  predicted cells whose quote resolved to a passage containing the value (no annotation needed)
    grounding P/R/F1 a cell counts only when its value is accepted AND its quote lies on an occurrence of that
                     annotation value in the source (ExtractBench's grounded F1; all annotation cells, any occurrence)
    verified         the annotation cells whose location is known - the value occurs exactly once (certain), or the row's context
                     resolves it to one section (31, status context, only where its shuffle control shows the resolution is row-specific): share found
                     by value, and share found by value at the right place."""
    pc = predicted_cells(run_dir)
    ge = annotation_evidence(case, annotation)
    if pc is None or ge is None:
        return None
    cells, summary, sha = pc
    if sha and sha != ge["source_sha256"]:
        return {"error": "evidence and annotation evidence refer to different source texts"}
    annotation_cells = [((c["normalised"], c["lint"]), tuple(tuple(o["char_span"]) for o in c["occurrences"])) for c in ge["cells"]]
    certain = [g for g, c in zip(annotation_cells, ge["cells"]) if c["status"] == "unique"]
    # verified = certain (value occurs once) + context-resolved (31_annotation_evidence.py: the row's own context points to one
    # occurrence; any occurrence in that occurrence's section is accepted, since a sentence-level pick is a heuristic)
    unique = certain + [((c["normalised"], c["lint"]), tuple(tuple(c["occurrences"][i]["char_span"]) for i in c["same_section"]))
                        for c in ge["cells"] if c["status"] == "context" and ge["summary"]["context_row_specific"]]
    tp = located_matching(cells, annotation_cells)
    p, r = (tp / len(cells) if cells else 0.0), (tp / len(annotation_cells) if annotation_cells else 0.0)
    return {"traceable_share": summary["traceable_share"], "evidence": summary,
            "tp": tp, "predicted": len(cells), "annotation": len(annotation_cells),
            "precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0,
            "verified_annotation": len(unique), "certain_annotation": len(certain),
            "certain_grounded_recall": located_matching(cells, certain) / len(certain) if certain else 0.0,
            "verified_value_recall": located_matching(cells, unique, need_location=False) / len(unique) if unique else 0.0,
            "verified_grounded_recall": located_matching(cells, unique) / len(unique) if unique else 0.0}


def score_case(case):
    """Score every run of one case against its annotations -> list of leaderboard rows; writes scores.json / scores.md."""
    cfg = CASES[case]
    annotations = cfg["annotations"]
    missing = [str(p) for p in annotations.values() if not p.exists()]
    if missing:
        sys.exit("missing annotation: " + ", ".join(missing))
    annotation_facts = {g: facts(p) for g, p in annotations.items()}
    annotation_recs = {g: records(p) for g, p in annotations.items()}
    print(controls(case, annotation_facts, annotation_recs))
    src = source_atoms(case)
    runs = discover(case)
    for g, p in annotations.items():
        runs[f"annotation {g} (reference)"] = {"dir": p.parent, "model": f"annotation {g}", "prompt": "reference", "rep": "",
                                         "xlsx": p, "status": "ok", "reason": ""}
    results, board = {}, []
    for label, run in runs.items():
        if run["status"] == "incomplete":
            continue
        meta = run_meta(run["dir"]) if not label.startswith("annotation") else {}
        tables, rows = table_shape(run["xlsx"]) if run["status"] == "ok" else (0, 0)
        for g in annotations:
            if label == f"annotation {g} (reference)":
                continue
            s = (full_score(run["xlsx"], annotations[g], annotation_facts[g], annotation_recs[g], src) if run["status"] == "ok"
                 else zero_score(annotation_facts[g], annotation_recs[g]))
            s["status"], s["reason"] = run["status"], run["reason"]
            gs = grounding_score(run["dir"], case, g) if run["status"] == "ok" and not label.startswith("annotation") else None
            if gs:
                s["grounding"] = gs
            results[f"{label} | vs {g}"] = s
            rec, cd, pr = s["record"]["all"], s["column-distinct"]["all"], s["per-row"]["all"]
            gs = gs if gs and "error" not in gs else {}
            board.append({"case": case, "annotation": g, "label": label, "model": run["model"], "prompt": run["prompt"],
                          "run": run["rep"], "status": run["status"], "reason": run["reason"],
                          "record_p": rec["precision"], "record_r": rec["recall"], "record_f1": rec["f1"],
                          "records_predicted": rec.get("records_predicted", 0), "records_annotation": rec.get("records_annotation"),
                          "records_aligned": rec.get("records_aligned", 0),
                          "column_distinct_f1": cd["f1"], "per_row_f1": pr["f1"], "tables": tables, "rows": rows,
                          "traceable_share": gs.get("traceable_share"), "grounding_p": gs.get("precision"),
                          "grounding_r": gs.get("recall"), "grounding_f1": gs.get("f1"),
                          "verified_value_recall": gs.get("verified_value_recall"),
                          "verified_grounded_recall": gs.get("verified_grounded_recall"),
                          **{k: meta.get(k) for k in ("calls", "prompt_tokens", "completion_tokens", "seconds", "cost_usd")}})
    (cfg["eval"] / "scores.json").write_text(json.dumps(results, indent=1))
    write_case_md(case, results)
    return board


def write_case_md(case, results):
    head = ("| Run | Annotation | Mode | P | R | F1 | numbers P / R / F1 | text P / R / F1 | TP / predicted / annotation |\n"
            "|---|---|---|---|---|---|---|---|---|")
    lines = []
    for key, s in results.items():
        label, g = key.split(" | vs ")
        flag = "" if s["status"] == "ok" else f" **FAILED** ({s['reason'][:80]})"
        for mode in ("record", "column-distinct", "per-row", "distinct"):
            a, n, t = s[mode]["all"], s[mode]["numbers"], s[mode]["text"]
            lines.append(f"| {label}{flag} | {g} | {mode} | {a['precision']:.3f} | {a['recall']:.3f} | **{a['f1']:.3f}** "
                         f"| {n['precision']:.3f} / {n['recall']:.3f} / {n['f1']:.3f} | {t['precision']:.3f} / {t['recall']:.3f} / "
                         f"{t['f1']:.3f} | {a['tp']} / {a['predicted']} / {a['annotation']} |")
        gr = s.get("grounding")
        if gr and "error" not in gr:
            lines.append(f"| {label} | {g} | grounding (traceable {gr['traceable_share']:.1%}) | {gr['precision']:.3f} | "
                         f"{gr['recall']:.3f} | **{gr['f1']:.3f}** | verified cells: value {gr['verified_value_recall']:.3f}, "
                         f"located {gr['verified_grounded_recall']:.3f} | | {gr['tp']} / {gr['predicted']} / {gr['annotation']} |")
    md = [f"# LLM conversion scores ({CASES[case]['title']})", "",
          "Generated by `scripts/28_score_extraction.py`; method in its docstring. Headline mode: **record** "
          "(rows aligned one-to-one, then cells). Failed runs are listed and score 0. P = precision, R = recall.", "",
          head] + lines
    (CASES[case]["eval"] / "scores.md").write_text("\n".join(md) + "\n")


def fmt_mean(values, digits=2):
    if not values:
        return "–"
    m = statistics.mean(values)
    return f"{m:.{digits}f}" + (f" ± {statistics.stdev(values):.{digits}f} (n={len(values)})" if len(values) > 1 else "")


def write_leaderboard(board):
    """leaderboard.csv (one row per run x annotation) and leaderboard.md (configs: mean over repeats per entry, and the
    unweighted mean over the three entries vs the headline annotation, only for configs run on all three)."""
    out = ROOT / "work/eval"
    fields = list(board[0].keys())
    with open(out / "leaderboard.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in board:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in row.items()})
    configs = {}
    for row in board:
        if row["prompt"] == "reference":
            continue
        configs.setdefault((row["model"], row["prompt"]), []).append(row)
    entries = [("phage", HEADLINE_ANNOTATION), ("sdy1", HEADLINE_ANNOTATION)]
    table = []
    for (model, prompt), rows in configs.items():
        per_entry = {}
        for case, g in entries:
            vals = [r for r in rows if r["case"] == case and r["annotation"] == g]
            per_entry[case] = vals
        complete = all(per_entry[c] for c, _ in entries)
        entry_means = [statistics.mean(r["record_f1"] for r in per_entry[c]) for c, _ in entries] if complete else []
        mean = statistics.mean(entry_means) if complete else None
        def cost(case, key):
            v = [r[key] for r in per_entry[case] if r[key] is not None]
            return f"{statistics.mean(v):,.0f}" if v else "–"
        cells = []
        for case, _ in entries:
            v = per_entry[case]
            if not v:
                cells.append("not run")
                continue
            failed = [r for r in v if r["status"] == "failed"]
            endpoint = sum(1 for r in failed if r["reason"].startswith("endpoint error"))
            note = (f" ({len(failed)} failed" + (f", {endpoint} by endpoint error" if endpoint else "") + ")") if failed else ""
            cells.append(fmt_mean([r["record_f1"] for r in v]) + note
                         + f"<br><sub>{cost(case, 'completion_tokens')} out-tok, {cost(case, 'seconds')} s</sub>")
        table.append((mean if mean is not None else -1, model, prompt, cells))
    table.sort(key=lambda t: -t[0])
    md = ["# Leaderboard: LLM extraction of eLabFTW protocols into ISA assays", "",
          "Generated by `scripts/28_score_extraction.py` (method in its docstring). Headline metric: **record F1** "
          f"against the {HEADLINE_ANNOTATION} manual annotation (independent human curation; the only annotation that exists for every entry): "
          "rows aligned one-to-one across all tables, then cells compared. Per entry: mean ± sd over repeated runs; "
          "failed runs count as 0. **Mean** = unweighted mean over the entries, only for configurations run on all "
          "of them. Below each score: mean completion tokens and seconds per run. Raw rows (every run x annotation, P/R, other "
          "modes, calls, prompt tokens, cost): `leaderboard.csv`.", "",
          "| Model | Prompt | Mean | Phage (dense measurements) | SDY1 (condition table) |",
          "|---|---|---|---|---|"]
    for mean, model, prompt, cells in table:
        md.append(f"| {model} | {prompt} | {'**%.2f**' % mean if mean >= 0 else '–'} | " + " | ".join(cells) + " |")
    traced = {}
    for row in board:
        if row["annotation"] == HEADLINE_ANNOTATION and row.get("traceable_share") is not None:
            traced.setdefault((row["model"], row["prompt"]), {})[row["case"]] = row
    if traced:
        lookup = {}
        for case, _ in entries:
            ge = annotation_evidence(case, HEADLINE_ANNOTATION)
            if ge:
                lookup[case] = ge["summary"]["unique"] / ge["summary"]["cells"]
        md += ["", "## Traceability (prompt v7: a verbatim quote per value, resolved by `32_resolve_evidence.js`)", "",
               "**Traceable** = share of the model's value cells whose quote was found in the protocol and contains the value. "
               f"**Grounding F1** (vs {HEADLINE_ANNOTATION}) = a cell counts only when its value matches an annotation cell AND its quote lies "
               "on an occurrence of that value in the source. **Verified** = annotation cells whose value occurs exactly once in the "
               "source: share found at that location. The first row is the reference: the share of the hand-curated annotation "
               "whose location can be recovered by looking its values up (`31_annotation_evidence.py`).", "",
               "| Model | Prompt | Phage: traceable / grounding F1 / verified | SDY1 |", "|---|---|---|---|",
               f"| {HEADLINE_ANNOTATION}'s annotation, by lookup | – | " + " | ".join(
                   f"unique location for {lookup[c]:.0%} of cells" if c in lookup else "–" for c, _ in entries) + " |"]
        for (model, prompt), per in sorted(traced.items()):
            cells = [(f"{per[c]['traceable_share']:.0%} / {per[c]['grounding_f1']:.2f} / {per[c]['verified_grounded_recall']:.2f}"
                      if c in per and per[c].get("grounding_f1") is not None else "–") for c, _ in entries]
            md.append(f"| {model} | {prompt} | " + " | ".join(cells) + " |")
    ceiling = [r for r in board if r["prompt"] == "reference"]
    if ceiling:
        md += ["", "Annotation vs annotation (ceiling, record F1): " + "; ".join(
            f"{r['case']} {r['label'].replace(' (reference)', '')} vs {r['annotation']}: {r['record_f1']:.2f}" for r in ceiling)]
    (out / "leaderboard.md").write_text("\n".join(md) + "\n")
    print(f"-> {out / 'leaderboard.csv'} ({len(board)} rows), {out / 'leaderboard.md'} ({len(table)} configurations)")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    cases = list(CASES) if arg == "all" else [arg]
    board = []
    for case in cases:
        board += score_case(case)
        print(f"-> {CASES[case]['eval'] / 'scores.md'}")
    if arg == "all":
        write_leaderboard(board)


if __name__ == "__main__":
    main()
