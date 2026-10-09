#!/opt/homebrew/bin/python3.13
"""Evidence feedback: what the evidence file of a v7.x run says about the run, without an LLM (PLAN_evidence_loop.md, phase A).

  34_evidence_feedback.py <run-dir> [--annotation]    -> <run-dir>/feedback.json + feedback.md
  34_evidence_feedback.py --control             controls: every check must fail on a deliberately wrong input

Inputs: llm.json (llmData), evidence.json (32_resolve_evidence.js: quote, character span, status per value cell), the protocol markdown
(llm.json "input", its sha256 must equal the evidence file's), and with --annotation the annotation evidence of the entry (31_annotation_evidence.py).

1. Cell diagnostics - every cell that is not exact / fuzzy gets exactly one class (rules, applied in this order):
     missing                          no quote given
     unresolved/table_paraphrase      quote not found; >= 0.6 of its distinct tokens occur in ONE source row (a text line, or one <tr> of a
                                      table) or two consecutive rows: the model rewrote a table row (reordered, words added or dropped)
     unresolved/not_in_source         quote not found and no row holds 0.6 of its tokens: text the source does not contain
     value_not_in_quote/number_changed  quote found, a number of the value is not among the numbers of the quote (rounded, converted, computed)
     value_not_in_quote/derived_label   quote found, all numbers of the value are in the quote but a word is not (an inferred label)
2. Source coverage (annotation-free): numeric tokens of the protocol text (numbers, dates, numbers glued to units; as 31_annotation_evidence.py tokenises)
   lying inside any resolved quote span. Per section (markdown heading, bold-only line, lone date line, HTML table block; a section of more than
   50 lines is cut into chunks of 40 lines) and overall; the 10 sections with most uncovered tokens.
3. Structure (annotation-free, heuristics): protocols without parameters; outputs never used as an input of another protocol; duplicate rows;
   rows written and the share of distinct sample labels that occur verbatim in the text.
4. With --annotation: verified annotation cells (value occurs once, or resolved by row context) whose source span no quote overlaps = recall missed at a known place.
"""
import bisect
import hashlib
import importlib.util
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent                  # root of the section; the run folders (work/eval*/) are not part of it


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename if filename.startswith("28_") else Path(__file__).resolve().parent / filename)
    mod = importlib.util.module_from_spec(spec)
    argv, sys.argv = sys.argv, sys.argv[:1]
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.argv = argv
    return mod


S = _load("score28", "28_score_extraction.py")
G = _load("annotation31", "31_annotation_evidence.py")

TAG = re.compile(r"<[^<>]{0,300}>")
MARKUP = re.compile(r"[*_`|\\#]")
NUMBER = re.compile(r"\d+(?:\.\d+)?")
ISO = re.compile(r"\d{4}-\d{2}-\d{2}")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+\S")
BOLD_LINE = re.compile(r"^\s*(?:_?\*\*|__).{1,200}(?:\*\*_?|__)\s*:?\s*$")
DATE_LINE = re.compile(r"^\s*(?:\d{4}-\d{2}-\d{2}|\d{1,2}[./]\d{1,2}[./]\d{2,4})\s*$")
PARAPHRASE_SHARE = 0.6
LONG_SECTION, CHUNK = 50, 40
GOOD = ("exact", "fuzzy")


# ---------------------------------------------------------------------------------------------------- text helpers
def toks(text):
    """normalised tokens of a text, as 31_annotation_evidence.py tokenises the source (markup characters are separators)."""
    return [t for t, _, _ in G.tokenize_source(MARKUP.sub(" ", text))[0]]


def is_numeric(t):
    return bool(NUMBER.fullmatch(t) or ISO.fullmatch(t))


def numeric_tokens(text):
    """-> [(start, end, token)] of the numeric tokens of the protocol text (numbers, ISO dates)."""
    return [(a, b, t) for t, a, b in G.tokenize_source(text)[0] if is_numeric(t)]


