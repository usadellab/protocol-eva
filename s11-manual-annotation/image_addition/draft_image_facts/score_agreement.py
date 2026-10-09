#!/opt/homebrew/bin/python3.13
"""Agreement of the draft (image_facts_draft_by_claude.json) with the two independent readings R2 (fresh Sonnet subagent) and R3 (claude -p haiku).
Lexical, per fact: printed facts (label, mark, legend, axis, value; kind != observation/layout/colour-code) are 'supported' by a reader when >= 0.8 of the
tokens (letter runs and digit runs) of the fact's value occur in the reader's text. Colour-coded clone numbers: the sequence of colours (green vs other) of the reader's
colour_coded list against the draft's, per blot. Observations (approximate band/growth/curve statements) are NOT scored automatically.
Also checks the colour-code facts against annotation B (curator) of UX511 (`work/eval_ux511/annotation_evidence.manual_annotation_b.json`): used only as an external check, never as input.
Output: image_facts_agreement.json and .md"""
import collections, json, re, sys
from pathlib import Path
here = Path(__file__).parent
ROOT = here.parents[1]                                   # root of the section s11-manual-annotation
draft = json.loads((here / "image_facts_draft_by_claude.json").read_text())["facts"]
tok = lambda s: re.findall(r"[a-z]+|\d+", s.lower().replace("µ", "u").replace("μ", "u"))

def strings(o):
    if isinstance(o, str): yield o
    elif isinstance(o, dict):
        for v in o.values(): yield from strings(v)
    elif isinstance(o, list):
        for v in o: yield from strings(v)

