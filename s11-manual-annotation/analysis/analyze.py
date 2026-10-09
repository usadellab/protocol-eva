#!/opt/homebrew/bin/python3.13
"""Trend statistics for the supplement -> trends.json (this folder).   Population: v6, text-only, manual annotation B, five entries (+ the PDF-text version of the spot assay for the format test).
Every test is stated before it is run; exact permutation tests where the number of entries is small (5 entries = 120 permutations)."""
import itertools, json, math
import numpy as np, pandas as pd
from scipy import stats
from pathlib import Path
# inputs: results/runs.csv, results/entries.csv of the section; outputs: this folder
R = str(Path(__file__).resolve().parent.parent / "results") + "/"
T = str(Path(__file__).resolve().parent) + "/"
runs = pd.read_csv(R + "runs.csv"); ent = pd.read_csv(R + "entries.csv").set_index("case")
FIVE = ["sdy1", "phage", "ux511", "biolector034", "pux782"]
v6 = runs[(runs.prompt == "general prompt v6") & runs.case.isin(FIVE)].copy()
out = {"n_runs_v6": int(len(v6)), "n_failed_v6": int((v6.ok == 0).sum())}
ok = v6[v6.ok == 1]
# ---------------- H1: the more cells the manual annotation has (= the more the model has to write), the lower the recall
models_full = [m for m, g in ok.groupby("model") if g.case.nunique() == 5]
def per_model_rho(measure, metric, data=ok, entries=FIVE, perm=None):
    rhos = []
    for m in models_full:
        g = data[data.model == m].groupby("case")[metric].mean().reindex(entries)
        x = [measure[c] for c in entries] if perm is None else [measure[perm[i]] for i in range(len(entries))]
        rhos.append(stats.spearmanr(x, g.values).statistic)
    return np.array(rhos)
def perm_test(measure, metric, data=ok):
    obs = per_model_rho(measure, metric, data); mean_obs = obs.mean()
    null = [per_model_rho(measure, metric, data, perm=list(p)).mean() for p in itertools.permutations(FIVE)]
    p_two = float(np.mean([abs(n) >= abs(mean_obs) - 1e-12 for n in null]))
    return {"mean_rho": float(mean_obs), "models": len(obs), "n_negative": int((obs < 0).sum()), "perm_p_two_sided": p_two, "per_model": {m: float(r) for m, r in zip(models_full, obs)}}
cells_human = ent.cells_human.to_dict(); words = ent.input_words.to_dict(); tables = ent.tables_human.to_dict(); chars = ent.input_chars.to_dict()
out["measures"] = {c: {"cells_human": int(cells_human[c]), "input_words": int(words[c]), "tables_human": int(tables[c]), "input_chars": int(ent.input_chars[c]), "rows_human": int(ent.rows_human[c])} for c in FIVE}
out["H1_recall_vs_cells_human"] = perm_test(cells_human, "recall")
out["H1_recall_vs_input_words"] = perm_test(words, "recall")
out["H1_recall_vs_input_chars"] = perm_test(chars, "recall")
out["H1_recall_vs_tables_human"] = perm_test(tables, "recall")
out["H1_f1_vs_cells_human"] = perm_test(cells_human, "f1")
out["H1_precision_vs_cells_human"] = perm_test(cells_human, "precision")
# the mechanism: models write about the same number of cells whatever the size -> coverage = predicted/annotation falls
cov = ok.assign(coverage=ok.cells_ai / ok.cells_human).groupby("case").coverage.median().reindex(FIVE)
out["cells_ai_over_cells_human_median"] = {c: float(v) for c, v in cov.items()}
pred_med = ok.groupby("case").cells_ai.median().reindex(FIVE)
out["cells_ai_median"] = {c: float(v) for c, v in pred_med.items()}
# run level: log(recall odds) ~ log(annotation cells) + model fixed effects, p by permuting the entry labels (the entries are the units)
def run_level_slope(data):
    d = data.copy(); d["x"] = np.log(d.case.map(cells_human)); d["y"] = d.recall
    X = pd.get_dummies(d.model, drop_first=True).astype(float); X["x"] = d.x; X["c"] = 1.0
    beta = np.linalg.lstsq(X.values, d.y.values, rcond=None)[0]; return beta[list(X.columns).index("x")]
d_ok = ok[ok.model.isin(models_full)]
slope = run_level_slope(d_ok)
null = []
for p in itertools.permutations(FIVE):
    mp = dict(zip(FIVE, p)); dd = d_ok.copy(); dd["case_perm"] = dd.case.map(mp)
    d2 = dd.copy(); d2["x"] = np.log(d2.case_perm.map(cells_human)); X = pd.get_dummies(d2.model, drop_first=True).astype(float); X["x"] = d2.x; X["c"] = 1.0
    null.append(np.linalg.lstsq(X.values, d2.recall.values, rcond=None)[0][list(X.columns).index("x")])
