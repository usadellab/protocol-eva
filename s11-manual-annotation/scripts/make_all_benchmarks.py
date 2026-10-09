#!/opt/homebrew/bin/python3.13
"""work/eval/ALL_BENCHMARKS.md from work/eval/leaderboard.csv (run `scripts/28_score_extraction.py all` first). Record F1 vs manual annotation B on the five reporting entries; failed runs = 0."""
import csv, collections, re, statistics as st
from pathlib import Path
HERE = Path(__file__).resolve().parent
rows = [r for r in csv.DictReader(open(HERE / "leaderboard.csv")) if r["annotation"] == "manual annotation B" and r["prompt"] != "reference" and r["case"] in ("sdy1", "phage", "ux511", "biolector034", "pux782")]
cases = ["sdy1", "phage", "ux511", "biolector034", "pux782"]; names = ["SDY1", "phage", "UX511", "BioLector-034", "pUX782-787"]
G = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    model, cond = r["model"], "text"
    m = re.search(r", \+ (.*)$", model)
    if m: cond, model = m.group(1), model[:m.start()]
    G[(model, r["prompt"].split(" (")[0], cond)][r["case"]].append((float(r["record_f1"] or 0), r["status"], float(r["traceable_share"]) if r["traceable_share"] else None))
out = []
for k, g in G.items():
    ent = [c for c in cases if g.get(c)]
    out.append((len(ent), st.mean(st.mean(x[0] for x in g[c]) for c in ent), k, g, sum(1 for c in ent for x in g[c] if x[1] != "ok"), sum(len(g[c]) for c in ent)))
out.sort(key=lambda o: (-o[0], -o[1]))
md = ["# All benchmarks (record F1 vs manual annotation B; failed runs count as 0)", "",
      "Cell = mean ± sd (n); `*` = at least one failed run in the cell; `–` = not run. Mean = mean of the entry means over the entries that were run (count in the Entries column). Traceable = share of cells whose evidence quote was located in the text (evidence prompts only).", "",
      "| Model | Prompt | Input | " + " | ".join(names) + " | Mean | Entries | Runs | Failed | Traceable |", "|" + "---|" * (len(names) + 8)]
for ne, mean, (model, prompt, cond), g, fails, nruns in out:
    cells = [("%.2f±%.2f (%d)%s" % (st.mean(x[0] for x in g[c]), st.stdev([x[0] for x in g[c]]) if len(g[c]) > 1 else 0, len(g[c]), "*" if any(x[1] != "ok" for x in g[c]) else "")) if g.get(c) else "–" for c in cases]
    tr = [x[2] for c in cases for x in g.get(c, []) if x[2] is not None]
    md.append("| %s | %s | %s | %s | **%.3f** | %d | %d | %d | %s |" % (model, prompt, cond, " | ".join(cells), mean, ne, nruns, fails, ("%.2f" % st.mean(tr)) if tr else ""))
(HERE / "ALL_BENCHMARKS.md").write_text("\n".join(md) + "\n"); print(len(out), "configurations ->", HERE / "ALL_BENCHMARKS.md")