def source_rows(text):
    """Text lines, and inside a line every <tr> ... </tr> of a table, as (start, end) character ranges with non-empty text."""
    rows, pos = [], 0
    for line in text.split("\n"):
        start, end = pos, pos + len(line)
        pos = end + 1
        if "<tr" in line:
            cuts = [m.start() for m in re.finditer(r"<tr\b", line)]
            bounds = [start + c for c in cuts] + [end]
            rows += [(a, b) for a, b in zip(bounds, bounds[1:]) if TAG.sub("", text[a:b]).strip()]
        elif TAG.sub("", line).strip():
            rows.append((start, end))
    return rows


def classify_unresolved(quote, row_sets):
    """-> (class, best share, index of the best row). table_paraphrase when >= PARAPHRASE_SHARE of the quote's distinct tokens lie in
    one row or two consecutive rows (the index is the first row of the best window)."""
    q = set(toks(quote))
    if not q:
        return "not_in_source", 0.0, None
    best, at, size = 0.0, None, 0
    for i, r in enumerate(row_sets):
        for window in (r, r | row_sets[i + 1] if i + 1 < len(row_sets) else None):
            if window is None:
                continue
            share = len(q & window) / len(q)
            if share > best or (share == best and at is not None and len(window) < size):   # ties: the smaller row
                best, at, size = share, i, len(window)
    return ("table_paraphrase" if best >= PARAPHRASE_SHARE else "not_in_source"), round(best, 3), at


def classify_value_not_in_quote(value, quote):
    qn = {t for t in toks(quote) if is_numeric(t)}
    vn = [t for t in toks(str(value)) if is_numeric(t)]
    return "number_changed" if any(t not in qn for t in vn) else "derived_label"


def diagnose_cells(entries, text, flagged=None):
    """-> (counts per class, examples per class (<= 3 each, spread over distinct cells), per-entry class list); every cell that is not ok
    is also appended, with its class, to the list `flagged` when one is given."""
    rows = source_rows(text)
    row_sets = [set(toks(text[a:b])) for a, b in rows]
    classes, examples = [], {}
    for e in entries:
        st = e["status"]
        if st in GOOD:
            cls = "ok"
        elif st == "missing":
            cls = "missing"
        elif st == "unresolved":
            cls, share, at = classify_unresolved(e["quote"], row_sets)
            cls = "unresolved/" + cls
            e = {**e, "best_row_share": share}
            if at is not None and cls.endswith("table_paraphrase"):
                a, b = rows[at]
                e["line"] = text.count("\n", 0, a) + 1
                e["passage"] = re.sub(r"\s+", " ", TAG.sub(" ", text[a:b])).strip()[:240]
        elif st == "value_not_in_quote":
            cls = "value_not_in_quote/" + classify_value_not_in_quote(e["value"], e["quote"])
        else:
            raise ValueError(f"unknown status {st}")
        classes.append(cls)
        if cls != "ok":
            ex = {k: e.get(k) for k in ("field_path", "name", "value", "quote", "line", "passage", "best_row_share")
                  if e.get(k) is not None}
            if flagged is not None:
                flagged.append({**ex, "class": cls})
            if len(examples.setdefault(cls, [])) < 3:
                examples[cls].append(ex)
    return dict(Counter(classes)), examples, classes


# ---------------------------------------------------------------------------------------------------- coverage
def sections(text):
    """-> [{start_line, end_line, start, end, label}] covering the whole text (lines 1-based, chars [start, end))."""
    lines = text.split("\n")
    offs, pos = [], 0
    for ln in lines:
        offs.append(pos)
        pos += len(ln) + 1
    cuts, in_table = [0], False
    for i, ln in enumerate(lines):
        starts_table = "<table" in ln and not in_table
        if starts_table and i:
            cuts.append(i)
        if starts_table:
            in_table = True
        boundary = HEADING.match(ln) or BOLD_LINE.match(ln) or DATE_LINE.match(ln)
        if boundary and not in_table and i:
            cuts.append(i)
        if "</table>" in ln:
            in_table = False
            if i + 1 < len(lines):
                cuts.append(i + 1)
    cuts = sorted(set(cuts)) + [len(lines)]
    secs = []
    for a, b in zip(cuts, cuts[1:]):
        if b - a > LONG_SECTION:
            parts = list(range(a, b, CHUNK)) + [b]
        else:
            parts = [a, b]
        for x, y in zip(parts, parts[1:]):
            body = [l for l in lines[x:y] if TAG.sub("", l).strip()]
            if not body:
                continue
            label = re.sub(r"\s+", " ", TAG.sub(" ", MARKUP.sub("", body[0]))).strip()[:70]
            secs.append({"start_line": x + 1, "end_line": y, "start": offs[x],
                         "end": offs[y - 1] + len(lines[y - 1]) + 1 if y > x else offs[x], "label": label})
    return secs


