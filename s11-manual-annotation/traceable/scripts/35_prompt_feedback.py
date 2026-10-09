#!/opt/homebrew/bin/python3.13
"""Prompt feedback from evidence feedback (PLAN_evidence_loop.md, phase B).

  35_prompt_feedback.py <model-tag> <prompt-tag> [<prompt-tag> ...]   -> work/eval/prompt_feedback_<prompt-tag>.md
        e.g. 35_prompt_feedback.py gemma4-31b-lms v71        (the runs work/eval_<entry>/gemma4-31b-lms_v71_r*)
  35_prompt_feedback.py --critic <model-tag> <prompt-tag>             Kimi as critic on one run of EACH tuning entry; request and answer
        -> work/eval/prompt_iter/req_critic_<prompt-tag>_<entry>.md / ans_critic_<prompt-tag>_<entry>.md, together in critics_<prompt-tag>.md
  35_prompt_feedback.py --control

Per tuning entry (the hold-out entries are never read: they must not steer an edit): the Phase A feedback (34_evidence_feedback.py,
annotation-free part) of every run of the prompt, aggregated as
  - cell classes, share of the entry's cells (mean +- sd over the runs),
  - source coverage of the numeric tokens (mean +- sd) and the sections left uncovered in most runs (>= 50% of their numeric tokens uncovered,
    >= 2 numeric tokens), with line range and text excerpt,
  - 3 verbatim examples per class (quote, value, source line), taken round-robin over the runs.
"""
import importlib.util
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent                  # root of the section; the run folders (work/eval*/) are not part of it
TUNING = {"sdy1": "work/eval_sdy1", "phage": "work/eval_phage", "ux511": "work/eval_ux511"}   # hold-out: BioLector-034
PRIOR_CLASSES = ["ok", "missing", "unresolved/table_paraphrase", "unresolved/not_in_source",
                 "value_not_in_quote/number_changed", "value_not_in_quote/derived_label"]


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename if filename.startswith("28_") else Path(__file__).resolve().parent / filename)
    mod = importlib.util.module_from_spec(spec)
    argv, sys.argv = sys.argv, sys.argv[:1]
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.argv = argv
    return mod


F = _load("fb34", "34_evidence_feedback.py")


def run_dirs(entry_dir, model, prompt):
    return sorted(d for d in (ROOT / entry_dir).glob(f"{model}_{prompt}_r[0-9]*") if d.is_dir())


def collect(model, prompt):
    """-> {entry: {"runs": [feedback], "failed": [dir names without usable evidence], "source_text": str}} for the tuning entries."""
    out = {}
    for entry, edir in TUNING.items():
        runs, failed, text = [], [], None
        for d in run_dirs(edir, model, prompt):
            if not (d / "evidence.json").exists():
                failed.append(d.name)
                continue
            runs.append(F.feedback(d, annotation=False))
            text = text or F.load_run(d)[2]
        if runs:
            out[entry] = {"runs": runs, "failed": failed, "text": text}
    return out


def ms(values):
    values = list(values)
    return f"{statistics.mean(values):.3f} ± {statistics.stdev(values) if len(values) > 1 else 0.0:.3f}"


def share(fb, cls):
    return fb["cell_classes"].get(cls, {"share": 0.0})["share"]


def uncovered_sections(runs):
    """sections (start_line, end_line, label) with >= 50% of >= 2 numeric tokens uncovered, with the number of runs in which this holds."""
    count, info = {}, {}
    for fb in runs:
        for s in fb["coverage"]["sections"]:
            key = (s["start_line"], s["end_line"])
            info[key] = s
            if s["numeric"] >= 2 and s["uncovered"] >= 0.5 * s["numeric"]:
                count[key] = count.get(key, 0) + 1
    return sorted(((k, n, info[k]) for k, n in count.items()), key=lambda t: (-t[1], -t[2]["uncovered"]))


def round_robin_examples(runs, cls, k=3):
    pools = [list(fb["examples"].get(cls, [])) for fb in runs]
    out = []
    while len(out) < k and any(pools):
        for p in pools:
            if p and len(out) < k:
                out.append(p.pop(0))
    return out


def line_text(text, line, limit=220):
    s = text.split("\n")[line - 1] if line and 1 <= line <= text.count("\n") + 1 else ""
    return re.sub(r"\s+", " ", F.TAG.sub(" ", s)).strip()[:limit]


