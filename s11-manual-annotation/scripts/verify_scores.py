#!/opt/homebrew/bin/python3.13
"""Independent re-implementation of the column-distinct score, written from the specification in
28_score_extraction.py's docstring (no code shared; only case/prediction/annotation paths are taken from 28).
Every stored score in the three scores.json files must be reproduced exactly: column-distinct and record F1
(record: rows as bags of facts, one-to-one row assignment maximising matched cells, TP = cells matched inside
the assigned pairs; failed runs must be stored as 0 over the full annotation count).

Spec: each distinct (cell, unit) of a Characteristic/Parameter/Factor/Comment/Date column is ONE fact. Normalised
form = tokens: ISO dates, canonical numbers, "-" between two numbers, lower-case words, punctuation dropped.
Lint form (only if the cell has a duration or a number with a known unit, inline or as the column unit of a
single-number cell): same tokens after durations -> hours and number+unit -> base-unit value + dimension.
Match: (1) identical normalised cell unless both lint forms exist and differ, (2) leftovers by lint form,
(3) leading quantity: one cell is exactly one quantity with a unit or a date, the other starts with it.
Tokens glueing letters and digits are identifiers, not numbers. Codes in digit groups ("97 613 732") are joined.
Maximum one-to-one matching (here: Hungarian method).
Hash cells skipped. P = TP/predicted, R = TP/annotation, F1 = 2PR/(P+R)."""
import functools, importlib.util, json, multiprocessing, os, re, sys
from collections import Counter
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parents[1]                  # root of the section; the run folders (work/eval*/) are not part of it
F = {"l": ("vol", 1), "ml": ("vol", 1e-3), "µl": ("vol", 1e-6), "ul": ("vol", 1e-6), "μl": ("vol", 1e-6),
     "microliter": ("vol", 1e-6), "milliliter": ("vol", 1e-3), "h": ("time", 1), "hr": ("time", 1), "hrs": ("time", 1),
     "hour": ("time", 1), "hours": ("time", 1), "min": ("time", 1 / 60), "mins": ("time", 1 / 60), "minute": ("time", 1 / 60),
     "minutes": ("time", 1 / 60), "sec": ("time", 1 / 3600), "s": ("time", 1 / 3600), "second": ("time", 1 / 3600),
     "m": ("mol", 1), "mm": ("mol", 1e-3), "µm": ("mol", 1e-6), "um": ("mol", 1e-6), "nm": ("mol", 1e-9),
     "millimolar": ("mol", 1e-3), "micromolar": ("mol", 1e-6), "nanomolar": ("mol", 1e-9), "g": ("mass", 1),
     "mg": ("mass", 1e-3), "µg": ("mass", 1e-6), "ug": ("mass", 1e-6), "ng": ("mass", 1e-9), "gram": ("mass", 1),
     "nanogram": ("mass", 1e-9), "microgram": ("mass", 1e-6), "mg/ml": ("mconc", 1), "µg/ml": ("mconc", 1e-3),
     "ug/ml": ("mconc", 1e-3), "ng/µl": ("mconc", 1e-3), "ng/ul": ("mconc", 1e-3), "g/l": ("mconc", 1),
     "microgram per milliliter": ("mconc", 1e-3), "milligram per milliliter": ("mconc", 1), "nanogram per microliter": ("mconc", 1e-3),
     "°c": ("temp", 1), "degree celsius": ("temp", 1), "rpm": ("rpm", 1)}
F.update({k.replace("\u00b5", "\u03bc"): v for k, v in F.items() if "\u00b5" in k})   # Greek mu: re.I makes it match the micro sign
ALT = "|".join(sorted(map(re.escape, F), key=len, reverse=True))


def cnum(t):
    return f"{float(t.replace(',', '.')):.10f}".rstrip("0").rstrip(".") or "0"