def merge(spans):
    out = []
    for a, b in sorted(spans):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def inside(merged, a, b):
    """token [a, b) lies completely inside one merged span."""
    i = bisect.bisect_right([m[0] for m in merged], a) - 1
    return i >= 0 and merged[i][0] <= a and b <= merged[i][1]


def overlaps(merged, a, b):
    i = bisect.bisect_left([m[1] for m in merged], a + 1)
    return i < len(merged) and merged[i][0] < b


def coverage(text, spans):
    """Annotation-free source coverage of the numeric tokens by resolved quote spans, overall and per section."""
    merged = merge(spans)
    nums = numeric_tokens(text)
    secs = sections(text)
    starts = [s["start"] for s in secs]
    for s in secs:
        s["numeric"] = s["covered"] = 0
    for a, b, _ in nums:
        s = secs[max(0, bisect.bisect_right(starts, a) - 1)]
        s["numeric"] += 1
        s["covered"] += inside(merged, a, b)
    total, cov = len(nums), sum(s["covered"] for s in secs)
    for s in secs:
        s["uncovered"] = s["numeric"] - s["covered"]
        s["excerpt"] = re.sub(r"\s+", " ", TAG.sub(" ", text[s["start"]:s["end"]])).strip()[:200]
    top = sorted((s for s in secs if s["uncovered"]), key=lambda s: -s["uncovered"])[:10]
    return {"numeric_tokens": total, "covered": cov, "share": round(cov / total, 4) if total else None,
            "sections": secs, "top_uncovered": top}


# ---------------------------------------------------------------------------------------------------- structure
def norm_label(s):
    return " ".join(toks(str(s)))


def structure(data, text):
    prots = data.get("protocols") or []
    later_inputs = [set(p.get("inputs") or []) for p in prots]
    unused, dup_rows, rows_total = [], 0, 0
    for i, p in enumerate(prots):
        outs = p.get("outputs") or []
        elsewhere = set().union(*(later_inputs[j] for j in range(len(prots)) if j != i)) if len(prots) > 1 else set()
        unused.append({"protocol": p.get("name"), "outputs": len(set(outs)), "never_input_elsewhere": len(set(outs) - elsewhere),
                       "last_protocol": i == len(prots) - 1})
        n = max(len(p.get("inputs") or []), len(outs))
        rows_total += n
        sig = []
        for k in range(n):
            vals = []
            for prm in p.get("parameters") or []:
                v = prm.get("value")
                vals.append(v[k] if isinstance(v, list) and k < len(v) else (None if isinstance(v, list) else v))
            ins = p.get("inputs") or []
            sig.append((ins[k] if k < len(ins) else None, outs[k] if k < len(outs) else None, tuple(map(str, vals))))
        dup_rows += sum(c - 1 for c in Counter(sig).values() if c > 1)
    labels = {x for p in prots for x in (p.get("inputs") or []) + (p.get("outputs") or [])}
    labels |= {s.get("name") for s in data.get("samples") or [] if s.get("name")}
    ntext = " " + norm_label(text) + " "
    found = {x for x in labels if x and f" {norm_label(x)} " in ntext}
    return {"protocols": len(prots),
            "protocols_without_parameters": [p.get("name") for p in prots if not (p.get("parameters") or [])],
            "outputs_never_input_elsewhere": unused,
            "duplicate_rows": dup_rows, "rows_written": rows_total,
            "distinct_labels": len(labels), "labels_verbatim_in_text": len(found),
            "label_verbatim_share": round(len(found) / len(labels), 4) if labels else None,
            "note": "heuristics: a label built by the model (e.g. 'S1_diluted') legitimately does not occur in the text"}


