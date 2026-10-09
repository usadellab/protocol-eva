#!/opt/homebrew/bin/python3.13
"""Turn the answers the cluster client saved (responses/<case>_<rep>.json) into run directories work/eval_<case>/gemma4-31b-vllm_v6_<rep>/ in the format of the other routes (llm.json, llm.raw1.txt, xlsx via 27).
Parsing = the app's: first { to last }, JSON.parse, no repair (a fenced answer is fine, the fence is outside the braces); an answer that is not valid JSON is a failed run (llmData null, scored 0); a request that got NO answer is an endpoint error and creates nothing.
  ingest_responses.py [--fetch]    --fetch first copies the responses from the cluster (scp)"""
import importlib.util, json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("k37", ROOT / "scripts/37_kimi_cli_extract.py"); K = importlib.util.module_from_spec(spec); spec.loader.exec_module(K)
import os
SET = os.environ.get("SET", ""); SLUG = os.environ.get("SLUG", "gemma4-31b-vllm"); SUF = ("_" + SET) if SET else ""
RESP = ROOT / ("work/cluster/responses" + SUF); RESP.mkdir(parents=True, exist_ok=True)
REQ = ROOT / ("work/cluster/requests" + SUF)
if "--fetch" in sys.argv:
    subprocess.run(["scp", "-q", "cluster:$LLM_ROOT/data/responses" + SUF + "/*.json", str(RESP) + "/"], check=False)
for f in sorted(RESP.glob("*.json")):
    rec = json.loads(f.read_text()); req = json.loads((REQ / f.name).read_text())
    case, rep, tag = req["case"], req["rep"], req.get("prompt", "v6")
    d = ROOT / ("work/eval" + ("_" + case)) / f"{SLUG}_{tag}_{rep}"
    if (d / "llm.json").exists(): continue
    ans = rec["response"]; choice = ans["choices"][0]; content = choice["message"].get("content") or ""
    data, error = K.parse_answer(content)
    if choice.get("finish_reason") == "length" and error: error += " (finish_reason length: answer cut at max_tokens)"
    d.mkdir(parents=True, exist_ok=True)
    (d / "llm.raw1.txt").write_text(content)
    (d / "llm.json").write_text(json.dumps({"module": f"work/eval/llm-service.local-{tag}.js", "input": req["input"], "metadata": req["metadata"], "seconds": rec["seconds"],
        "request": {"model": os.environ.get("MODEL_DESC", "gemma-4-31b-it (vLLM on cluster)"), "route": "cluster-vllm", "prompt": req["body"]["messages"][0]["content"],
                    "settings": {k: v for k, v in req["body"].items() if k != "messages"}}, "requests": 1, "usage": [ans.get("usage")], "error": error, "llmData": data, "route": "cluster-vllm"}, indent=2))
    print(case, tag, rep, "failed: " + error[:80] if error else f"{len(data['protocols'])} protocols", rec["seconds"], "s")
    if data:
        md = ROOT / req["input"]
        if tag != "v6":                                       # evidence prompts: resolve the quotes against the text the model saw
            subprocess.run(["node", str(ROOT / "scripts/32_resolve_evidence.js"), str(d / "llm.json"), str(md)], capture_output=True)
        subprocess.run(["node", str(ROOT / "scripts/27_llm_to_xlsx.js"), str(d / "llm.json"), str(md), str(d / "isa.assay.xlsx"), req["assay"]], capture_output=True)
