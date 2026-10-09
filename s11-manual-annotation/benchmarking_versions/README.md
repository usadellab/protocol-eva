# Benchmarking prompt versions

**Files.** `prompts/prompt_<version>.txt` is the prompt of the application's LLM module as a JavaScript template literal: the text between the backticks of `promptTemplate = \`...\`` in the module of that version, unchanged, including the `${...}` expressions. `deployed` is the prompt of the published tool before this study; v6 is the prompt of Supplement S11.
`prompts/prompt_v6_as_sent.txt` is the text a model receives for the spot assay entry (recorded in the run, `request.prompt`); the check in the build script renders `prompt_v6.txt` with the values below and obtains this text up to a blank line and the trailing newline of the file (the audit found the blank line at the start, produced by `${contextInfo}`).

| Placeholder in the template | Value |
|---|---|
| `${chunk}` | the markdown text of the entry (`datasets/protocol_inputs/<entry>.md`), or one part of it when the entry exceeds the context window and is split into chunks |
| `${contextInfo}` | `Protocol File: <file name>`, `Protocol Path: <path in the ARC>`, `Assay/Experiment ID: <assay identifier>`, one per line (the values of the spot assay run are in `prompt_v6_as_sent.txt`) |
| `${chunkInfo}` | empty for a single request; ` (chunk i/n)` when the entry is split |
| `${chunks.length > 1 ? ' section' : ''}` | empty for a single request |
| `${metadata.protocolPath ? ...}` | ` (<Protocol Path>)` |

**Versions** (the labels are those of the score files; `prompts/` has the text of every version):

| Version | Label in the score files | Text | Configurations scored in this section |
|---|---|---|---|
| deployed | deployed prompt | `prompts/prompt_deployed.txt` | 1 |
| v2 | general prompt v2 | `prompts/prompt_v2.txt` | 0 |
| v3 | general prompt v3 | `prompts/prompt_v3.txt` | 1 |
| v4 | general prompt v4 | `prompts/prompt_v4.txt` | 1 |
| v5 | general prompt v5 | `prompts/prompt_v5.txt` | 1 |
| v6 | general prompt v6 | `prompts/prompt_v6.txt` | 10 |
| v7 | evidence prompt v7 | `prompts/prompt_v7.txt` | 5 |
| v7.1 | evidence prompt v7.1 (table quoting) | `prompts/prompt_v7.1.txt` | 4 |
| v7.2 | evidence prompt v7.2 (Kimi-assisted candidate) | `prompts/prompt_v7.2.txt` | 0 |
| v7.3 | evidence prompt v7.3 (Kimi-assisted candidate) | `prompts/prompt_v7.3.txt` | 0 |
| v7.4 | evidence prompt v7.4 (Kimi-assisted candidate) | `prompts/prompt_v7.4.txt` | 2 |
| v7.5 | evidence prompt v7.5 (Kimi-assisted candidate) | `prompts/prompt_v7.5.txt` | 5 |
| v7.6 | evidence prompt v7.6 (Kimi-assisted candidate) | `prompts/prompt_v7.6.txt` | 1 |
| v7.7 | evidence prompt v7.7 (Kimi-assisted candidate) | `prompts/prompt_v7.7.txt` | 1 |
| v8 | evidence prompt v8 (Kimi: descriptions supplementary) | `prompts/prompt_v8.txt` | 1 |
| v9 | evidence prompt v9 (Kimi rewrite: plain steps, one example) | `prompts/prompt_v9.txt` | 5 |
| v9.1 | evidence prompt v9.1 (v9 + granularity fix) | `prompts/prompt_v9.1.txt` | 2 |
| v10 | evidence prompt v10 (Kimi: v6 rules + v9 wording) | `prompts/prompt_v10.txt` | 3 |

`kimi_prompt_workflow/` holds what was used to write v8 to v10 with Kimi-K3 through the Kimi Code CLI: the briefs (`instructions_*.md`), the answers (`ans_*.md`), the rewrite tool `rewrite_prompt.py` and the checks that it runs before an answer is accepted (every placeholder exactly once, no backtick or `${`, every schema key present, no all-caps word, shorter than the base prompt, `check_prompt_leakage.py` against the vocabulary of the annotations, the module renders under node). v9 was a whole-prompt rewrite requested to fix the linking rule, avoid all-caps emphasis, use plain steps and merge the examples into the first example JSON.

## Scores of every text-only configuration
Mean F1 over the entries run, `entries` = number of entries (of five) on which the configuration was run, `Δ F1` = change against prompt version 6 of the same model on the same entries (blank where the model has no v6 run on a common entry). Rows with fewer than five entries are not comparable with the others. Failed runs count 0. Full per-entry means, sd, n, precision and recall: `prompt_versions_text_only.csv`; all differences: `../results/delta_vs_baseline.csv`.

Prompt versions other than v6 against v6, same model, same entries: 33 configurations have a baseline on at least one common entry (common entries per configuration: 1 to 5); mean F1 over the common entries is lower than the baseline in 26, higher in 7. 7 of these configurations score higher than version 6 (DeepSeek-V4.1-Flash v4 (+0.283, 2 entries), DeepSeek-V4.1-Flash v5 (+0.197, 2 entries), DeepSeek-V4.1-Flash v7 (+0.113, 4 entries), GLM-4.7-Flash (local LM Studio) v7.1 (+0.025, 4 entries), Gemma-4-31B (local LM Studio) v9 (+0.018, 3 entries), Kimi-K3 (Kimi Code) v7.1 (+0.215, 1 entries), Kimi-K3 (Kimi Code) v7.5 (+0.155, 5 entries)).