# ---------------------------------------------------------------------------------------------------- annotation
def annotation_missed(annotation_ev, spans, secs):
    """verified annotation cells (unique, or context-resolved when the context is row-specific) whose source span no quote overlaps."""
    merged = merge(spans)
    row_specific = annotation_ev["summary"]["context_row_specific"]
    starts = [s["start"] for s in secs]
    verified = missed = 0
    by_section = Counter()
    examples = []
    for c in annotation_ev["cells"]:
        if c["status"] == "unique":
            occ = [c["occurrences"][0]["char_span"]]
        elif c["status"] == "context" and row_specific:
            occ = [c["occurrences"][i]["char_span"] for i in c["same_section"]]
        else:
            continue
        verified += 1
        if any(overlaps(merged, a, b) for a, b in occ):
            continue
        missed += 1
        a = c["occurrences"][c["resolved"]]["char_span"][0] if c["status"] == "context" else occ[0][0]
        s = secs[max(0, bisect.bisect_right(starts, a) - 1)]
        by_section[(s["start_line"], s["end_line"], s["label"])] += 1
        if len(examples) < 5:
            examples.append({"sheet": c["sheet"], "column": c["column"], "value": c["value"], "line": c["occurrences"][0]["line"]})
    top = [{"start_line": k[0], "end_line": k[1], "label": k[2], "missed_cells": n} for k, n in by_section.most_common(10)]
    return {"verified_annotation_cells": verified, "missed": missed, "missed_share": round(missed / verified, 4) if verified else None,
            "top_sections": top, "examples": examples}


# ---------------------------------------------------------------------------------------------------- run level
def load_run(run_dir):
    run_dir = Path(run_dir)
    raw = json.loads((run_dir / "llm.json").read_text())
    ev = json.loads((run_dir / "evidence.json").read_text())
    data = S.llm_data(raw)
    src = ROOT / raw["input"]
    text = src.read_text()
    sha = hashlib.sha256(text.encode()).hexdigest()
    if sha != ev["source_sha256"]:
        raise ValueError(f"{run_dir}: the protocol text differs from the one the evidence was resolved against")
    return data, ev, text, raw


def feedback(run_dir, annotation=False, annotation_file=None):
    run_dir = Path(run_dir)
    data, ev, text, raw = load_run(run_dir)
    entries = ev["entries"]
    flagged = []
    counts, examples, _ = diagnose_cells(entries, text, flagged)
    n = len(entries)
    spans = [tuple(e["char_span"]) for e in entries if e.get("char_span")]
    cov = coverage(text, spans)
    fb = {"run": run_dir.name, "entry": run_dir.parent.name, "source": ev["source"], "cells": n,
          "cell_classes": {k: {"cells": v, "share": round(v / n, 4)} for k, v in sorted(counts.items())},
          "examples": examples, "flagged_cells": flagged,
          "value_not_in_quote_share": round(sum(v for k, v in counts.items() if k.startswith("value_not_in_quote")) / n, 4) if n else None,
          "coverage": cov, "structure": structure(data, text)}
    if annotation:
        gf = Path(annotation_file) if annotation_file else run_dir.parent / "annotation_evidence.manual_annotation_b.json"
        gev = json.loads(gf.read_text())
        if gev["source_sha256"] != ev["source_sha256"]:
            raise ValueError("annotation evidence and run evidence refer to different source texts")
        fb["annotation"] = annotation_missed(gev, spans, cov["sections"])
    return fb