def excerpt(text, a, b, limit=260):
    lines = text.split("\n")[a - 1:b]
    return re.sub(r"\s+", " ", F.TAG.sub(" ", " ".join(lines))).strip()[:limit]


def render(model, prompt, data):
    L = [f"# Prompt feedback for {model} / prompt {prompt} (tuning entries only)", "",
         "Built from the evidence of every run of this prompt (Phase A feedback, annotation-free). Shares are shares of the entry's value cells. "
         "A class other than `ok` is a defect of the quote: the value could not be traced to the protocol text.", ""]
    tot = {c: [] for c in PRIOR_CLASSES}
    for entry, d in data.items():
        for fb in d["runs"]:
            for c in PRIOR_CLASSES:
                tot[c].append(share(fb, c))
    L += ["## All tuning entries together", "", "| class | mean share per run |", "|---|---|"] + [f"| {c} | {ms(v)} |" for c, v in tot.items() if v]
    for entry, d in data.items():
        runs, text = d["runs"], d["text"]
        L += ["", f"## Entry {entry}: {len(runs)} runs with evidence" + (f", {len(d['failed'])} failed runs ({', '.join(d['failed'])})" if d["failed"] else ""),
              "", f"Cells per run: {ms(fb['cells'] for fb in runs)}. Source coverage of numeric tokens: {ms(fb['coverage']['share'] for fb in runs)}.", "",
              "| class | share per run |", "|---|---|"]
        for c in PRIOR_CLASSES:
            L.append(f"| {c} | {ms(share(fb, c) for fb in runs)} |")
        unc = uncovered_sections(runs)
        L += ["", "Sections whose numeric tokens are uncovered (>= 50%) - in how many runs:", ""]
        if not unc:
            L.append("- none")
        for (a, b), n, s in unc[:6]:
            L.append(f"- lines {a}-{b}, {n} of {len(runs)} runs, {s['numeric']} numeric tokens: `{excerpt(text, a, b)}`")
        for c in PRIOR_CLASSES[1:]:
            exs = round_robin_examples(runs, c)
            if not exs:
                continue
            L += ["", f"Examples of `{c}`:", ""]
            for e in exs:
                src = e.get("passage") or (line_text(text, e["line"]) if e.get("line") else "")
                L.append(f"- value `{e['value']}` ({e.get('name')}); quote: `{str(e['quote'])[:200]}`" + (f"; source line {e['line']}: `{src[:220]}`" if src else ""))
    return "\n".join(L) + "\n"


def critic_request(model, prompt, entry, run_dir):
    fb = F.feedback(run_dir, annotation=False)
    data, ev, text, raw = F.load_run(run_dir)
    prompt_text = (ROOT / raw["module"]).read_text()
    a = prompt_text.index("promptTemplate = `You are a scientific data extraction assistant")
    b = prompt_text.index("Return ONLY valid JSON, no additional text.") + len("Return ONLY valid JSON, no additional text.")
    cur = prompt_text[a:b]
    secs = fb["coverage"]["top_uncovered"][:6]
    bad = [e for e in ev["entries"] if e["status"] not in F.GOOD][:8]
    parts = [f"Section {s['start_line']}-{s['end_line']} ({s['uncovered']} of {s['numeric']} numeric tokens not covered by any quote):\n"
             f"{excerpt(text, s['start_line'], s['end_line'], 700)}" for s in secs]
    quotes = [f"- cell {e['name']} = {e['value']!r}; status {e['status']}; quote: {str(e.get('quote'))[:200]!r}" for e in bad]
    msg = f"""You are the model that runs the extraction prompt below on a wet-lab protocol text. One run of yours was checked against the text: every value you
wrote should carry a verbatim quote, and the program located each quote. No answer key was used, only the protocol text.

Result of this run: {fb['cells']} value cells; share of numeric tokens of the text that lie inside one of your quotes: {fb['coverage']['share']}.

Passages of the text with numbers that none of your quotes covers (so you extracted nothing from them, or quoted elsewhere):
{chr(10).join(parts) or '(none)'}

Cells whose quote could not be traced to the text:
{chr(10).join(quotes) or '(none)'}

QUESTION: why did the extraction miss these passages, and which unresolved quotes went wrong and why? Then give ONE generic rule (at most 8 lines, no names
from these examples, synthetic examples only) that would make an extractor capture such passages and quote exactly. The rule must not ask the model to repair,
tolerate or post-process anything, and must keep the JSON schema.

CURRENT PROMPT:
<<<PROMPT
{cur}
PROMPT>>>

Answer as ONE JSON object and nothing else: {{"diagnosis": "<3-5 sentences>", "rule": "<the rule text, lines separated by \\n>"}}"""
    return msg


