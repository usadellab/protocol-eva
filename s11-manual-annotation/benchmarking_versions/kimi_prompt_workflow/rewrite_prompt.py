#!/opt/homebrew/bin/python3.13
"""Whole-prompt rewrite by Kimi (Kimi Code CLI), with mechanical checks. Used for v9 (the user's request: fix the linking rule, no all-caps emphasis, plain steps, all examples merged into the first example JSON).

  rewrite_prompt.py <base-module> <new-module> [rounds=4]
The program placeholders of the template are masked ({{CHUNK}} ...), template-literal escapes are shown as the text the model sees; Kimi returns the complete template between <<<PROMPT and PROMPT>>>.
Checks (a failed check goes back to Kimi as feedback): all six placeholders exactly once, no backtick, no "${", every schema key still present, no all-caps word (acronym whitelist), shorter than the base,
leakage check against the base module (check_prompt_leakage.py), the module renders under node. Only prompt text changes: the code of the module is copied byte for byte."""
import os, re, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
START = "promptTemplate = `You are a scientific data extraction assistant"
PH = [("${chunks.length > 1 ? ' section' : ''}", "{{SECTION}}"), ("${contextInfo}", "{{CONTEXT}}"), ("${chunkInfo}", "{{CHUNKINFO}}"), ("${chunk}", "{{CHUNK}}"),
      ("${metadata.protocolPath ? ` (${metadata.protocolPath})` : ''}", "{{PROTOCOL_PATH_SUFFIX}}"),
      ("${chunks.length > 1 ? 'NOTE: This is part of a larger protocol, extract what you can from this section\\n\\n' : ''}", "{{PART_NOTE}}")]
KEYS = ["samples", "name", "organism", "characteristics", "category", "value", "unit", "termSource", "termAccession", "evidence", "protocols", "description", "inputs", "parameters", "outputs", "dataFiles"]
ACRONYMS = {"JSON", "OD", "DNA", "RNA", "PCR", "ID", "HTML", "UTF", "RPM", "UV", "SDS", "PBS", "NCBI", "NCIT", "OBI", "EFO", "SOP", "CSV", "XML", "URL", "FASTQ", "FASTA", "QC", "TAE", "ARC", "ISA", "BSA", "DMSO", "EDTA", "TSV"}


def split(path):
    lines = Path(path).read_text().split("\n")
    a = next(i for i, l in enumerate(lines) if START in l)
    b = next(i for i, l in enumerate(lines) if l.startswith("Return ONLY valid JSON") or l.startswith("Return only valid JSON"))
    return lines, a, b


def masked(path):
    lines, a, b = split(path)
    text = "\n".join(lines[a:b + 1])
    text = text.split("promptTemplate = `", 1)[1].rsplit("`;", 1)[0]
    for src, tok in PH:
        assert text.count(src) == 1, (src, text.count(src))
        text = text.replace(src, tok)
    return text.replace("\\\\", "\\")           # template-literal escape -> the characters the model sees


def build(base, new, body):
    lines, a, b = split(base)
    for src, tok in PH:
        body = body.replace(tok, "\x00" + str(PH.index((src, tok))) + "\x00")
    body = body.replace("\\", "\\\\")
    for i, (src, tok) in enumerate(PH):
        body = body.replace("\x00" + str(i) + "\x00", src)
    head = lines[a][:lines[a].index("promptTemplate = `")] + "promptTemplate = `"
    out = lines[:a] + [head + body + "`;"] + lines[b + 1:]
    Path(new).write_text("\n".join(out))


def checks(base, body):
    problems = []
    for _, tok in PH:
        if body.count(tok) != 1:
            problems.append(f"placeholder {tok} must occur exactly once (found {body.count(tok)})")
    if "`" in body: problems.append("contains a backtick")
    if "${" in body: problems.append("contains '${'")
    for k in KEYS:
        if f'"{k}"' not in body: problems.append(f'schema key "{k}" is missing')
    caps = sorted({w for w in re.findall(r"\b[A-Z]{3,}\b", re.sub(r"\{\{[A-Z_]+\}\}", "", body)) if w not in ACRONYMS})
    if caps: problems.append(f"all-capital words found: {caps}")
    limit = len(masked(base)) * float(os.environ.get("RATIO", "1.0"))          # RATIO=1.1: a small revision may grow by 10 %
    if len(body) >= limit: problems.append(f"too long ({len(body)} >= {limit:.0f} characters; the base has {len(masked(base))})")
    return problems