def render_md(fb):
    L = [f"# Evidence feedback: {fb['entry']} / {fb['run']}", "", f"Source `{fb['source']}`, {fb['cells']} value cells.", "",
         "## Cell classes", "", "| class | cells | share |", "|---|---|---|"]
    for k, v in fb["cell_classes"].items():
        L.append(f"| {k} | {v['cells']} | {v['share']:.3f} |")
    for cls, exs in fb["examples"].items():
        L += ["", f"### Examples: {cls}"]
        for e in exs:
            L.append(f"- `{e['field_path']}` ({e.get('name')}), value `{e['value']}`, quote `{str(e['quote'])[:160]}`"
                     + (f", line {e['line']}" if e.get("line") else "") + (f", best row share {e['best_row_share']}" if "best_row_share" in e else ""))
    c = fb["coverage"]
    L += ["", "## Source coverage (annotation-free)", "",
          f"Numeric tokens of the protocol text inside a resolved quote: {c['covered']} of {c['numeric_tokens']} (share {c['share']}).", "",
          "Top sections by uncovered numeric tokens:", "", "| lines | uncovered / numeric | section | excerpt |", "|---|---|---|---|"]
    for s in c["top_uncovered"]:
        L.append(f"| {s['start_line']}-{s['end_line']} | {s['uncovered']} / {s['numeric']} | {s['label']} | {s['excerpt'][:120].replace('|', '/')} |")
    st = fb["structure"]
    L += ["", "## Structure (heuristics)", "",
          f"- protocols {st['protocols']}; without parameters: {st['protocols_without_parameters'] or 'none'}",
          f"- rows written {st['rows_written']}; duplicate rows {st['duplicate_rows']}",
          f"- distinct sample labels {st['distinct_labels']}, verbatim in the text {st['labels_verbatim_in_text']} (share {st['label_verbatim_share']})",
          f"- outputs never used as an input elsewhere (not counting the last protocol): "
          f"{sum(u['never_input_elsewhere'] for u in st['outputs_never_input_elsewhere'] if not u['last_protocol'])} of "
          f"{sum(u['outputs'] for u in st['outputs_never_input_elsewhere'] if not u['last_protocol'])}"]
    if "annotation" in fb:
        g = fb["annotation"]
        L += ["", "## Annotation (benchmark only)", "",
              f"Verified annotation cells {g['verified_annotation_cells']}, source span covered by no quote: {g['missed']} (share {g['missed_share']}).", ""]
        for s in g["top_sections"]:
            L.append(f"- lines {s['start_line']}-{s['end_line']} `{s['label']}`: {s['missed_cells']} cells")
    return "\n".join(L) + "\n"


def write_feedback(run_dir, annotation):
    fb = feedback(run_dir, annotation)
    out = Path(run_dir)
    slim = json.loads(json.dumps(fb))
    slim["coverage"]["sections"] = [{k: v for k, v in s.items() if k != "excerpt"} for s in slim["coverage"]["sections"]]
    (out / "feedback.json").write_text(json.dumps(slim, indent=1))
    (out / "feedback.md").write_text(render_md(fb))
    return fb


