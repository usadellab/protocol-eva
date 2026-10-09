#!/opt/homebrew/bin/python3.13
"""Run one extraction on Kimi-K3 through the Kimi Code CLI (print mode) and write an llm.json in the format of 26_llm_extraction.js.

  37_kimi_cli_extract.py <llm-service.js> <protocol.md> <out.json> [assayId]
  37_kimi_cli_extract.py --control        stub tests only (a stub script imitates `kimi-cli --print`; no real CLI call, no network)

The prompt is exactly the one the app module builds: 26_llm_extraction.js is run with DRY=1 (the request is captured, nothing is sent) and its
request.prompt is taken. The CLI is started as
    kimi-cli --print --final-message-only -m kimi-code/k3 -y -p <prompt>
in an EMPTY temporary directory (nothing to read, no tools needed). The JSON is taken from the final message the way the app takes it from an
answer: the {...} match, JSON.parse, no repair. An answer that is not valid JSON, has no protocols, or a non-zero exit of the CLI is a FAILED run:
llm.json gets llmData = null and the reason in "error", never a partial result; there is no retry. The final message is saved as llm.raw1.txt.
llm.json: {module, input, metadata, seconds, request{model, prompt, ...}, requests: 1, usage: [null], error, llmData, route: "kimi-code"}.
KIMI_CLI=<path> overrides the CLI (tests use a stub). No timeout is set. Never touches together.ai / h.dataplan.top.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ASSAY = "assay"
MODEL = "kimi-code/k3"


def capture_prompt(module, protocol, assay):
    """The request of the app module, as 26_llm_extraction.js DRY=1 captures it -> (prompt, metadata)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "dry.json"
        env = {k: v for k, v in os.environ.items() if k not in ("ALLOW_TOGETHER", "MODEL", "ENDPOINT")}
        env["DRY"] = "1"
        subprocess.run(["node", str(ROOT / "scripts/26_llm_extraction.js"), str(module), str(protocol), str(out), assay],
                       env=env, check=True, capture_output=True, text=True)
        dry = json.loads(out.read_text())
    return dry["request"]["prompt"], dry["metadata"]


def parse_answer(content):
    """The app's parse: first { to last }, JSON.parse, no repair -> (llmData, error)."""
    m = re.search(r"\{[\s\S]*\}", content)
    if not m:
        return None, "no JSON object in the final message"
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        return None, f"invalid JSON: {e}"
    if not isinstance(data, dict) or not isinstance(data.get("protocols"), list) or not data["protocols"]:
        return None, "no protocols in the answer"
    return data, None


def extract(module, protocol, out_file, assay=DEFAULT_ASSAY):
    module, protocol, out_file = Path(module), Path(protocol), Path(out_file)
    prompt, metadata = capture_prompt(module, protocol, assay)
    cli = os.environ.get("KIMI_CLI", "kimi-cli")
    t0 = time.time()
    with tempfile.TemporaryDirectory() as empty:                      # nothing in the working directory
        proc = subprocess.run([cli, "--print", "--final-message-only", "-m", MODEL, "-y", "-p", prompt],
                              cwd=empty, capture_output=True, text=True)
    seconds = round(time.time() - t0)
    if proc.returncode != 0:
        data, error = None, f"kimi-cli exit {proc.returncode}: {proc.stderr.strip()[-300:]}"
    else:
        data, error = parse_answer(proc.stdout)
    result = {"module": str(module), "input": str(protocol), "metadata": metadata, "seconds": seconds,
              "request": {"model": MODEL, "route": "kimi-code", "prompt": prompt}, "requests": 1, "usage": [None],
              "error": error, "llmData": data, "route": "kimi-code"}
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.with_name(out_file.stem + ".raw1.txt").write_text(proc.stdout)
    if proc.stderr:
        out_file.with_name(out_file.stem + ".stderr.txt").write_text(proc.stderr)
    out_file.write_text(json.dumps(result, indent=2))
    n = len(data["protocols"]) if data else 0
    print(f"{out_file}: kimi-code {MODEL}, {n} protocols, {seconds}s" + (f", error: {error}" if error else ""))
    return result


# ---------------------------------------------------------------------------------------------------------------- controls
STUB = '''#!/bin/bash
# stub of `kimi-cli --print --final-message-only -m kimi-code/k3 -y -p <prompt>`: records argv and cwd, answers by STUB_MODE
printf '%s\\n' "$PWD" > "$STUB_LOG"; printf '%s\\n' "${@:1:6}" >> "$STUB_LOG"; echo "n_files=$(ls -A | wc -l | tr -d ' ')" >> "$STUB_LOG"
echo "prompt_chars=${#7}" >> "$STUB_LOG"
J=$(cat "$STUB_JSON")
case "$STUB_MODE" in
  plain) printf '%s' "$J";;
  fence) printf '```json\\n%s\\n```\\n' "$J";;
  prose) printf 'Here is the extraction:\\n%s\\nHope this helps.\\n' "$J";;
  invalid) printf '{"samples": [], "protocols": [{"name": "x", "inputs": ["a"] * 12}]}';;
  noprotocols) printf '{"samples": [], "protocols": []}';;
  exit1) printf '%s' "$J"; echo "boom" >&2; exit 3;;
esac
'''


