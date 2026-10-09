#!/opt/homebrew/bin/python3.13
"""Trend analysis figure (five panels) from results/runs.csv, results/entries.csv and trends.json -> fig_trends.png (this folder)."""
import json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from pathlib import Path
# inputs: results/runs.csv, results/entries.csv of the section; outputs: this folder
R = str(Path(__file__).resolve().parent.parent / "results") + "/"
T = str(Path(__file__).resolve().parent) + "/"
runs = pd.read_csv(R + "runs.csv"); ent = pd.read_csv(R + "entries.csv").set_index("case"); t = json.load(open(T + "trends.json"))
FIVE = ["sdy1", "phage", "ux511", "biolector034", "pux782"]
NAME = {"sdy1": "Spot assay", "phage": "Bacteriophage\nsequencing", "ux511": "Strain\ngeneration", "biolector034": "BioLector\ncultivation", "pux782": "Plasmid\ngeneration"}
SHORT = {"sdy1": "Spot\nassay", "phage": "Phage", "ux511": "Strain\ngen.", "biolector034": "BioLector", "pux782": "Plasmid\ngen."}
COL = {"sdy1": "#0072B2", "phage": "#009E73", "ux511": "#D55E00", "biolector034": "#CC79A7", "pux782": "#E69F00"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 9, "axes.titleweight": "bold"})
v6 = runs[(runs.prompt == "general prompt v6") & runs.case.isin(FIVE) & (runs.ok == 1)]
order = sorted(FIVE, key=lambda c: ent.loc[c, "cells_human"])
fig = plt.figure(figsize=(13, 9.4)); gs = GridSpec(2, 12, figure=fig, hspace=0.5, wspace=2.2, height_ratios=[1.1, 1])
# (a) scores per entry (solid bars) and three entry attributes (hatched bars, each scaled to its maximum, true value printed on the bar)
ax = fig.add_subplot(gs[0, 0:5]); x = np.arange(len(order)); w = 0.135
m = v6.groupby("case")[["precision", "recall", "f1"]].mean().reindex(order)
mm = t["measures"]; cov = t["cells_ai_over_cells_human_median"]
attrs = [("Cell human", [mm[c]["cells_human"] for c in order], lambda v: f"{int(v):,}", "#7f4f9e"), ("Characters of the input text", [mm[c]["input_chars"] for c in order], lambda v: f"{int(v):,}", "#8c8c8c"),
         ("Cell AI / cell human", [cov[c] for c in order], lambda v: f"{v:.2f}", "#009E73")]
bars = [("Precision", m.precision.values, "#56B4E9"), ("Recall", m.recall.values, "#E69F00"), ("F1", m.f1.values, "#222222")]
for i, (lab, vals, col) in enumerate(bars): ax.bar(x + (i - 2.5) * w, vals, w, label=lab, color=col)
for j, (lab, vals, fmt, col) in enumerate(attrs):
    sc = np.array(vals, float) / max(vals); xs_ = x + (j + 0.5) * w
    ax.bar(xs_, sc, w, label=lab + " (scaled to its maximum)", facecolor="white", edgecolor=col, hatch="////", linewidth=0.9)
    for xx, v, h_ in zip(xs_, vals, sc): ax.text(xx, h_ + 0.015, fmt(v), rotation=90, ha="center", va="bottom", fontsize=6)
ax.set_xticks(x); ax.set_xticklabels([SHORT[c].replace("\n", " ") for c in order], fontsize=7); ax.set_ylim(0, 1.5); ax.set_yticks(np.arange(0, 1.01, 0.2)); ax.set_ylabel("score, or attribute scaled to its maximum")
ax.set_xlabel("entries ordered by cell human"); ax.set_title("a  Scores and size of each entry")
ax.legend(frameon=False, fontsize=6.3, ncol=2, loc="upper left", handlelength=1.6, columnspacing=1.0)
# (b) recall vs annotation size, one line per model
ax = fig.add_subplot(gs[0, 5:9]); h = t["H1_recall_vs_cells_human"]; mods = list(h["per_model"])
xs = np.arange(len(order))
mat = []
for mname in mods:
    g = v6[v6.model == mname].groupby("case").recall.mean().reindex(order); mat.append(g.values); ax.plot(xs, g.values, "-", color="#999999", lw=0.9, alpha=0.8)
    ax.scatter(xs, g.values, s=10, c=[COL[c] for c in order], zorder=3, linewidths=0)