def ask(request_path, answer_path):
    r = subprocess.run([sys.executable, str(HERE / "ask_kimi_cli.py"), str(request_path), str(answer_path)], capture_output=True, text=True)
    if r.returncode: sys.exit("Kimi call failed: " + (r.stdout + r.stderr)[-400:])


def main(base, new, rounds=4):
    base, new = HERE / base, HERE / new
    instr = (HERE / "prompt_iter" / os.environ.get("INSTR", "instructions_v9.md")).read_text()
    request = instr + "\n\nCURRENT PROMPT (between the markers):\n<<<PROMPT\n" + masked(base) + "\nPROMPT>>>\n"
    if os.environ.get("REF"):                                  # a second prompt shown as reference (e.g. v6 for v10)
        request += "\n\nREFERENCE PROMPT (the earlier version 6, between the markers; the answer must not copy its capital-letter emphasis):\n<<<REFERENCE\n" + masked(HERE / os.environ["REF"]) + "\nREFERENCE>>>\n"
    feedback = ""
    for rnd in range(rounds + 1):
        req = HERE / "prompt_iter" / f"req_{os.environ.get('TAG', 'v9')}_{rnd}.md"; ans = HERE / "prompt_iter" / f"ans_{os.environ.get('TAG', 'v9')}_{rnd}.md"
        req.write_text(request + feedback); ask(req, ans)
        m = re.search(r"<<<PROMPT\n(.*?)\nPROMPT>>>", ans.read_text(), re.S)
        if not m:
            feedback = "\n\nYour previous answer had no <<<PROMPT ... PROMPT>>> block. Send the complete prompt text between those markers and nothing else.\n"; continue
        body = m.group(1)
        problems = checks(base, body)
        if not problems:
            build(base, new, body)
            leak = subprocess.run([sys.executable, str(HERE / "check_prompt_leakage.py"), str(new), "--baseline", str(base)], capture_output=True, text=True).stdout
            if "\nLEAK" in leak or leak.strip().endswith("LEAK"):
                problems.append("leakage control: " + re.search(r"new annotation tokens in prompt = (.*)", leak).group(0) + " (words that also occur in the curated annotation tables; rephrase without them)")
        if not problems:
            print(f"PASS after {rnd + 1} answer(s): {new} ({len(body)} characters vs {len(masked(base))} in the base)"); return
        print(f"answer {rnd}: " + "; ".join(problems))
        feedback = ("\n\nYOUR PREVIOUS ANSWER WAS REJECTED by the automatic checks:\n- " + "\n- ".join(problems)
                    + "\nSend the COMPLETE prompt again between <<<PROMPT and PROMPT>>>, fixing these points and changing nothing else.\n")
    sys.exit("no passing answer")


if __name__ == "__main__":
    if sys.argv[1] == "--control":                       # round trip: masking then building reproduces the base module byte for byte; the checks catch bad input
        base = "llm-service.local-v8.js"; body = masked(HERE / base)
        build(HERE / base, HERE / "_roundtrip.js", body)
        assert (HERE / "_roundtrip.js").read_text() == (HERE / base).read_text(), "round trip changed the module"
        assert checks(HERE / base, body) and any("too long" in p for p in checks(HERE / base, body)), "base must fail the 'shorter' check"
        bad = checks(HERE / base, body.replace("{{CHUNK}}", "").replace("Extract", "EXTRACT ALL").replace(' "unit"', ''))
        assert any("{{CHUNK}}" in p for p in bad) and any("all-capital" in p for p in bad) and any('"unit"' in p for p in bad), bad
        (HERE / "_roundtrip.js").unlink(); print("control OK: byte-exact round trip; missing placeholder, all-capital word and missing schema key are caught")
    else:
        main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 4)
