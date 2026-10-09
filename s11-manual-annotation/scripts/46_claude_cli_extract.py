#!/opt/homebrew/bin/python3.13
"""One extraction through `claude -p` (print mode, no tools, empty working directory) -> llm.json in the format of 26_llm_extraction.js, plus cli_output.json for 28.

  46_claude_cli_extract.py <llm-service.js> <protocol.md> <out.json> [assayId]      env CLAUDE_MODEL (default claude-opus-5-5), CLAUDE_CONFIG_DIR (subscription)
Prompt = exactly what the app module builds (37's capture_prompt, DRY run); answer parsing = the app's (37's parse_answer): first { to last }, JSON.parse, no repair.
Invalid JSON / non-zero exit = failed run (llmData null, reason in "error"), no retry. No timeout. Never touches together.ai.
"""
import importlib.util, json, os, subprocess, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("k37", ROOT / "scripts/37_kimi_cli_extract.py")
K = importlib.util.module_from_spec(spec); spec.loader.exec_module(K)
MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")

def extract(module, protocol, out_file, assay=K.DEFAULT_ASSAY):
    out_file = Path(out_file)
    prompt, metadata = K.capture_prompt(Path(module), Path(protocol), assay)
    t0 = time.time()
    with tempfile.TemporaryDirectory() as empty:
        proc = subprocess.run(["claude", "-p", "--model", MODEL, "--output-format", "json", "--tools", "", "--disable-slash-commands", "--strict-mcp-config"],
                              input=prompt, cwd=empty, capture_output=True, text=True)
    seconds = round(time.time() - t0)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.with_name("cli_output.json").write_text(proc.stdout)
    cli, text, cost = {}, "", None
    try:
        cli = json.loads(proc.stdout)
        if isinstance(cli, list):                       # this CLI version emits the event list; the result event holds the answer
            cli = next((x for x in cli if isinstance(x, dict) and x.get("type") == "result"), {})
        text = cli.get("result") or ""; cost = cli.get("total_cost_usd")
    except json.JSONDecodeError:
        pass
    if proc.returncode != 0 or cli.get("is_error"):
        data, error = None, f"claude exit {proc.returncode}: {(text or proc.stderr).strip()[-300:]}"
    else:
        data, error = K.parse_answer(text)
    if proc.stderr:
        out_file.with_name("cli.err").write_text(proc.stderr)
    out_file.with_name(out_file.stem + ".raw1.txt").write_text(text)
    out_file.write_text(json.dumps({"source": str(out_file.with_name("cli_output.json")), "model": [MODEL], "module": str(module), "input": str(protocol), "metadata": metadata,
                                    "seconds": seconds, "cost_usd": cost, "request": {"model": MODEL, "route": "claude-p", "prompt": prompt}, "requests": 1, "error": error,
                                    "llmData": data, "route": "claude-p"}, indent=2))
    print(f"{out_file}: claude -p {MODEL}, {len(data['protocols']) if data else 0} protocols, {seconds}s" + (f", error: {error}" if error else ""))

if __name__ == "__main__":
    extract(*sys.argv[1:])
