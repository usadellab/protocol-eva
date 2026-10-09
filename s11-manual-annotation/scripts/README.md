# Scripts

Scripts are given as used in the study. The scorer expects the working tree of the study (`work/eval*/<run folder>/llm.json`, the annotation files, `scripts/`) and are not packaged for a one-line run; the scripts marked **runs here** work inside this folder. Script numbers are those of the study's script folder, so they have gaps. Names of people, hosts and user directories of the study were replaced: cluster paths by `$LLM_ROOT`, `$CLUSTER_HOME`, `$CLUSTER_DATA`; the name of the experimenter in the example metadata of `27_llm_to_xlsx.js` by `experimenter` and the default assay id of the extraction scripts by `assay`.

| Script | Purpose |
|---|---|
| `26_llm_extraction.js` | Runs the application's LLM module headless (jsdom) on one entry; one request; writes `llm.json` (request, answer, usage). Options by environment: `MODEL`, `ENDPOINT`, `PARAMS_FILE`, `IMAGES`. |
| `27_llm_to_xlsx.js` | Turns the answer into the assay spreadsheet with the application's ISA code. |
| `28_score_extraction.py` | The scorer: record precision, recall, F1 of run folders against the manual annotation, controls with deliberately wrong input; writes `scores.json` and the leaderboard. **runs here** as a module for `score_agreement.py`. |
| `verify_scores.py` | Independent recomputation of the scores (second matching algorithm; one worker process per stored score); needs the run folders. |
| `build_run_table.py` | Writes `results/runs.csv` and `results/entries.csv` from the run folders and the scores; needs the run folders. |
| `recompute_statements.py` | **runs here**: the statements of the text (prompt versions against version 6, figure additions, traceable prompts) from `results/all_configurations.csv` -> `results/statements.csv`. |
| `make_all_benchmarks.py` | Table of all configurations from the leaderboard. |
| `score_agreement.py` | **runs here**: agreement of manual annotations A and B of the bacteriophage entry. |
| `recompute_table_s11_2.py`, `check_table_s11_2.py` | **run here**: recompute Table S11-2 from `results/runs.csv`; compare README and supplement. |
| `33_eln_to_input_md.js`, `40_html_to_app_md.js` | Entry (eLabFTW export or HTML) to the markdown the application sends. `40_html_to_app_md.js` rewrites links to the eLabFTW server of the study's institute; the host in this copy is a placeholder. |
| `37_kimi_cli_extract.py`, `46_claude_cli_extract.py` | The same extraction through the Kimi Code and Claude Code CLIs. |
| `cluster/` | vLLM server jobs (`vllm_serve`, `vllm_gemma2`, `vllm_env`, `hf_download`), the request builder `prepare_requests.py`, the clients `client.py` and `client2.py` with their job scripts `client_set` and `client_multi`, and `ingest_responses.py`. |