def norm(text):
    if re.fullmatch(r"\s*\d{1,3}(?: \d{3})+\s*", text): text = text.replace(" ", "")
    dates = []
    def iso(m):
        if m.group(1): y, mo, d = m.group(1), m.group(2), m.group(3)
        else: d, mo, y = m.group(4), m.group(5), m.group(6); y = y if len(y) == 4 else "20" + y
        dates.append(f"{y}-{int(mo):02d}-{int(d):02d}"); return f" @{len(dates) - 1}@ "
    t = re.sub(r"\b(\d{4})-(\d{2})-(\d{2})\b|\b(\d{1,2})[./](\d{1,2})[./](\d{2}|\d{4})\b", iso, text).lower()
    t = re.sub(r"(?<=\d)\s*[-–]\s*(?=\d)", " § ", t)       # § = range marker; a literal "~" ("approximately") is dropped, as in 28
    toks = []
    for tok in re.findall(r"@\d+@|§|[a-z0-9äöüßµμ°%]+(?:[.,]\d+)?", t):
        toks.append(dates[int(tok[1:-1])] if tok.startswith("@") else "-" if tok == "§"
                    else cnum(tok) if re.fullmatch(r"\d+(?:[.,]\d+)?", tok) else tok)
    return " ".join(toks)


def lint2(v, u):
    s = re.sub(r"(\d+)\s*(?:h|hrs?|hours?)\s*(\d+)\s*(?:min|mins|minutes?)(?![a-zA-Z])",
               lambda m: format(int(m.group(1)) + int(m.group(2)) / 60, ".12g") + " h", v, flags=re.I)
    if u and re.fullmatch(r"\s*\d+(?:[.,]\d+)?\s*", s): s = s + " " + u
    return re.sub(rf"(\d+(?:[.,]\d+)?)\s*({ALT})(?![a-zA-Z])",
                  lambda m: format(float(m.group(1).replace(",", ".")) * F[m.group(2).lower()][1], ".12g") + " " + F[m.group(2).lower()][0],
                  s, flags=re.I)


def fact(v, u):
    v = str(v).strip()
    if not v or re.fullmatch(r"(sha256:\s*)?[0-9a-fA-F]{32,}", v): return None
    n = norm(v)
    if not n: return None
    u = str(u or "").strip()
    lv = lint2(v, u if u.lower() in F else "")
    return (n, norm(lv) if lv != v else None)


def facts(x):
    wb = openpyxl.load_workbook(x, read_only=True); c = Counter()
    for sh in wb.sheetnames:
        if sh == "isa_assay": continue
        rows = list(wb[sh].iter_rows(values_only=True))
        if len(rows) < 2: continue
        hd = [str(v or "").strip() for v in rows[0]]
        for j, h in enumerate(hd):
            if not re.match(r"^(Characteristic|Parameter|Factor|Comment)\b|^Date$", h): continue
            hu = j + 1 < len(hd) and hd[j + 1] == "Unit"
            for v, u in {(str(r[j]) if j < len(r) and r[j] is not None else "", str((r[j + 1] or "") if hu and j + 1 < len(r) else "")) for r in rows[1:]}:
                f = fact(v, u)
                if f: c[f] += 1
    return c


NUMRX = re.compile(r"\d+(?:\.\d+)?")
DATERX = re.compile(r"\d{4}-\d{2}-\d{2}")
DIMS = ("vol", "time", "mol", "mass", "mconc", "temp", "rpm")


def qs(cell):
    t, out, k = cell.split(), [], 0
    while k < len(t):
        if DATERX.fullmatch(t[k]): out.append((t[k], "date")); k += 1; continue
        if NUMRX.fullmatch(t[k]):
            if k + 2 < len(t) and t[k + 1] == "-" and NUMRX.fullmatch(t[k + 2]): out.append((t[k] + "-" + t[k + 2], "")); k += 3; continue
            d = t[k + 1] if k + 1 < len(t) and t[k + 1] in DIMS else ""
            out.append((t[k], d)); k += 2 if d else 1; continue
        k += 1
    return out