ax.plot(xs, np.mean(mat, axis=0), "-", color="black", lw=2, label="mean of 8 models")
ax.scatter(xs, np.mean(mat, axis=0), s=55, c=[COL[c] for c in order], edgecolors="black", linewidths=1, zorder=4)
ax.set_xticks(xs); ax.set_xticklabels([f"{SHORT[c]}\n{int(ent.loc[c, 'cells_human']):,}" for c in order], fontsize=6.5); ax.set_xlabel("entries ordered by cell human"); ax.set_ylabel("recall")
ax.legend(frameon=False, fontsize=7, loc="upper right")
ax.set_title("b  Longer output to write, lower recall", fontsize=9, pad=16); ax.text(0.5, 1.015, f"mean ρ = {h['mean_rho']:.2f}, {h['n_negative']}/{h['models']} models negative, permutation p = {h['perm_p_two_sided']:.3f}", transform=ax.transAxes, ha="center", fontsize=7)
# (c) cells written vs cells in the annotation
ax = fig.add_subplot(gs[0, 9:12]); med = v6.groupby("case").cells_ai.median().reindex(order); lim = [150, 3200]
ax.plot(lim, lim, "--", color="#888888", lw=1, label="cell AI = cell human")
for c in order: ax.scatter(ent.loc[c, "cells_human"], med[c], s=60, color=COL[c], zorder=3); ax.annotate(NAME[c].replace("\n", " "), (ent.loc[c, "cells_human"], med[c]), fontsize=6.3, xytext=(4, -9), textcoords="offset points")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(lim); ax.set_ylim(lim); import matplotlib.ticker as mt; [a_.set_major_formatter(mt.FuncFormatter(lambda v, _: f"{int(v):,}")) for a_ in (ax.xaxis, ax.yaxis)]; ax.set_xticks([300, 1000, 3000]); ax.set_yticks([300, 1000, 3000]); ax.minorticks_off(); ax.set_xlabel("cell human"); ax.set_ylabel("cell AI (median over models)")
ax.set_title("c  Cell AI stays at 300-800\nwhatever cell human is", pad=16); ax.legend(frameon=False, fontsize=7, loc="upper left")
# (d) precision vs unpairable rows, all prompts and models, within entry
ax = fig.add_subplot(gs[1, 0:6]); # the same runs as in trends.json (H4)
a = runs[(runs.ok == 1) & runs.case.isin(FIVE) & runs.rows_ai.notna() & runs.steps_written.notna()].copy(); a["share"] = (a.rows_ai - a.rows_aligned) / a.rows_ai
for c in FIVE: g = a[a.case == c]; ax.scatter(g.share, g.precision, s=9, alpha=0.5, color=COL[c], label=NAME[c].replace("\n", " "), linewidths=0)
bins = np.linspace(0, 0.9, 10); a["b"] = pd.cut(a.share, bins); bm = a.groupby("b", observed=True).agg(x=("share", "mean"), y=("precision", "mean")); ax.plot(bm.x, bm.y, "k-", lw=2, label="binned mean")
ax.set_xlabel("share of answer rows that cannot be paired with an annotation row"); ax.set_ylabel("precision"); ax.legend(frameon=False, fontsize=6.5, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.2), markerscale=1.6)
p4 = t["H4_per_model"]; ax.set_title("d  Wrong row structure lowers precision", fontsize=9, pad=16); ax.text(0.5, 1.015, f"{len(a)} runs, all prompts: within-entry ρ = {t['H4_precision_vs_extra_rows_share_within_entry']['rho']:.2f} (recall {t['H4_recall_vs_extra_rows_share_within_entry']['rho']:.2f}); {p4['n_negative_precision']}/{p4['n_models']} models negative, p = {p4['sign_test_p_two_sided']:.3f}", transform=ax.transAxes, ha="center", fontsize=7)
# (e) PDF text vs HTML text (spot assay, so the colour of the spot assay in panels c and d); solid line = precision, dashed line = recall; filled = HTML-derived text, open = text extracted from the PDF
ax = fig.add_subplot(gs[1, 7:12]); P = t["H3_pdf_vs_html"]["pairs"]; y = np.arange(len(P))[::-1]; ec = COL["sdy1"]
short = lambda s: s.replace(" (local LM Studio)", " (Mac)").replace("-4bit", "").replace(" (OpenRouter free)", "")
for k, ls, off in (("precision", "-", 0.14), ("recall", "--", -0.14)):
    for yi, p in zip(y, P):
        ax.plot([p["html_" + k], p["pdf_" + k]], [yi + off] * 2, ls, color=ec, lw=1.5, alpha=0.9)
        ax.scatter(p["html_" + k], yi + off, s=26, color=ec, zorder=3, edgecolors=ec, linewidths=1.0)
        ax.scatter(p["pdf_" + k], yi + off, s=26, color="white", zorder=3, edgecolors=ec, linewidths=1.3)
ax.set_yticks(y); ax.set_yticklabels([short(p["model"]) for p in P], fontsize=6.5); ax.set_xlim(0, 1.0); ax.set_xlabel("precision or recall of the spot assay")
pf = lambda x: "not computed" if x is None else f"{x:.2f}"; h3 = t["H3_pdf_vs_html"]; ax.set_title("e  Text extracted from the PDF lowers both", fontsize=9, pad=16); ax.text(0.5, 1.015, f"precision {h3['precision']['mean_change']:+.2f} ({h3['precision']['n_lower_with_pdf']}/{h3['precision']['n_models']} lower, p = {pf(h3['precision']['wilcoxon_p_two_sided'])}); recall {h3['recall']['mean_change']:+.2f} ({h3['recall']['n_lower_with_pdf']}/{h3['recall']['n_models']} lower, p = {pf(h3['recall']['wilcoxon_p_two_sided'])})", transform=ax.transAxes, ha="center", fontsize=7)
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([], [], color=ec, lw=1.6, ls="-", label="precision (solid line)"), Line2D([], [], color=ec, lw=1.6, ls="--", label="recall (dashed line)"),
                   Line2D([], [], color=ec, marker="o", ls="", markerfacecolor=ec, label="HTML-derived text (filled)"), Line2D([], [], color=ec, marker="o", ls="", markerfacecolor="white", markeredgewidth=1.3, label="text extracted from the PDF (open)")],
          frameon=False, fontsize=6.6, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, handlelength=2.2, columnspacing=1.6)
fig.savefig(T + "fig_trends.png", dpi=220, bbox_inches="tight"); print("saved", T + "fig_trends.png")
