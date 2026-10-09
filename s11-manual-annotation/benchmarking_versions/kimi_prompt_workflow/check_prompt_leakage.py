#!/opt/homebrew/bin/python3.13
"""Leakage control for candidate extraction prompts (PLAN_prompt_kimi.md).

An annotation token = a word-token (lower case) of any cell of any annotation assay xlsx (all entries, all annotations in 28_score_extraction.CASES),
at least 3 characters long, not among the 50 most frequent tokens over all annotation cells. The prompt text is the template literal of the
module (as in make_prompt_versions.py). A candidate PASSES when no annotation token occurs in its prompt text beyond the annotation tokens the
baseline prompt (default v6) already contains.

  check_prompt_leakage.py <candidate-module.js> [--baseline <module.js>]   exit 0 = pass, 1 = leak
  check_prompt_leakage.py --control                                         exit 0 only if (a) the baseline passes against itself and
                                                                            (b) the baseline plus one annotation token fails
"""
import re, sys
from collections import Counter
from pathlib import Path
import openpyxl

ROOT = Path(__file__).resolve().parents[2]
EVAL = ROOT / "work/eval"
sys.path.insert(0, str(ROOT / "scripts"))
sys.argv, _argv = [sys.argv[0]], sys.argv           # 28 reads argv[1] at import
import importlib
score = importlib.import_module("28_score_extraction")
sys.argv = _argv
START = "promptTemplate = `You are a scientific data extraction assistant"
END = "Return ONLY valid JSON, no additional text."
TOKEN = re.compile(r"[a-z0-9]+(?:[._\-][a-z0-9]+)*")
BASELINE = EVAL / "llm-service.local-v6.js"


def tokens(text):
    return TOKEN.findall(text.lower())


def prompt_text(module):
    lines = Path(module).read_text().split("\n")
    a = next(i for i, l in enumerate(lines) if START in l)
    b = next(i for i, l in enumerate(lines) if l.startswith(END))
    return "\n".join(lines[a:b + 1])


def annotation_tokens():
    """-> set of annotation tokens (>= 3 chars, without the 50 most frequent)."""
    counts = Counter()
    for case in score.CASES.values():
        for path in case["annotations"].values():
            wb = openpyxl.load_workbook(path, read_only=True)
            for name in wb.sheetnames:
                if name == "isa_assay":
                    continue
                for row in list(wb[name].iter_rows(values_only=True))[1:]:
                    for cell in row:
                        if cell is not None:
                            counts.update(tokens(str(cell)))
    common = {t for t, _ in counts.most_common(50)}
    return {t for t in counts if len(t) >= 3 and t not in common}, common


def leaks(module_text, annotation):
    return annotation & set(tokens(module_text))


def check(candidate_text, baseline_text, annotation):
    return sorted(leaks(candidate_text, annotation) - leaks(baseline_text, annotation))


def control():
    annotation, common = annotation_tokens()
    base = prompt_text(BASELINE)
    clean = check(base, base, annotation)
    rare = sorted(t for t in annotation if t not in set(tokens(base)))[0]
    dirty = check(base + f"\nExample: the strain {rare} grows at 37 C", base, annotation)
    ok = clean == [] and dirty == [rare]
    print(f"control: baseline vs itself -> {clean}; baseline + '{rare}' -> {dirty}: {'PASS' if ok else 'FAIL'}")
    return ok


if __name__ == "__main__":
    if "--control" in sys.argv:
        sys.exit(0 if control() else 1)
    cand = sys.argv[1]
    base = sys.argv[sys.argv.index("--baseline") + 1] if "--baseline" in sys.argv else BASELINE
    annotation, common = annotation_tokens()
    bad = check(prompt_text(cand), prompt_text(base), annotation)
    print(f"annotation tokens: {len(annotation)} (50 most common excluded: {sorted(common)[:8]}...)")
    print(f"{Path(cand).name} vs {Path(base).name}: new annotation tokens in prompt = {bad}")
    print("PASS" if not bad else "LEAK")
    sys.exit(0 if not bad else 1)
