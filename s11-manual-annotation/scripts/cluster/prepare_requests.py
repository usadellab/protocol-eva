#!/opt/homebrew/bin/python3.13
"""Build the chat-completion request bodies of the cluster run: exactly the prompt the app module builds for each entry (26_llm_extraction.js with DRY=1, as 37_kimi_cli_extract.py does),
sampling parameters of the model card (work/eval/model_params_cluster.json). One request per entry and repeat -> work/cluster/requests/<case>_<rep>.json  {model, messages, temperature, top_p, top_k, max_tokens, stream:false}"""
import importlib.util, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("k37", ROOT / "scripts/37_kimi_cli_extract.py"); K = importlib.util.module_from_spec(spec); spec.loader.exec_module(K)
import os
SET = os.environ.get("SET", "")                      # "" = the Gemma set (requests/, responses/); otherwise requests_<SET>/
MODEL_NAME = os.environ.get("MODEL_NAME", "gemma-4-31b-it")
PARAMS = json.loads(os.environ["PARAMS_JSON"]) if os.environ.get("PARAMS_JSON") else json.loads((ROOT / "work/eval/model_params_cluster.json").read_text())["gemma-4-31b-it"]
ENTRIES = {"sdy1": ("work/eval_sdy1", "SDY1_phenotyping_SSD1"), "phage": ("work/eval_phage", "EXP001_BAS33_bacteriophage_sequencing"), "ux511": ("work/eval_ux511", "Generation_of_UX511-523"),
           "biolector034": ("work/eval_biolector034", "Pima1_Malt_Glc_BioLector-034"), "pux782": ("work/eval_pux782", "Generation_of_pUX782-787")}
PROMPTS = sys.argv[1:] or ["v6"]
out = ROOT / ("work/cluster/requests" + (("_" + SET) if SET else "")); out.mkdir(parents=True, exist_ok=True)
for tag in PROMPTS:
    module = ROOT / f"work/eval/llm-service.local-{tag}.js"
    for case, (d, assay) in ENTRIES.items():
        md = next((ROOT / d / "input").glob("*.md"))
        prompt, metadata = K.capture_prompt(module, md, assay)
        for rep in ("r1", "r2", "r3"):
            body = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}], **PARAMS, "stream": False}
            (out / f"{case}_{tag}_{rep}.json").write_text(json.dumps({"body": body, "case": case, "prompt": tag, "rep": rep, "input": str(md.relative_to(ROOT)), "assay": assay, "metadata": metadata}))
        print(tag, case, len(prompt), "chars")
