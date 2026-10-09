#!/opt/homebrew/bin/python3.13
"""Why did a v6 run fail? For every failed v6 run (five entries, text only): finish reason of the last request, completion tokens, token limit of the request, parse error.
cause = 'budget' when the answer stopped at the output limit (finish_reason length or completion tokens >= 98 % of max_tokens), 'invalid JSON' (answer complete but not parseable), 'empty' (no content), 'other'."""
import importlib.util, json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]                  # root of the section; the run folders (work/eval*/) are not part of it
spec = importlib.util.spec_from_file_location("s", ROOT / "scripts/28_score_extraction.py")
out = []
for case in ("sdy1", "phage", "ux511", "biolector034", "pux782"):
    sys.argv = ["x", case]; S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
    for label, run in S.discover(case).items():
        if "general prompt v6" not in label or ", +" in label or run["status"] == "ok": continue
        d = run["dir"]; j = json.loads((d / "llm.json").read_text()) if (d / "llm.json").exists() else {}
        raws = sorted(d.glob("llm.raw*.txt")); raw = raws[-1].read_text() if raws else ""
        fin = (re.findall(r'"finish_reason":\s*"(\w+)"', raw) or [None])[-1]
        u = ((j.get("usage") or [None])[-1]) or {}
        ct = u.get("completion_tokens"); mt = (j.get("request") or {}).get("max_tokens") or ((j.get("request") or {}).get("settings") or {}).get("max_tokens")
        cause = "budget" if (fin == "length" or (ct and mt and ct >= 0.98 * mt)) else ("invalid JSON" if "invalid JSON" in str(j.get("error")) else ("empty" if not j.get("llmData") and not raw.strip() else "other"))
        out.append({"model": run["model"], "case": case, "dir": str(d.relative_to(ROOT)), "cause": cause, "finish": fin, "completion_tokens": ct, "max_tokens": mt, "route": j.get("route") or ("cli" if "cli_output.json" in [p.name for p in d.iterdir()] else "api")})
json.dump(out, open(ROOT / "analysis/failures_v6.json", "w"), indent=1)
import collections
c = collections.Counter((o["model"], o["cause"]) for o in out)
for (m, cause), n in sorted(c.items()): print(f"{m:44s} {cause:13s} {n}")
print(len(out), "failed v6 runs")
for o in out:
    if o["cause"] == "budget": print("  budget:", o["dir"], o["completion_tokens"], "/", o["max_tokens"])
