#!/opt/homebrew/bin/python3.13
"""Score the phase-3 describe-and-list answers (50_image_feasibility.py) against the DRAFT image facts (work/eval/image_facts/image_facts_draft_by_claude.json).
The draft is not manual annotation (it is a draft read by Claude); the score is agreement with it.

Per figure and route:
  printed recall  share of the draft's printed facts (kinds label / mark / legend / axis / value; clone numbers and colour codes excluded) with >= 0.8 of their tokens (letter runs and digit runs) in the answer
  label+mark      the same restricted to kinds label and mark (plan phase 3: go if >= 90 %)
  lanes           gels and blots: lane lines of the LANES section against the draft's lane labels:
                    gel: a lane line is valid when it covers >= 0.8 of the tokens of the draft label at the same position;
                    blot: the clone numbers (last integer of each line, UMa133 / ladder lines dropped) against the draft's clone numbers in order;
                  invented = lane lines that do not match (plan phase 3: <= 10 % of the lane lines), plus lines beyond the true number of lanes;
  colour          blots: of the lane lines that carry a number, the share whose (green) flag equals the draft's colour at the same position
Observations are not scored.
  51_score_image_feasibility.py <route> ...     -> work/image_phase3/<route>/scores.json + work/eval/IMAGE_PHASE3_scores_<route>.md
  51_score_image_feasibility.py --control
"""
import collections, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAFT = ROOT / "work/eval/image_facts/image_facts_draft_by_claude.json"
tok = lambda s: re.findall(r"[a-z]+|\d+", s.lower().replace("µ", "u").replace("μ", "u"))
covered = lambda value, bag: (lambda t: bool(t) and sum(x in bag for x in t) / len(t) >= 0.8)(tok(value))


def section(answer, name):
    m = re.search(rf"^\W*{name}\W*:?(.*?)(?=^\W*(?:TYPE|TEXT|LANES|MARKERS|NUMBERS|OBSERVATIONS)\W*:|\Z)", answer, re.S | re.M | re.I)
    return m.group(1) if m else ""


def lane_lines(answer):
    out = []
    for ln in section(answer, "LANES").splitlines():
        ln = ln.strip().lstrip("-*• ").strip()
        if not ln or ln.upper().startswith("NONE"): continue
        out.append(re.sub(r"^\d+\s*[.)]\s*", "", ln))
    return out


def score_figure(figure, answer, facts):
    mine = [f for f in facts if f["figure"] == figure]
    printed = [f for f in mine if f["kind"] in ("label", "mark", "legend", "axis", "value") and f["attribute"] != "clone number"]
    bag = set(tok(answer))
    ok = [f for f in printed if covered(f["value"], bag)]
    lm = [f for f in printed if f["kind"] in ("label", "mark")]
    r = {"figure": figure, "printed": len(printed), "printed_ok": len(ok), "labelmark": len(lm), "labelmark_ok": sum(f in ok for f in lm),
         "missed": [f["id"] + " " + f["value"][:40] for f in printed if f not in ok][:8]}
    lanes_true = [f for f in mine if f["attribute"] == "lane label"]
    blot = [f for f in mine if f["attribute"] == "marked as correct on blot image" and not f["locator"].startswith("UMa")]
    lines = [l for l in lane_lines(answer) if "ladder" not in l.lower() and not l.lower().startswith("uma")] if (lanes_true or blot) else []
    if lanes_true:
        truth = [tok(f["value"]) for f in lanes_true]
        valid = 0
        for i, l in enumerate(lines):
            t = set(tok(l))
            if i < len(truth) and truth[i] and sum(x in t for x in truth[i]) / len(truth[i]) >= 0.8: valid += 1
        r.update(lane_lines=len(lines), lanes_true=len(truth), lane_valid=valid, lane_invented=len(lines) - valid)
    if blot:
        truth_n = [re.search(r"clone (\d+)", f["locator"]).group(1) for f in blot]
        truth_g = [f["value"].startswith("yes") for f in blot]
        nums = []
        for l in lines:
            m = re.findall(r"\d+", re.sub(r"\(green\)", "", l, flags=re.I))
            nums.append((m[-1] if m else None, "(green)" in l.lower() or "green" in l.lower()))
        valid = sum(1 for i, (n, g) in enumerate(nums) if i < len(truth_n) and n == truth_n[i])
        col = sum(1 for i, (n, g) in enumerate(nums) if i < len(truth_n) and n == truth_n[i] and g == truth_g[i])
        r.update(lane_lines=len(lines), lanes_true=len(truth_n), lane_valid=valid, lane_invented=len(lines) - valid, colour_ok=col, colour_n=valid)
    return r


def adjust(answer):
    """POST-HOC adjustment (added after the first phase-3 scoring, reported separately): LaTeX micro sign "$\\mu$M" -> "µM"; lane lines that are only the placeholder "unclear" (unlabelled ladder lanes) dropped"""
    a = answer.replace("$\\mu$", "µ").replace("\\mu", "µ")
    return "\n".join(l for l in a.splitlines() if not re.fullmatch(r"\W*\d+\s*[.)]\s*unclear\W*", l.strip(), re.I))