def control():
    import importlib.util
    fails = []

    def check(name, ok, detail=""):
        print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
        if not ok:
            fails.append(name)

    case = ROOT / "work/eval_phage"
    src = next(case.glob("kimi-k3_v71_r1"))
    first = json.loads((src / "llm.json").read_text())
    md = ROOT / first["input"]
    module = ROOT / "work/eval/llm-service.local-v71.js"
    assay = first["metadata"]["assayId"]
    tmp = Path(tempfile.mkdtemp(prefix="kimi37-"))
    (tmp / "ref.json").write_text(json.dumps(first["llmData"]))
    stub = tmp / "stub.sh"
    stub.write_text(STUB)
    stub.chmod(0o755)
    os.environ.update({"KIMI_CLI": str(stub), "STUB_JSON": str(tmp / "ref.json"), "STUB_LOG": str(tmp / "stub.log")})
    prompt, _ = capture_prompt(module, md, assay)
    check("captured prompt equals the prompt the first-pass run of the same module sent", prompt == first["request"]["prompt"], f"{len(prompt)} chars")
    runs = {}
    for mode in ("plain", "fence", "prose", "invalid", "noprotocols", "exit1"):
        os.environ["STUB_MODE"] = mode
        d = tmp / mode
        runs[mode] = (extract(module, md, d / "llm.json", assay), d)
    log = (tmp / "stub.log").read_text().split("\n")
    check("CLI started in an empty directory", log[1:] and log[-3] == "n_files=0" and Path(log[0]).name != "study_dir", log[-3])
    check("CLI arguments are --print --final-message-only -m kimi-code/k3 -y -p", log[1:7] == ["--print", "--final-message-only", "-m", "kimi-code/k3", "-y", "-p"], str(log[1:7]))
    check("the whole prompt is passed as the -p argument", log[-2] == f"prompt_chars={len(prompt)}", log[-2])
    for mode in ("plain", "fence", "prose"):
        r, d = runs[mode]
        check(f"{mode}: valid llmData identical to the reference, route kimi-code", r["llmData"] == first["llmData"] and r["error"] is None and r["route"] == "kimi-code")
    for mode in ("invalid", "noprotocols", "exit1"):
        r, d = runs[mode]
        saved = json.loads((d / "llm.json").read_text())
        check(f"{mode}: failed run, llmData null, reason recorded, no valid llm.json", saved["llmData"] is None and bool(saved["error"]), saved["error"][:70])
    check("raw final message saved as llm.raw1.txt", (runs["prose"][1] / "llm.raw1.txt").read_text().startswith("Here is the extraction"))
    # downstream: 32, 27, 28 accept the produced directory
    spec = importlib.util.spec_from_file_location("s28", ROOT / "scripts/28_score_extraction.py")
    S = importlib.util.module_from_spec(spec)
    argv, sys.argv = sys.argv, sys.argv[:1]
    spec.loader.exec_module(S)
    sys.argv = argv
    for mode in ("plain", "invalid", "exit1"):
        d = runs[mode][1]
        if mode == "plain":
            ev = subprocess.run(["node", str(ROOT / "scripts/32_resolve_evidence.js"), str(d / "llm.json"), str(md)], capture_output=True, text=True)
            xl = subprocess.run(["node", str(ROOT / "scripts/27_llm_to_xlsx.js"), str(d / "llm.json"), str(md), str(d / "isa.assay.xlsx"), assay], capture_output=True, text=True)
            check("32 resolves the evidence of the produced llm.json", ev.returncode == 0 and (d / "evidence.json").exists(), ev.stdout.strip()[-90:])
            check("27 writes the xlsx", xl.returncode == 0 and (d / "isa.assay.xlsx").exists(), xl.stdout.strip()[-60:])
            check("28 run_status: ok", S.run_status(d)[0] == "ok")
            annotation = S.CASES["phage"]["annotations"]["manual annotation B"]
            gf, gr = S.facts(annotation), S.records(annotation)
            sc = S.full_score(d / "isa.assay.xlsx", annotation, gf, gr, S.source_atoms("phage"))
            ref = S.full_score(src / "isa.assay.xlsx", annotation, gf, gr, S.source_atoms("phage"))
            check("28 scores the stub run exactly like the run it copies (record F1)", abs(sc["record"]["all"]["f1"] - ref["record"]["all"]["f1"]) < 1e-12, f"{sc['record']['all']['f1']:.4f}")
            check("28 run_meta reads the produced llm.json", S.run_meta(d)["calls"] == 1 and S.run_meta(d)["seconds"] is not None)
            check("28 model label kimicode-k3", S.MODELS.get("kimicode-k3") == "Kimi-K3 (Kimi Code)")
        else:
            st = S.run_status(d)
            check(f"28 run_status of the {mode} run: failed, not an endpoint error", st[0] == "failed" and not st[1].startswith("endpoint error"), st[1][:70])
    check("control: the failed runs are scored 0 by 28", S.zero_score(S.facts(S.CASES["phage"]["annotations"]["manual annotation B"]), S.records(S.CASES["phage"]["annotations"]["manual annotation B"]))["record"]["all"]["f1"] == 0.0)
    print("CONTROLS PASS" if not fails else f"CONTROLS FAILED: {fails}")
    return not fails


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--control"]:
        sys.exit(0 if control() else 1)
    if len(a) < 3:
        sys.exit(__doc__)
    r = extract(*a[:3], *(a[3:4] or [DEFAULT_ASSAY]))
    sys.exit(1 if r["error"] else 0)