def parse_json(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    return json.loads(m.group(0)) if m else None

readers = {}
readers["R2_sonnet_subagent"] = {o["figure"]: o for o in json.loads((here / "reading_R2_subagent_sonnet.json").read_text())}
r3 = json.loads((here / "reading_R3_haiku.json").read_text())
readers["R3_haiku_cli"] = {}
for fig, v in r3.items():
    try: readers["R3_haiku_cli"][fig] = parse_json(v["answer"])
    except Exception: readers["R3_haiku_cli"][fig] = None

def colour_seq(o):
    seq = []
    for e in (o or {}).get("colour_coded", []) or []:
        t = str(e.get("text", "")).strip()
        if re.search(r"\d+$", t) and not re.match(r"uma", t, re.I): seq.append(1 if "green" in str(e.get("colour", "")).lower() else 0)
    return seq

res = collections.OrderedDict()
for f in draft:
    res.setdefault(f["figure"], {"printed": [], "obs": 0, "layout": 0})
    r = res[f["figure"]]
    if f["kind"] == "observation": r["obs"] += 1
    elif f["kind"] in ("layout",): r["layout"] += 1
    elif f["kind"] == "colour-code": pass
    elif f["attribute"] == "clone number": pass
    else: r["printed"].append(f)
rows = []
for fig, r in res.items():
    row = {"figure": fig, "n_facts": sum(1 for f in draft if f["figure"] == fig), "printed": len(r["printed"]), "observations": r["obs"], "layout": r["layout"]}
    mine = [1 if f["value"].startswith("yes") else 0 for f in draft if f["figure"] == fig and f["attribute"] == "marked as correct on blot image" and not f["locator"].startswith("UMa")]
    row["colour_n"] = len(mine)
    for name, rd in readers.items():
        o = rd.get(fig)
        bag = set(tok(" ".join(strings(o)))) if o else set()
        ok = [f for f in r["printed"] if (lambda t: t and sum(x in bag for x in t) / len(t) >= 0.8)(tok(f["value"]))]
        row[name] = {"printed_supported": len(ok), "printed_missed": [f["id"] + " " + f["value"][:40] for f in r["printed"] if f not in ok][:6]}
        if mine:
            seq = colour_seq(o)
            row[name]["colour_sequence_equal"] = seq == mine
            row[name]["colour_positions_agree"] = sum(a == b for a, b in zip(seq, mine)) if len(seq) == len(mine) else None
            row[name]["reader_colour_n"] = len(seq)
    both = [f for f in r["printed"] if all((lambda t: t and sum(x in set(tok(" ".join(strings(rd.get(fig))))) for x in t) / len(t) >= 0.8)(tok(f["value"])) for rd in readers.values())]
    row["printed_supported_by_both"] = len(both)
    rows.append(row)
# external check of the draft's colour codes against annotation B (UX511)
import openpyxl
sheet = list(openpyxl.load_workbook(ROOT / "datasets/manual_annotations/ux511_manual_annotation_B_curator.xlsx", read_only=True)["Southern_blot"].iter_rows(values_only=True))
cells = collections.defaultdict(dict)
for i, row in enumerate(sheet[1:], start=2):
    for head, value in zip(sheet[0], row):
        if head and value not in (None, ""): cells[i][head] = str(value)
B = collections.defaultdict(set)
for cols in cells.values():
    if cols.get("Comment [lane]") and cols.get("Comment [marked as correct on blot image]"): B[cols["Comment [lane]"]].add(cols["Comment [marked as correct on blot image]"])
mine = collections.defaultdict(set)
for f in draft:
    m = re.match(r"(UX\d+) clone (\d+)", f["locator"])
    if f["attribute"] == "marked as correct on blot image" and m: mine[f"{m.group(1)} clone {m.group(2)}"].add(f["value"].split()[0])
agree = [k for k in B if mine.get(k) == B[k]]
ext = {"lanes_in_B_with_marking": len(B), "agree": len(agree), "disagree": sorted(k for k in B if mine.get(k) != B[k])}
(here / "image_facts_agreement.json").write_text(json.dumps({"rows": rows, "external_check_B_colour": ext}, indent=1, ensure_ascii=False))
L = ["# Agreement of the draft image facts with two independent readings (2026-10-06)", "",
     "Draft: `image_facts_draft_by_claude.json` (read by Claude, Sonnet 5.5, this window). R2: a fresh Sonnet subagent that saw only the 13 images and a generic extraction schema (no draft, no annotation, no text of the entries). R3: `claude -p --model haiku`, one call per image, same schema. Lexical rule and limits: see the header of `score_agreement.py`. **Observation facts (band/growth/curve statements, medium confidence) are not scored automatically.**", "",
     "| Figure | facts | printed (scored) | R2 supports | R3 supports | both | observations | colour sequence R2 / R3 |", "|---|---|---|---|---|---|---|---|"]
tot = collections.Counter()
for r in rows:
    c2, c3 = r["R2_sonnet_subagent"], r["R3_haiku_cli"]
    col = "-" if not r["colour_n"] else f"{'=' if c2.get('colour_sequence_equal') else 'differs (' + str(c2.get('reader_colour_n')) + ' read)'} / {'=' if c3.get('colour_sequence_equal') else 'differs (' + str(c3.get('reader_colour_n')) + ' read)'}"
    L.append(f"| {r['figure']} | {r['n_facts']} | {r['printed']} | {c2['printed_supported']} | {c3['printed_supported']} | {r['printed_supported_by_both']} | {r['observations']} | {col} |")
    tot.update(printed=r["printed"], r2=c2["printed_supported"], r3=c3["printed_supported"], both=r["printed_supported_by_both"], obs=r["observations"], facts=r["n_facts"])
L.append(f"| **all** | {tot['facts']} | {tot['printed']} | {tot['r2']} ({tot['r2']/tot['printed']:.0%}) | {tot['r3']} ({tot['r3']/tot['printed']:.0%}) | {tot['both']} ({tot['both']/tot['printed']:.0%}) | {tot['obs']} | |")
L += ["", f"External check of the draft's blot colour codes against annotation B (curator, UX511): {ext['agree']} of {ext['lanes_in_B_with_marking']} lanes that B marks yes/no agree" + (f"; differing: {', '.join(ext['disagree'])}" if ext["disagree"] else "") + ".", "",
      "## Printed facts the readers did not support (first 6 per figure and reader)", ""]
for r in rows:
    for name in readers:
        if r[name]["printed_missed"]: L.append(f"- {r['figure']} {name}: " + "; ".join(r[name]["printed_missed"]))
L += ["", "## Observations (hand comparison, not scored)", "",
      "The 49 draft observations (band positions against the markers, growth by plate, curve levels; confidence medium, all 'approximate') were compared by hand with the observations of R2 (`reading_R2_subagent_sonnet.json`). No contradiction was found; R2 lists 2-5 observations per figure, so most draft observations are simply not mentioned by it. Points where R2 says something the draft does not: UX523 lane 8 on the repeat blot (3acf4cbb) has bands near 10000 and 8000 bp; UX512 lane 3 on bc82c478 shows no clear band; UX517 lane 1 on 6fed9d0a shows no clear band; pUX784 is slightly lower than pUX783 on the digest gel 76a1dde7. These are candidates for the reviewer. R3 (haiku) observations were not compared in detail: R3 (haiku) reproduced the colour code on none of the 5 blots (lane-by-lane agreement with the draft: 10 of 12, 5 of 10, 7 of 9 and 2 of 4 lanes on the four blots where it listed the same number of lanes; on 6fed9d0a it listed 9 of 12 lanes), so its observations are the weakest reading; R2 reproduced the colour sequence on all 5.",
      "", "## Limits", "",
      "- All three readers are Claude models; the agreement says that the printed text and the colour codes are reproducible, not that a human curator would agree. The one independent check (annotation B, 44 of 44 lanes) concerns only the green/black codes of UX511.",
      "- Lexical support is lenient for short values (a bare number such as 800 is supported when it occurs anywhere in a reader's answer).",
      "- R2 is a fresh subagent of the same model family as the draft; it was told nothing but the schema and the paths."]
(here / "image_facts_agreement.md").write_text("\n".join(L) + "\n")
print("\n".join(L[:22]))