# ---------------------------------------------------------------------------------------------------- controls
def control():
    fails = []

    def check(name, ok, detail=""):
        print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
        if not ok:
            fails.append(name)

    # 1. synthetic text with known numbers: exact expected coverage
    text = "Mix 5 µl of A with 10 ml of B at 37°C for 2 h.\n\nUnrelated: 99 and 100 ml.\n"
    a = text.index("Mix"); b = text.index("2 h") + 3
    c = coverage(text, [(a, b)])
    check("synthetic coverage 4 of 6 numeric tokens", (c["numeric_tokens"], c["covered"]) == (6, 4), f"{c['covered']}/{c['numeric_tokens']}")
    check("synthetic: no spans -> 0 covered", coverage(text, [])["covered"] == 0)
    check("synthetic: all spans -> all covered", coverage(text, [(0, len(text))])["covered"] == 6)
    # 1b. wrong expectation must be detected (control of the control): the check above fails if the expectation is wrong
    check("control of control: wrong expectation (5 of 6) is NOT met", (c["numeric_tokens"], c["covered"]) != (6, 5))
    # 2. diagnosis rules on synthetic cells
    t2 = "Strain S1 was grown at 37 °C.\n<table><tbody><tr><td>S1</td><td>734</td><td>1.8</td></tr><tr><td>S2</td><td>521</td><td>1.9</td></tr></tbody></table>\n"
    mk = lambda st, q, v: {"status": st, "quote": q, "value": v, "field_path": "x"}
    ents = [mk("exact", "Strain S1 was grown at 37 °C", "37"),
            mk("missing", "", "5"),
            mk("unresolved", "S2 521 1.9 measured", "521"),            # row words reordered with an extra word
            mk("unresolved", "completely different words about nothing", "7"),
            mk("value_not_in_quote", "Strain S1 was grown at 37 °C", "310 K"),
            mk("value_not_in_quote", "Strain S1 was grown at 37 °C", "warm culture")]
    _, _, cls = diagnose_cells(ents, t2)
    want = ["ok", "missing", "unresolved/table_paraphrase", "unresolved/not_in_source",
            "value_not_in_quote/number_changed", "value_not_in_quote/derived_label"]
    check("diagnosis classes on synthetic cells", cls == want, str(cls))
    check("control of control: a swapped class is detected", cls != want[::-1])
    # 3. real run: shifted spans and removed quotes
    real = next((d for d in sorted((ROOT / "work/eval_phage").glob("gemma4-31b-lms_v71_r*")) if (d / "evidence.json").exists()), None)
    if real is None:
        check("real run available", False)
    else:
        data, ev, txt, _ = load_run(real)
        spans = [tuple(e["char_span"]) for e in ev["entries"] if e.get("char_span")]
        base = coverage(txt, spans)["share"]
        shift = len(txt) // 2
        shifted = coverage(txt, [((a + shift) % len(txt), min(len(txt), (a + shift) % len(txt) + (b - a))) for a, b in spans])["share"]
        check("real run: correct spans cover most numbers", base is not None and base >= 0.5, f"coverage {base}")
        # a shift cannot give "near zero": the quote spans cover a large share of the characters, so spans put at a wrong place
        # still hit numbers by chance; the chance level is the share of characters covered (the control must land near it)
        density = sum(b - a for a, b in merge(spans)) / len(txt)
        check("real run: spans shifted to the wrong place fall to about the chance level (character density)",
              shifted < base - 0.25 and abs(shifted - density) < 0.2, f"coverage {base} -> {shifted}, chance level {density:.3f}")
        stripped = [{**{k: v for k, v in e.items() if k not in ("char_span", "line", "passage", "occurrences")}, "quote": "", "status": "missing"}
                    for e in ev["entries"]]
        counts, _, _ = diagnose_cells(stripped, txt)
        check("quotes removed: every cell missing", counts == {"missing": len(stripped)}, str(counts))
        check("quotes removed: coverage 0", coverage(txt, [])["share"] == 0.0)
        # the real run must classify some cells (otherwise the diagnosis is untested on real data)
        counts, _, _ = diagnose_cells(ev["entries"], txt)
        check("real run: classes add up to the cell count", sum(counts.values()) == len(ev["entries"]), str(counts))
        # 4. annotation: no quotes -> every verified annotation cell missed; all text covered -> none missed
        gev = json.loads((real.parent / "annotation_evidence.manual_annotation_b.json").read_text())
        secs = coverage(txt, [])["sections"]
        g_none = annotation_missed(gev, [], secs)
        g_all = annotation_missed(gev, [(0, len(txt))], secs)
        check("annotation: no quote spans -> all verified cells missed", g_none["missed"] == g_none["verified_annotation_cells"] > 0, str(g_none["missed"]))
        check("annotation: whole text covered -> none missed", g_all["missed"] == 0)
    print("CONTROLS PASS" if not fails else f"CONTROLS FAILED: {fails}")
    return not fails


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--control"]:
        sys.exit(0 if control() else 1)
    if not args or args[0].startswith("--"):
        sys.exit(__doc__)
    fb = write_feedback(args[0], "--annotation" in args)
    print(f"{args[0]}/feedback.json: cells {fb['cells']}, classes {fb['cell_classes'] and {k: v['cells'] for k, v in fb['cell_classes'].items()}}, "
          f"coverage {fb['coverage']['share']}" + (f", annotation missed {fb['annotation']['missed']}/{fb['annotation']['verified_annotation_cells']}" if "annotation" in fb else ""))