def critic(model, prompt):
    """Kimi as critic on the first successful run of EACH tuning entry; answers in prompt_iter/ans_critic_<prompt>_<entry>.md and all
    together in prompt_iter/critics_<prompt>.md (the file propose_edit.py --critique reads)."""
    sys.path.insert(0, str(ROOT / "work/eval"))
    import ask_kimi
    out = ROOT / "work/eval/prompt_iter"
    combined = []
    for entry, edir in TUNING.items():
        run = next((x for x in run_dirs(edir, model, prompt) if (x / "evidence.json").exists()), None)
        if run is None:
            continue
        req = critic_request(model, prompt, entry, run)
        (out / f"req_critic_{prompt}_{entry}.md").write_text(req)
        content, usage, secs = ask_kimi.ask(req)
        (out / f"ans_critic_{prompt}_{entry}.md").write_text(content)
        combined.append(f"Critique of one run on entry {entry} ({run.name}):\n{content}")
        print(f"critic on {run.name}: answer {len(content)} chars, usage {usage}, {secs}s")
    (out / f"critics_{prompt}.md").write_text("\n\n".join(combined))
    return combined


def control():
    fails = []

    def check(name, ok, detail=""):
        print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
        if not ok:
            fails.append(name)

    mk = lambda cls, n, ex=(): {"cells": 10, "cell_classes": {cls: {"cells": n, "share": n / 10}}, "examples": {cls: list(ex)},
                                "coverage": {"share": 0.5, "sections": [{"start_line": 1, "end_line": 2, "numeric": 4, "uncovered": 3}]}, "run": "r"}
    ex = [{"value": f"v{i}", "quote": f"q{i}", "name": "n", "line": 1} for i in range(3)]
    runs = [mk("unresolved/not_in_source", 2, ex), mk("unresolved/not_in_source", 4, ex[:1])]
    check("class share mean over runs", abs(statistics.mean(share(r, "unresolved/not_in_source") for r in runs) - 0.3) < 1e-9)
    check("class share of an absent class is 0", share(runs[0], "missing") == 0.0)
    check("round robin takes one example from each run first", [e["value"] for e in round_robin_examples(runs, "unresolved/not_in_source")] == ["v0", "v0", "v1"])
    check("section uncovered in both runs", uncovered_sections(runs)[0][1] == 2)
    check("control of control: a section with only 1 of 4 numeric tokens uncovered is not listed",
          uncovered_sections([{"coverage": {"sections": [{"start_line": 1, "end_line": 2, "numeric": 4, "uncovered": 1}]}}]) == [])
    check("hold-out entries are not read", not ({"biolector034"} & set(TUNING)))
    real = collect("gemma4-31b-lms", "v71")
    check("real v71 runs found for the three tuning entries", set(real) == set(TUNING), str(sorted(real)))
    text = render("gemma4-31b-lms", "v71", real)
    check("rendered feedback has examples of a real class", "Examples of `" in text)
    wrong = collect("gemma4-31b-lms", "v7999")
    check("control: a prompt tag without runs gives no entries", wrong == {})
    print("CONTROLS PASS" if not fails else f"CONTROLS FAILED: {fails}")
    return not fails


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--control"]:
        sys.exit(0 if control() else 1)
    if a and a[0] == "--critic" and len(a) == 3:
        critic(a[1], a[2])
        sys.exit(0)
    if len(a) < 2 or a[0].startswith("--"):
        sys.exit(__doc__)
    model = a[0]
    for prompt in a[1:]:
        data = collect(model, prompt)
        if not data:
            sys.exit(f"no runs with evidence for {model} {prompt}")
        out = ROOT / f"work/eval/prompt_feedback_{prompt}.md"
        out.write_text(render(model, prompt, data))
        print(f"{out}: {sum(len(d['runs']) for d in data.values())} runs, entries {list(data)}")