out["H1_run_level"] = {"slope_recall_per_ln_cell": float(slope), "recall_change_per_doubling": float(slope * math.log(2)), "n_runs": int(len(d_ok)), "perm_p_two_sided": float(np.mean([abs(n) >= abs(slope) - 1e-12 for n in null]))}
# failed runs vs size
fl = v6[v6.model.isin(models_full + list(v6.model.unique()))].groupby("case").apply(lambda g: float((g.ok == 0).mean()), include_groups=False).reindex(FIVE)
out["failed_share_by_entry"] = {c: float(v) for c, v in fl.items()}
out["failed_vs_cells_human_spearman"] = {"rho": float(stats.spearmanr([cells_human[c] for c in FIVE], fl.values).statistic)}
# ---------------- H2: short, well-structured entries score better (entry level)
by_entry = ok.groupby("case").agg(f1=("f1", "mean"), precision=("precision", "mean"), recall=("recall", "mean")).reindex(FIVE)
out["entry_means"] = {c: {k: float(v) for k, v in r.items()} for c, r in by_entry.iterrows()}
out["H2_entry_f1_rank_vs_cells_human_spearman"] = {"rho": float(stats.spearmanr([cells_human[c] for c in FIVE], by_entry.f1.values).statistic), "n_entries": 5, "exact_two_sided_p_if_|rho|=1": 2 / 120}
out["H2_entry_f1_vs_ref_tables_spearman"] = {"rho": float(stats.spearmanr([tables[c] for c in FIVE], by_entry.f1.values).statistic)}
# ---------------- H3: wrong input format (text extracted from the PDF instead of the HTML) lowers precision? paired by model
pdf = runs[(runs.prompt == "general prompt v6") & (runs.case == "sdy1_pdfinput") & (runs.ok == 1)]
html = runs[(runs.prompt == "general prompt v6") & (runs.case == "sdy1") & (runs.ok == 1)]
pairs = []
for m in sorted(set(pdf.model) & set(html.model)):
    a, b = html[html.model == m], pdf[pdf.model == m]
    pairs.append({"model": m, **{f"html_{k}": float(a[k].mean()) for k in ("precision", "recall", "f1")}, **{f"pdf_{k}": float(b[k].mean()) for k in ("precision", "recall", "f1")}, "n_html": int(len(a)), "n_pdf": int(len(b))})
pp = pd.DataFrame(pairs)
def wil(a, b):
    d = np.array(a) - np.array(b)
    return {"mean_change": float(np.mean(np.array(b) - np.array(a))), "n_models": int(len(d)), "n_lower_with_pdf": int((d > 0).sum()), "wilcoxon_p_two_sided": float(stats.wilcoxon(a, b).pvalue) if len(d) > 5 and np.any(d != 0) else None}
if len(pp):
    out["H3_pdf_vs_html"] = {"precision": wil(pp.html_precision, pp.pdf_precision), "recall": wil(pp.html_recall, pp.pdf_recall), "f1": wil(pp.html_f1, pp.pdf_f1), "pairs": pairs}
# ---------------- H4: wrong structure of the answer (extra protocol steps / extra rows) lowers precision (all prompts, all models; within entry standardised)
allrun = runs[(runs.ok == 1) & runs.steps_written.notna() & runs.case.isin(FIVE)].copy()
allrun["extra_steps"] = allrun.steps_written - allrun.tables_human
allrun["extra_rows_share"] = (allrun.rows_ai - allrun.rows_aligned) / allrun.rows_ai
for col in ("precision", "recall", "f1", "extra_steps", "extra_rows_share"):
    allrun["z_" + col] = allrun.groupby("case")[col].transform(lambda s: (s - s.mean()) / s.std(ddof=0) if s.std(ddof=0) > 0 else 0)
def corr(x, y, data):
    r = stats.spearmanr(data[x], data[y]); return {"rho": float(r.statistic), "p": float(r.pvalue), "n": int(len(data))}
out["H4_precision_vs_extra_steps_within_entry"] = corr("z_extra_steps", "z_precision", allrun)
out["H4_recall_vs_extra_steps_within_entry"] = corr("z_extra_steps", "z_recall", allrun)
out["H4_precision_vs_extra_rows_share_within_entry"] = corr("z_extra_rows_share", "z_precision", allrun)
out["H4_recall_vs_extra_rows_share_within_entry"] = corr("z_extra_rows_share", "z_recall", allrun)
op = allrun[allrun.model.isin(["Claude Opus", "Claude Sonnet 5.5"])]
out["H4_opus_sonnet_precision_vs_extra_steps"] = corr("z_extra_steps", "z_precision", op)

# robustness of H4: one correlation per model (runs of one model are not independent of each other), then a sign test over the models
per = []
for m, g in allrun.groupby("model"):
    if len(g) >= 15:
        r1 = stats.spearmanr(g.z_extra_rows_share, g.z_precision); r2 = stats.spearmanr(g.z_extra_rows_share, g.z_recall)
        per.append({"model": m, "n_runs": int(len(g)), "rho_precision": float(r1.statistic), "rho_recall": float(r2.statistic)})
neg = sum(1 for x in per if x["rho_precision"] < 0)
out["H4_per_model"] = {"models": per, "n_models": len(per), "n_negative_precision": neg, "sign_test_p_two_sided": float(stats.binomtest(neg, len(per), 0.5).pvalue) if per else None,
                       "mean_rho_precision": float(np.mean([x["rho_precision"] for x in per])) if per else None, "mean_rho_recall": float(np.mean([x["rho_recall"] for x in per])) if per else None}
# cluster bootstrap over models for the pooled correlation
rng = np.random.default_rng(1); ms = list(allrun.model.unique()); bs = []
for _ in range(2000):
    pick = rng.choice(ms, len(ms)); d = pd.concat([allrun[allrun.model == m] for m in pick])
    bs.append(stats.spearmanr(d.z_extra_rows_share, d.z_precision).statistic)
out["H4_pooled_rho_bootstrap_over_models_95ci"] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
# failed (truncated or invalid) answers: score 0 for both -> they pull precision AND recall down equally; share of failed runs by route
allv6 = runs[runs.prompt == "general prompt v6"]
out["failed_share_all_v6_runs"] = float((allv6.ok == 0).mean())
json.dump(out, open(T + "trends.json", "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k.startswith(("H", "failed", "coverage", "predicted", "entry"))}, indent=1)[:6000])