| Model | Prompt | Entries | Runs | Failed | Mean F1 | Δ F1 vs v6 |
|---|---|---|---|---|---|---|
| Claude Opus | evidence prompt v10 | 5 | 5 | 0 | 0.511 | −0.080 |
| Claude Opus | evidence prompt v7.5 | 5 | 5 | 0 | 0.512 | −0.078 |
| Claude Opus | evidence prompt v9 | 5 | 5 | 0 | 0.421 | −0.169 |
| Claude Opus | general prompt v6 | 5 | 5 | 0 | 0.591 |  |
| Claude Sonnet 5.5 | evidence prompt v10 | 5 | 5 | 0 | 0.414 | −0.004 |
| Claude Sonnet 5.5 | evidence prompt v9 | 5 | 5 | 0 | 0.397 | −0.022 |
| Claude Sonnet 5.5 | evidence prompt v9.1 | 5 | 5 | 1 | 0.301 | −0.118 |
| Claude Sonnet 5.5 | general prompt v6 | 5 | 15 | 0 | 0.419 |  |
| DeepSeek-V4.1-Flash | deployed prompt | 1 | 1 | 0 | 0.294 | −0.233 |
| DeepSeek-V4.1-Flash | evidence prompt v7 | 4 | 6 | 0 | 0.385 | +0.113 |
| DeepSeek-V4.1-Flash | general prompt v3 | 1 | 1 | 0 | 0.430 | −0.097 |
| DeepSeek-V4.1-Flash | general prompt v4 | 2 | 3 | 0 | 0.638 | +0.283 |
| DeepSeek-V4.1-Flash | general prompt v5 | 2 | 2 | 0 | 0.552 | +0.197 |
| DeepSeek-V4.1-Flash | general prompt v6 | 5 | 15 | 2 | 0.282 |  |
| GLM-4.7-Flash (local LM Studio) | evidence prompt v7 | 4 | 6 | 0 | 0.218 | −0.028 |
| GLM-4.7-Flash (local LM Studio) | evidence prompt v7.1 | 4 | 12 | 1 | 0.272 | +0.025 |
| GLM-4.7-Flash (local LM Studio) | evidence prompt v7.5 | 2 | 6 | 0 | 0.249 | −0.073 |
| GLM-4.7-Flash (local LM Studio) | general prompt v6 | 5 | 15 | 1 | 0.262 |  |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v10 | 5 | 15 | 0 | 0.300 | −0.029 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v7 | 5 | 15 | 0 | 0.276 | −0.054 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v7.1 | 5 | 15 | 1 | 0.259 | −0.070 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v7.4 | 5 | 15 | 0 | 0.299 | −0.030 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v7.5 | 5 | 15 | 0 | 0.273 | −0.056 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v7.6 | 5 | 15 | 0 | 0.295 | −0.034 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v7.7 | 5 | 15 | 0 | 0.286 | −0.043 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v8 | 5 | 15 | 0 | 0.270 | −0.059 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v9 | 5 | 15 | 0 | 0.295 | −0.034 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | evidence prompt v9.1 | 5 | 15 | 0 | 0.276 | −0.053 |
| Gemma-4-31B (cluster vLLM, QAT w4a16) | general prompt v6 | 5 | 15 | 0 | 0.329 |  |
| Gemma-4-31B (local LM Studio) | evidence prompt v7 | 4 | 8 | 0 | 0.312 | −0.054 |
| Gemma-4-31B (local LM Studio) | evidence prompt v7.1 | 4 | 12 | 1 | 0.310 | −0.056 |
| Gemma-4-31B (local LM Studio) | evidence prompt v7.4 | 4 | 12 | 0 | 0.321 | −0.046 |
| Gemma-4-31B (local LM Studio) | evidence prompt v7.5 | 5 | 15 | 1 | 0.290 | −0.044 |
| Gemma-4-31B (local LM Studio) | evidence prompt v9 | 3 | 9 | 0 | 0.229 | +0.018 |
| Gemma-4-31B (local LM Studio) | general prompt v6 | 5 | 15 | 0 | 0.334 |  |
| Kimi-K3 (Kimi Code) | evidence prompt v7.1 | 1 | 3 | 1 | 0.256 | +0.215 |
| Kimi-K3 (Kimi Code) | evidence prompt v7.5 | 5 | 5 | 1 | 0.397 | +0.155 |
| Kimi-K3 (Kimi Code) | evidence prompt v9 | 5 | 5 | 3 | 0.185 | −0.058 |
| Kimi-K3 (Kimi Code) | general prompt v6 | 5 | 15 | 6 | 0.242 |  |
| MiniMax-M3-4bit (local oMLX) | evidence prompt v7 | 4 | 4 | 2 | 0.152 | −0.137 |
| MiniMax-M3-4bit (local oMLX) | general prompt v6 | 5 | 15 | 5 | 0.301 |  |
| Nemotron-3-Ultra-550B (OpenRouter free) | general prompt v6 | 5 | 5 | 1 | 0.309 |  |
| dots-3-note-preview (OpenRouter free) | general prompt v6 | 5 | 5 | 0 | 0.372 |  |
