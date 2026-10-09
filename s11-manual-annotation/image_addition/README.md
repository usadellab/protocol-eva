# Adding figures to the prompt

The five entries contain 13 figures (gels, blots, plates, curves). Two ways were tested: (1) a vision model (Gemma-4-31B) writes a description that is inserted after the image line (`scripts/45_caption_images.py`; generic, guided by the surrounding text, and a short version with an instruction written by Kimi-K3; `captions/`), (2) the real images are sent with the text at the position of the image line (`scripts/47_image_parts.js`; images flattened on white and capped at 1000 px by `48_prepare_images.py`). The images themselves are not part of this section.

## Result
11 configurations have a baseline on at least one common entry (common entries per configuration: 3 to 5); mean F1 over the common entries is lower than the baseline in 7, higher in 4. Each configuration is compared with the same model and prompt without figures on the common entries:

| Model | Prompt | Added to the prompt | Common entries | Mean F1 text only | Mean F1 with figures | Δ F1 | Δ precision, spot assay |
|---|---|---|---|---|---|---|---|
| Claude Opus | evidence prompt v7.5 | generic image descriptions | 5 | 0.512 | 0.524 | +0.012 | −0.118 |
| Claude Opus | evidence prompt v7.5 | short descriptions (v8 captioner) | 5 | 0.512 | 0.580 | +0.067 | −0.081 |
| Claude Opus | general prompt v6 | guided image descriptions | 5 | 0.591 | 0.516 | −0.074 | −0.380 |
| Gemma-4-31B (local) | evidence prompt v7.1 | generic image descriptions | 4 | 0.310 | 0.266 | −0.044 | −0.342 |
| Gemma-4-31B (local) | evidence prompt v7.1 | images interleaved | 3 | 0.352 | 0.304 | −0.048 | −0.256 |
| Gemma-4-31B (local) | evidence prompt v7.5 | generic image descriptions | 5 | 0.290 | 0.293 | +0.003 | −0.266 |
| Gemma-4-31B (local) | evidence prompt v7.5 | images interleaved | 3 | 0.356 | 0.353 | −0.003 | −0.326 |
| Gemma-4-31B (local) | general prompt v6 | generic image descriptions | 5 | 0.334 | 0.290 | −0.044 | −0.222 |
| Gemma-4-31B (local) | general prompt v6 | guided image descriptions | 5 | 0.334 | 0.282 | −0.052 | −0.264 |
| Kimi-K3 (Kimi Code) | evidence prompt v7.5 | generic image descriptions | 5 | 0.397 | 0.172 | −0.226 | −0.595 |
| Kimi-K3 (Kimi Code) | general prompt v6 | guided image descriptions | 5 | 0.242 | 0.340 | +0.097 | +0.189 |

Real images were tested only with Gemma-4-31B (local), on 3 entries and two prompts. On the spot assay entry the precision changed in 11 configurations by -0.595 to +0.189 (lower in 10); this table does not say why.
Scores of every configuration, with entries, runs and failed runs: `caption_and_image_conditions.csv`.

## Draft facts visible in the figures (`draft_image_facts/`)
A draft list of the facts visible in the 13 figures was written by a Claude model (Sonnet 5.5) and checked against two independent readings of the same images, R2 (a fresh Sonnet subagent that saw only the images and a generic schema) and R3 (`claude -p --model haiku`, one call per image). Of 263 printed facts (labels, marks, legends, values) R2 supports 258 (98%), R3 242 (92%), both 240 (91%) by a lexical rule (at least 0.8 of the tokens of the fact occur in the reader's text). All three readers are Claude models and the rule is lenient for short values (a bare number counts when it occurs anywhere in the answer), so the agreement shows that the readings are reproducible, not that they are correct. The draft has not been reviewed by a person and is not a manual annotation.
`python3.13 draft_image_facts/score_agreement.py` recomputes the agreement from the draft and the two readings; the one external check of the colour codes against annotation B of UX511 reads the shipped annotation spreadsheet.