def score_route(route, adjusted=False):
    facts = json.loads(DRAFT.read_text())["facts"]
    rows = []
    for p in sorted((ROOT / "work/image_phase3" / route).glob("*_*.json")):
        if p.name in ("scores.json",): continue
        rec = json.loads(p.read_text())
        rows.append({**score_figure(rec["figure"], adjust(rec.get("answer", "")) if adjusted else rec.get("answer", ""), facts), "ok": rec["ok"], "seconds": rec.get("seconds"), "prompt_tokens": (rec.get("usage") or {}).get("prompt_tokens"),
                     "attempts": rec.get("attempts")})
    return rows


def summary(rows):
    s = collections.Counter()
    for r in rows:
        for k in ("printed", "printed_ok", "labelmark", "labelmark_ok", "lane_lines", "lane_valid", "lane_invented", "colour_ok", "colour_n"): s[k] += r.get(k, 0)
    return {"printed_recall": s["printed_ok"] / s["printed"] if s["printed"] else None, "labelmark_recall": s["labelmark_ok"] / s["labelmark"] if s["labelmark"] else None,
            "lane_invented_rate": s["lane_invented"] / s["lane_lines"] if s["lane_lines"] else None, "colour_agreement": s["colour_ok"] / s["colour_n"] if s["colour_n"] else None, **s}


def control():
    facts = json.loads(DRAFT.read_text())["facts"]
    figs = list(dict.fromkeys(f["figure"] for f in facts)); bad = 0
    def check(name, ok):
        nonlocal bad
        print(("ok   " if ok else "FAIL ") + name); bad += (not ok)
    def perfect(fig):   # an answer built from the draft itself
        mine = [f for f in facts if f["figure"] == fig]
        lanes = [f["value"] for f in mine if f["attribute"] == "lane label"]
        blot = [(re.search(r"clone (\d+)", f["locator"]).group(1), f["value"].startswith("yes")) for f in mine if f["attribute"] == "marked as correct on blot image" and not f["locator"].startswith("UMa")]
        lane_txt = "\n".join(f"{i}. {l}" for i, l in enumerate(lanes, 1)) if lanes else "\n".join(f"{i}. {n}{' (green)' if g else ''}" for i, (n, g) in enumerate(blot, 1)) if blot else "NONE"
        return "TYPE: x\nTEXT:\n" + "\n".join(f["value"] for f in mine if f["kind"] in ("label", "mark", "legend", "axis", "value")) + "\nLANES:\n" + lane_txt + "\nMARKERS:\nNONE\nOBSERVATIONS:\n"
    perf = [score_figure(f, perfect(f), facts) for f in figs]; sp = summary(perf)
    check(f"draft's own values as the answer: printed recall 100 %, invented lanes 0, colour 100 % ({sp['printed_recall']:.2f}, {sp['lane_invented_rate']}, {sp['colour_agreement']})", sp["printed_recall"] == 1 and sp["lane_invented_rate"] == 0 and sp["colour_agreement"] == 1)
    empty = summary([score_figure(f, "", facts) for f in figs])
    check(f"empty answer: printed recall < 5 % ({empty['printed_recall']:.2f})", empty["printed_recall"] < 0.05)
    shuf = summary([score_figure(f, perfect(figs[(i + 5) % len(figs)]), facts) for i, f in enumerate(figs)])
    check(f"answers of the wrong figures: label+mark recall < 60 % ({shuf['labelmark_recall']:.2f})", shuf["labelmark_recall"] < 0.6)
    inv = summary([score_figure(f, perfect(f).replace("LANES:\n", "LANES:\n99. invented\n98. invented too\n"), facts) for f in figs if any(x["figure"] == f and x["attribute"] in ("lane label", "marked as correct on blot image") for x in facts)])
    check(f"two invented lane lines per gel/blot: invented rate > 10 % ({inv['lane_invented_rate']:.2f})", inv["lane_invented_rate"] > 0.10)
    swapcol = []
    for f in figs:
        a = perfect(f)
        swapcol.append(score_figure(f, a.replace(" (green)", "") if "(green)" in a else a, facts))
    sc = summary(swapcol)
    check(f"colour flag removed: colour agreement drops below 100 % ({sc['colour_agreement']:.2f})", sc["colour_agreement"] < 1)
    print("51 controls " + ("OK" if not bad else f"FAILED ({bad})")); sys.exit(1 if bad else 0)


if __name__ == "__main__":
    if sys.argv[1:] == ["--control"]: control()
    for route in sys.argv[1:]:
        rows = score_route(route); s = summary(rows); ra = score_route(route, adjusted=True); sa = summary(ra)
        (ROOT / "work/image_phase3" / route / "scores.json").write_text(json.dumps({"rows": rows, "summary": s, "rows_adjusted_post_hoc": ra, "summary_adjusted_post_hoc": sa}, indent=1))
        rd = lambda d: json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in d.items()})
        print(route, "strict  ", rd(s)); print(route, "adjusted", rd(sa))
