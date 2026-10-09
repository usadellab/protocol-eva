# Agreement of the draft image facts with two independent readings (2026-10-06)

Draft: `image_facts_draft_by_claude.json` (read by Claude, Sonnet 5.5, this window). R2: a fresh Sonnet subagent that saw only the 13 images and a generic extraction schema (no draft, no annotation, no text of the entries). R3: `claude -p --model haiku`, one call per image, same schema. Lexical rule and limits: see the header of `score_agreement.py`. **Observation facts (band/growth/curve statements, medium confidence) are not scored automatically.**

| Figure | facts | printed (scored) | R2 supports | R3 supports | both | observations | colour sequence R2 / R3 |
|---|---|---|---|---|---|---|---|
| phage:gelp1 | 19 | 11 | 11 | 11 | 11 | 5 | - |
| sdy1:4355ff27 | 32 | 25 | 25 | 23 | 23 | 6 | - |
| sdy1:3bc807ec | 29 | 25 | 24 | 22 | 22 | 3 | - |
| biolector034:38a110c5 | 46 | 34 | 32 | 28 | 26 | 3 | - |
| biolector034:5c18fdef | 38 | 29 | 27 | 19 | 19 | 2 | - |
| ux511:76a1dde7 | 24 | 19 | 19 | 19 | 19 | 4 | - |
| ux511:e9e15b0e | 27 | 20 | 20 | 20 | 20 | 6 | - |
| ux511:bc82c478 | 46 | 15 | 15 | 15 | 15 | 4 | = / differs (12 read) |
| ux511:be57156f | 39 | 13 | 13 | 13 | 13 | 3 | = / differs (10 read) |
| ux511:6fed9d0a | 44 | 15 | 15 | 15 | 15 | 2 | = / differs (9 read) |
| ux511:84dc38ff | 39 | 14 | 14 | 14 | 14 | 4 | = / differs (9 read) |
| ux511:3acf4cbb | 26 | 12 | 12 | 12 | 12 | 3 | = / differs (4 read) |
| pux782:grafik | 37 | 31 | 31 | 31 | 31 | 4 | - |
| **all** | 446 | 263 | 258 (98%) | 242 (92%) | 240 (91%) | 49 | |

External check of the draft's blot colour codes against annotation B (curator, UX511): 44 of 44 lanes that B marks yes/no agree.

## Printed facts the readers did not support (first 6 per figure and reader)

- sdy1:4355ff27 R3_haiku_cli: 4355ff27-012 Nikkomycin Z [5 µM]; 4355ff27-023 Nikkomycin Z [5 µM]
- sdy1:3bc807ec R2_sonnet_subagent: 3bc807ec-018 arrow followed by 'no growth'
- sdy1:3bc807ec R3_haiku_cli: 3bc807ec-006 caspofungin [100 nM]; 3bc807ec-007 caspofungin [500 nM]; 3bc807ec-018 arrow followed by 'no growth'
- biolector034:38a110c5 R2_sonnet_subagent: 38a110c5-009 1600; 38a110c5-019 1200
- biolector034:38a110c5 R3_haiku_cli: 38a110c5-006 + Glc: Pcrg, Prpl10; + Ara: Pcrg, Prpl10; 38a110c5-011 + Glc: Pcrg, Prpl10; + Ara: Pcrg, Prpl10; 38a110c5-016 + Glc: Pima1, Prpl10, Pima1short; + Malt; 38a110c5-021 + Glc: Pima1, Prpl10, Pima1short; + Malt; 38a110c5-026 + Glc: Pcrg, Prpl10; + Ara: Pcrg, Prpl10; 38a110c5-031 + Glc: Pcrg, Prpl10; + Ara: Pcrg, Prpl10
- biolector034:5c18fdef R2_sonnet_subagent: 5c18fdef-007 800; 5c18fdef-022 800
- biolector034:5c18fdef R3_haiku_cli: 5c18fdef-007 800; 5c18fdef-009 + H2O: Phsp70, Prpl10, Potef; + Nitrogen; 5c18fdef-014 + H2O: Phsp70, Prpl10; + Nitrogen: Phsp7; 5c18fdef-019 + H2O: Potef; + Nitrogen: Potef; 5c18fdef-022 800; 5c18fdef-024 + H2O: Phsp70, Prpl10, Potef; + Nitrogen

## Observations (hand comparison, not scored)

The 49 draft observations (band positions against the markers, growth by plate, curve levels; confidence medium, all 'approximate') were compared by hand with the observations of R2 (`reading_R2_subagent_sonnet.json`). No contradiction was found; R2 lists 2-5 observations per figure, so most draft observations are simply not mentioned by it. Points where R2 says something the draft does not: UX523 lane 8 on the repeat blot (3acf4cbb) has bands near 10000 and 8000 bp; UX512 lane 3 on bc82c478 shows no clear band; UX517 lane 1 on 6fed9d0a shows no clear band; pUX784 is slightly lower than pUX783 on the digest gel 76a1dde7. These are candidates for the reviewer. R3 (haiku) observations were not compared in detail: R3 (haiku) reproduced the colour code on none of the 5 blots (lane-by-lane agreement with the draft: 10 of 12, 5 of 10, 7 of 9 and 2 of 4 lanes on the four blots where it listed the same number of lanes; on 6fed9d0a it listed 9 of 12 lanes), so its observations are the weakest reading; R2 reproduced the colour sequence on all 5.

## Limits

- All three readers are Claude models; the agreement says that the printed text and the colour codes are reproducible, not that a human curator would agree. The one independent check (annotation B, 44 of 44 lanes) concerns only the green/black codes of UX511.
- Lexical support is lenient for short values (a bare number such as 800 is supported when it occurs anywhere in a reader's answer).
- R2 is a fresh subagent of the same model family as the draft; it was told nothing but the schema and the paths.
