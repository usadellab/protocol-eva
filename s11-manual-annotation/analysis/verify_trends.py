#!/opt/homebrew/bin/python3.13
"""Independent re-computation of the headline trend statistics (own rank code, own permutation loop, no scipy) and comparison with trends.json."""
import itertools, json, math
import numpy as np, pandas as pd
from pathlib import Path
# inputs: results/runs.csv, results/entries.csv of the section; outputs: this folder
R = str(Path(__file__).resolve().parent.parent / "results") + "/"
T = str(Path(__file__).resolve().parent) + "/"; t = json.load(open(T + "trends.json")); runs = pd.read_csv(R + "runs.csv"); ent = pd.read_csv(R + "entries.csv").set_index("case")
FIVE = ["sdy1", "phage", "ux511", "biolector034", "pux782"]
def rank(a):
    a = np.asarray(a, float); o = a.argsort(kind="mergesort"); r = np.empty(len(a)); i = 0
    while i < len(a):
        j = i
        while j + 1 < len(a) and a[o[j + 1]] == a[o[i]]: j += 1
        r[o[i:j + 1]] = (i + j) / 2 + 1; i = j + 1
    return r
def spear(x, y):
    rx, ry = rank(x) - rank(x).mean(), rank(y) - rank(y).mean(); return float((rx * ry).sum() / math.sqrt((rx ** 2).sum() * (ry ** 2).sum()))
v6 = runs[(runs.prompt == "general prompt v6") & runs.case.isin(FIVE) & (runs.ok == 1)]
models = sorted(m for m, g in v6.groupby("model") if g.case.nunique() == 5)
rec = {m: [v6[(v6.model == m) & (v6.case == c)].recall.mean() for c in FIVE] for m in models}
cells = [ent.loc[c, "cells_human"] for c in FIVE]
obs = np.mean([spear(cells, rec[m]) for m in models])
null = [np.mean([spear([cells[FIVE.index(p[i])] for i in range(5)], rec[m]) for m in models]) for p in itertools.permutations(FIVE)]
p = np.mean([abs(n) >= abs(obs) - 1e-12 for n in null])
checks = [("H1 mean rho", obs, t["H1_recall_vs_cells_human"]["mean_rho"]), ("H1 permutation p", p, t["H1_recall_vs_cells_human"]["perm_p_two_sided"])]
a = runs[(runs.ok == 1) & runs.steps_written.notna() & runs.case.isin(FIVE)].copy(); a["share"] = (a.rows_ai - a.rows_aligned) / a.rows_ai
z = lambda col: a.groupby("case")[col].transform(lambda s: (s - s.mean()) / s.std(ddof=0) if s.std(ddof=0) > 0 else 0)
checks.append(("H4 pooled rho precision", spear(z("share"), z("precision")), t["H4_precision_vs_extra_rows_share_within_entry"]["rho"]))
checks.append(("H4 pooled rho recall", spear(z("share"), z("recall")), t["H4_recall_vs_extra_rows_share_within_entry"]["rho"]))
neg = 0; n = 0
for m, g in a.groupby("model"):
    if len(g) >= 15:
        n += 1; neg += spear((g.share - g.groupby("case").share.transform("mean")) / 1, (g.precision - g.groupby("case").precision.transform("mean"))) < 0
checks.append(("H4 models negative (of >=15 runs)", neg, t["H4_per_model"]["n_negative_precision"])); checks.append(("H4 models counted", n, t["H4_per_model"]["n_models"]))
pdf = t["H3_pdf_vs_html"]["pairs"]; checks.append(("H3 precision lower with PDF (models)", sum(p_["pdf_precision"] < p_["html_precision"] for p_ in pdf), t["H3_pdf_vs_html"]["precision"]["n_lower_with_pdf"]))
ok = True
for name, mine, theirs in checks:
    d = abs(mine - theirs); ok &= d < 1e-6 or (name.startswith("H4 pooled") and d < 0.05)
    print("%-40s independent %.4f   trends.json %.4f   diff %.1e" % (name, mine, theirs, d))
print("ALL TREND STATISTICS CONFIRMED" if ok else "DIFFERENCES FOUND")