def lead(a, b):  # a is exactly one quantity with a unit or a date; b starts with it
    ca, cb = a[1] or a[0], b[1] or b[0]
    qa = qs(ca)
    if len(qa) != 1 or not qa[0][1]: return False
    if not all(NUMRX.fullmatch(x) or DATERX.fullmatch(x) or x in DIMS for x in ca.split()): return False
    tb, qb = cb.split(), qs(cb)
    return bool(tb and qb and (NUMRX.fullmatch(tb[0]) or DATERX.fullmatch(tb[0])) and qb[0] == qa[0])


def ok(pk, gk):
    if pk[0] == gk[0] and (pk[1] is None or gk[1] is None or pk[1] == gk[1]): return True
    if pk[1] is not None and pk[1] == gk[1]: return True
    return lead(pk, gk) or lead(gk, pk)


def match(p, g):
    """Maximum matching by the Hungarian method (scipy), a different algorithm from 28's augmenting paths."""
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    pn = [k for k, n in p.items() for _ in range(n)]; gn = [k for k, n in g.items() for _ in range(n)]
    pk_u, gk_u = list(p), list(g)
    comp = {(a, b): ok(a, b) for a in pk_u for b in gk_u}
    cost = np.array([[0 if comp[(a, b)] else 1 for b in gn] for a in pn], dtype=np.int8)
    r, c = linear_sum_assignment(cost)
    return int(sum(1 for i, j in zip(r, c) if cost[i, j] == 0))


def recs(x):
    """Rows of every sheet except isa_assay as Counters of facts (constants included; empty rows skipped)."""
    wb = openpyxl.load_workbook(x, read_only=True); out = []
    for sh in wb.sheetnames:
        if sh == "isa_assay": continue
        rows = list(wb[sh].iter_rows(values_only=True))
        if len(rows) < 2: continue
        hd = [str(v or "").strip() for v in rows[0]]
        cols = [(j, j + 1 < len(hd) and hd[j + 1] == "Unit") for j, h in enumerate(hd)
                if re.match(r"^(Characteristic|Parameter|Factor|Comment)\b|^Date$", h)]
        for r in rows[1:]:
            c = Counter(f for j, hu in cols if (f := fact(str(r[j]) if j < len(r) and r[j] is not None else "",
                                                          str((r[j + 1] or "") if hu and j + 1 < len(r) else ""))))
            if c: out.append(c)
    return out


def record_tp(P, G):
    """Record TP: Hungarian assignment of rows maximising per-pair matched cells (each pair by match())."""
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    w = np.zeros((len(P), len(G)), dtype=np.int64)
    for i, p in enumerate(P):
        for j, g in enumerate(G):
            if any(ok(a, b) for a in p for b in g):
                w[i, j] = match(p, g)
    r, c = linear_sum_assignment(w, maximize=True)
    return int(w[r, c].sum())


# Speed: the checks of the single scores are independent of each other, so they run in a pool of worker processes (one task = one stored score); the facts and rows of the annotation
# are read once per worker, not once per run; the compatibility of two facts is computed once per run (ok() is a pure function). The result of every check is the same as in the serial form.
ANNOTATION_CACHE = {}


def annotation_facts(path):
    if path not in ANNOTATION_CACHE: ANNOTATION_CACHE[path] = facts(path)
    return ANNOTATION_CACHE[path]


def annotation_recs(path):
    if ("r", path) not in ANNOTATION_CACHE: ANNOTATION_CACHE[("r", path)] = recs(path)
    return ANNOTATION_CACHE[("r", path)]


def check(task):
    """One stored score -> (worst difference, list of MISMATCH lines)."""
    case, key, v, pred_path, annotation_path = task
    ok.cache_clear()
    lines, worst = [], 0.0
    if v.get("status", "ok") != "ok":            # a failed run must be stored as 0 over the full annotation count
        G, m = annotation_facts(annotation_path), v["column-distinct"]["all"]
        d = m["tp"] + m["predicted"] + m["f1"] + abs(sum(G.values()) - m["annotation"])
        worst = max(worst, d)
        rg = sum(sum(c.values()) for c in annotation_recs(annotation_path))
        d += v["record"]["all"]["tp"] + v["record"]["all"]["predicted"] + abs(rg - v["record"]["all"]["annotation"])
        worst = max(worst, d)
        if d:
            lines.append(f"MISMATCH {case} {key}: failed run not stored as 0 / {sum(G.values())}")
        return worst, lines
    P, G = facts(pred_path), annotation_facts(annotation_path)
    tp, np_, ng = match(P, G), sum(P.values()), sum(G.values())
    pr, rc = tp / np_, tp / ng; f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
    m = v["column-distinct"]["all"]
    d = max(abs(pr - m["precision"]), abs(rc - m["recall"]), abs(f1 - m["f1"])) + abs(tp - m["tp"]) + abs(np_ - m["predicted"]) + abs(ng - m["annotation"])
    ident = abs(m["f1"] - 2 * m["tp"] / (m["predicted"] + m["annotation"]))
    worst = max(worst, d, ident)
    if d > 1e-9 or ident > 1e-9:
        lines.append(f"MISMATCH {case} {key}: independent {tp}/{np_}/{ng} F1 {f1:.4f} vs stored {m['tp']}/{m['predicted']}/{m['annotation']} F1 {m['f1']:.4f}")
    RP, RG, mr = recs(pred_path), annotation_recs(annotation_path), v["record"]["all"]
    rtp, rnp, rng = record_tp(RP, RG), sum(sum(c.values()) for c in RP), sum(sum(c.values()) for c in RG)
    rd = abs(rtp - mr["tp"]) + abs(rnp - mr["predicted"]) + abs(rng - mr["annotation"])
    worst = max(worst, rd)
    if rd:
        lines.append(f"MISMATCH record {case} {key}: independent {rtp}/{rnp}/{rng} vs stored {mr['tp']}/{mr['predicted']}/{mr['annotation']}")
    return worst, lines


CASE_FILES = (("phage", "work/eval_phage/scores.json"), ("sdy1", "work/eval_sdy1/scores.json"),
              ("biolector034", "work/eval_biolector034/scores.json"), ("ux511", "work/eval_ux511/scores.json"),
              ("sdy1_pdfinput", "work/eval_sdy1_pdfinput/scores.json"), ("pux782", "work/eval_pux782/scores.json"))
ok = functools.lru_cache(maxsize=None)(ok)


if __name__ == "__main__":
    only = [a for a in sys.argv[1:] if not a.startswith("-")]                    # optional: the cases to verify (default: all)
    workers = int(os.environ.get("VERIFY_WORKERS", os.cpu_count() or 1))
    worst = 0.0
    for case, scores in CASE_FILES:
        if only and case not in only:
            continue
        spec = importlib.util.spec_from_file_location("s", ROOT / "scripts/28_score_extraction.py")
        sys.argv = ["x", case]; S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
        paths = dict(S.PREDICTIONS); paths.update({f"annotation {g} (reference)": p for g, p in S.ANNOTATIONS.items()})
        stored = json.load(open(ROOT / scores))
        tasks = []
        for key, v in stored.items():
            label, g = key.split(" | vs ")
            tasks.append((case, key, v, paths.get(label), S.ANNOTATIONS[g]))
        tasks.sort(key=lambda t: -(t[3].stat().st_size if t[3] and t[3].exists() else 0))                  # the large answers first
        with multiprocessing.get_context("fork").Pool(min(workers, len(tasks))) as pool:
            results = pool.map(check, tasks, chunksize=1)
        for (w, lines), task in sorted(zip(results, tasks), key=lambda r: r[1][1]):
            worst = max(worst, w)
            for line in lines:
                print(line)
        print(f"{case}: {len(stored)} scores re-computed independently")
    print("ALL SCORES VERIFIED" if worst < 1e-9 else f"DIFFERENCES FOUND (max {worst})")
    sys.exit(0 if worst < 1e-9 else 1)
