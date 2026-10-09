# image_facts_draft_by_claude (DRAFT, 2026-10-06)

DRAFT. Read from the images with vision by Claude (Sonnet 5.5, window image-reading session, 2026-10-06). NOT a manual annotation, NOT manual annotation, not to be mixed with annotations A and B. Needs review by the curator / user before any use in a manuscript.

images opened and viewed (prepared flat PNG or original; label rows of the blots enlarged 2x); every fact is one read-off. Second independent readings and the per-image agreement are in image_facts_agreement.md.

Not a manual annotation and not manual annotation; keep apart from manual annotations A and B. Review by the curator / user needed before any manuscript use.

446 facts for 13 figures. Fields: id, figure (`case:uuid8`), kind, locator, attribute, value, confidence (high = printed text or unambiguous; medium = an approximate reading of band position, colour or growth).
Full machine-readable form: `image_facts_draft_by_claude.json`. Generator (the facts are authored there): `build_draft_claude.py`. Agreement with the independent readings: `image_facts_agreement.md`.


## phage:gelp1 (19 facts)

| id | kind | locator | attribute | value | conf |
|---|---|---|---|---|---|
| gelp1-001 | label | lane 1 | lane label | BD_R1 | high |
| gelp1-002 | label | lane 2 | lane label | BD_R2 | high |
| gelp1-003 | label | lane 3 | lane label | BD_R3 | high |
| gelp1-004 | label | lane 4 | lane label | B_R1 | high |
| gelp1-005 | label | lane 5 | lane label | B_R2 | high |
| gelp1-006 | label | lane 6 | lane label | B_R3 | high |
| gelp1-007 | label | lane 7 | lane label | 1kb Plus ladder | high |
| gelp1-008 | layout | gel | number of lanes | 7 (6 samples + 1 ladder) | high |
| gelp1-009 | layout | gel | ladder position | right-most lane (lane 7) | high |
| gelp1-010 | mark | right side, lines to the ladder | size mark | 20 kb | high |
| gelp1-011 | mark | right side, lines to the ladder | size mark | 5 kb | high |
| gelp1-012 | mark | right side, lines to the ladder | size mark | 1.5 kb | high |
| gelp1-013 | mark | right side, lines to the ladder | size mark | 0.5 kb | high |
| gelp1-014 | observation | lanes 1-6 | signal type | broad smear from the wells to below 0.5 kb in every sample lane; no discrete band | high |
| gelp1-015 | observation | lane 1 (BD_R1) | signal intensity | strongest smear of all lanes, most intense between about 5 kb and 1.5 kb | medium |
| gelp1-016 | observation | lanes 2-6 | signal intensity | weaker smears than lane 1; lane 5 (B_R2) and lane 6 (B_R3) denser than lanes 2-4 | medium |
| gelp1-017 | observation | ladder lane | ladder | about 15 discrete bands; brightest at the 5 kb, 1.5 kb and 0.5 kb marks | medium |
| gelp1-018 | observation | wells | faint band | faint high-molecular-weight band near the wells (about 20 kb mark) in several lanes | medium |
| gelp1-019 | layout | image | transparency | RGBA PNG; labels are black text on a transparent background (not readable on black) | high |

## sdy1:4355ff27 (32 facts)

| id | kind | locator | attribute | value | conf |
|---|---|---|---|---|---|
| 4355ff27-001 | label | top left | title | 48h, CM, 28°C | high |
| 4355ff27-002 | label | top left list | strain listed | AB33 | high |
| 4355ff27-003 | label | top left list | strain listed | UMa2700 | high |
| 4355ff27-004 | label | top left list | strain listed | UMa2950 | high |
| 4355ff27-005 | label | top | culture note | over night main culture in glucose and/or arabinose | high |
| 4355ff27-006 | label | dilution wedge | dilution range | 10^7 to 10^2 | high |
| 4355ff27-007 | label | upper row, plate 1 | plate title | CM [glucose] | high |
| 4355ff27-008 | label | upper row, plate 2 | plate title | CM [arabinose] | high |
| 4355ff27-009 | label | upper row, plate 3 | plate title | CFW [20 µM] | high |
| 4355ff27-010 | label | upper row, plate 4 | plate title | Congo red [150 µM] | high |
| 4355ff27-011 | label | upper row, plate 5 | plate title | caspofungin [500 nM] | high |
| 4355ff27-012 | label | upper row, plate 6 | plate title | Nikkomycin Z [5 µM] | high |
| 4355ff27-013 | label | upper row, plate 7 | plate title | SDS [0.1%] | high |
| 4355ff27-014 | label | upper row, plate 8 | plate title | SDS [0.05%] | high |
| 4355ff27-015 | label | row labels, left | row label | AB33 | high |
| 4355ff27-016 | label | row labels, left | row label | Pssd1-SSD1-GFP | high |
| 4355ff27-017 | label | row labels, left | row label | Pcrg1-SSD1-GFP (OFF) | high |
| 4355ff27-018 | label | row labels, left | row label | Pcrg1-SSD1-GFP (ON) | high |
| 4355ff27-019 | layout | upper row of plates | spot rows per plate | 6 (AB33, Pssd1-SSD1-GFP, 2 x Pcrg1 OFF, 2 x Pcrg1 ON; the vertical bars mark the OFF rows and the ON rows) | medium |
| 4355ff27-020 | label | lower row, plate 1 | plate title | CM [glucose] | high |
| 4355ff27-021 | label | lower row, plate 2 | plate title | CFW [20 µM] | high |
| 4355ff27-022 | label | lower row, plate 3 | plate title | caspofungin [500 nM] | high |
| 4355ff27-023 | label | lower row, plate 4 | plate title | Nikkomycin Z [5 µM] | high |
| 4355ff27-024 | label | lower row, right | annotation | glucose Pcrg1-OFF condition | high |
| 4355ff27-025 | label | bottom text | conclusion 1 | conditional SSD1-mutant sensitive to chitin synthase inhibitor Nikkomycin Z but not CFW which binds to chitin, looks slightly more growth; surprisingly the conditional SSD1-mutant was way more resistant to ß-glucan inhibitor CR | high |
| 4355ff27-026 | label | bottom text | conclusion 2 | overexpression of SSD1 (only in pre-culture) was sufficient to produce a strong sensitivity phenotype in presence of caspofungin, inhibiting ß-glucan synthesis not present in the conditional-mutant | high |
| 4355ff27-027 | observation | SDS [0.1%] and SDS [0.05%] plates | growth | no visible growth in any row | high |
| 4355ff27-028 | observation | Nikkomycin Z [5 µM] plate | growth by row | Pcrg1 OFF rows: strongly reduced (almost no spots); Pcrg1 ON, AB33 and Pssd1 rows: growth | medium |
| 4355ff27-029 | observation | caspofungin [500 nM] plate | growth by row | Pcrg1 ON rows: strongly reduced (only small colonies at low dilution); other rows: growth | medium |
| 4355ff27-030 | observation | CFW [20 µM] plate | growth | reduced in all rows (first one or two spots only) | medium |
| 4355ff27-031 | observation | Congo red [150 µM] plate | growth by row | only the Pcrg1 OFF rows show faint spots; other rows no growth | medium |
| 4355ff27-032 | observation | CM [glucose] and CM [arabinose] plates | growth | all rows grow with dilution series visible | high |

## sdy1:3bc807ec (29 facts)

| id | kind | locator | attribute | value | conf |
|---|---|---|---|---|---|
| 3bc807ec-001 | label | top left | title | 30.01.25 48h | high |
| 3bc807ec-002 | label | plate 1 | plate title | CM [glucose] | high |
| 3bc807ec-003 | label | plate 2 | plate title | CM [arabinose] | high |
| 3bc807ec-004 | label | plate 3 | plate title | CFW [10 µM] | high |
| 3bc807ec-005 | label | plate 4 | plate title | CFW [20 µM] | high |
| 3bc807ec-006 | label | plate 5 | plate title | caspofungin [100 nM] | high |
| 3bc807ec-007 | label | plate 6 | plate title | caspofungin [500 nM] | high |
| 3bc807ec-008 | label | plate 7 | plate title | Nikkomycin Z [2.5 µM] | high |
| 3bc807ec-009 | label | plate 8 | plate title | Nikkomycin Z [5 µM] | high |
| 3bc807ec-010 | label | row labels, left | row label | AB33 | high |
| 3bc807ec-011 | label | row labels, left | row label | Pssd1-SSD1-GFP | high |
| 3bc807ec-012 | label | row labels, left | row label | Pcrg1-SSD1-GFP (OFF) | high |
| 3bc807ec-013 | label | row labels, left | row label | Pcrg1-SSD1-GFP (ON) | high |
| 3bc807ec-014 | layout | plates | spot rows per plate | 5 visible rows (Pssd1-SSD1-GFP, 2 x OFF, 2 x ON); AB33 row without growth | medium |
| 3bc807ec-015 | legend | legend below the plates | inhibitor without growth | Congo red [150 µM] | high |
| 3bc807ec-016 | legend | legend below the plates | inhibitor without growth | SDS [0.1%] | high |
| 3bc807ec-017 | legend | legend below the plates | inhibitor without growth | SDS [0.05%] | high |
| 3bc807ec-018 | legend | legend below the plates | symbol | arrow followed by 'no growth' | high |
| 3bc807ec-019 | label | bottom text | bullet 1 | conditional mutant phenotype is reproducible on Nikkomycin Z, with lower inhibitor concentration still significant growth defect | high |
| 3bc807ec-020 | label | bottom text | bullet 2 | overexpression phenotype is also reproducible on caspofungin, but not at lower inhibitor concentration | high |
| 3bc807ec-021 | label | bottom text | bullet 3 | AB33 control strain did not grow, but starting OD was very low | high |
| 3bc807ec-022 | value | OD600 table, row AB33 | OD600 (start) | 0.165 | high |
| 3bc807ec-023 | value | OD600 table, row 2700 | OD600 (start) | 0.696 | high |
| 3bc807ec-024 | value | OD600 table, row 2950glc | OD600 (start) | 0.505 | high |
| 3bc807ec-025 | value | OD600 table, row 2950ara | OD600 (start) | 0.552 | high |
| 3bc807ec-026 | label | OD600 table | table heading | OD600 | high |
| 3bc807ec-027 | observation | Nikkomycin Z [2.5 µM] and [5 µM] plates | growth by row | Pcrg1 OFF rows: strongly reduced; Pcrg1 ON and Pssd1 rows: growth | medium |
| 3bc807ec-028 | observation | caspofungin [500 nM] plate | growth by row | Pcrg1 ON rows reduced; caspofungin [100 nM] plate: no clear difference between rows | medium |
| 3bc807ec-029 | observation | CFW [20 µM] plate | growth | strongly reduced in all rows | medium |

## biolector034:38a110c5 (46 facts)

| id | kind | locator | attribute | value | conf |
|---|---|---|---|---|---|
| 38a110c5-001 | label | top left | heading | Pcrg | high |
| 38a110c5-002 | label | top right | heading | Pima1 | high |
| 38a110c5-003 | axis | Pcrg biomass, upper row | y-axis title | Biomass [AU] | high |
| 38a110c5-004 | axis | Pcrg biomass, upper row | y-axis maximum | 800 | high |
| 38a110c5-005 | axis | Pcrg biomass, upper row | x-axis title | Time [h] | high |
| 38a110c5-006 | legend | Pcrg biomass, upper row | legend | + Glc: Pcrg, Prpl10; + Ara: Pcrg, Prpl10 | high |
| 38a110c5-007 | layout | Pcrg biomass, upper row | time axis range | 0 to 70 h | high |
| 38a110c5-008 | axis | Pcrg GFP, upper row | y-axis title | GFP [RFU] | high |
| 38a110c5-009 | axis | Pcrg GFP, upper row | y-axis maximum | 1600 | high |
| 38a110c5-010 | axis | Pcrg GFP, upper row | x-axis title | Time [h] | high |
| 38a110c5-011 | legend | Pcrg GFP, upper row | legend | + Glc: Pcrg, Prpl10; + Ara: Pcrg, Prpl10 | high |
| 38a110c5-012 | layout | Pcrg GFP, upper row | time axis range | 0 to 70 h | high |
| 38a110c5-013 | axis | Pima1 biomass, upper row | y-axis title | Biomass [AU] | high |
| 38a110c5-014 | axis | Pima1 biomass, upper row | y-axis maximum | 800 | high |
| 38a110c5-015 | axis | Pima1 biomass, upper row | x-axis title | Time [h] | high |
| 38a110c5-016 | legend | Pima1 biomass, upper row | legend | + Glc: Pima1, Prpl10, Pima1short; + Malt: Pima1, Prpl10, Pima1short | high |
| 38a110c5-017 | layout | Pima1 biomass, upper row | time axis range | 0 to 70 h | high |
| 38a110c5-018 | axis | Pima1 GFP, upper row | y-axis title | GFP [RFU] | high |
| 38a110c5-019 | axis | Pima1 GFP, upper row | y-axis maximum | 1200 | high |
| 38a110c5-020 | axis | Pima1 GFP, upper row | x-axis title | Time [h] | high |
| 38a110c5-021 | legend | Pima1 GFP, upper row | legend | + Glc: Pima1, Prpl10, Pima1short; + Malt: Pima1, Prpl10, Pima1short | high |
| 38a110c5-022 | layout | Pima1 GFP, upper row | time axis range | 0 to 70 h | high |
| 38a110c5-023 | axis | Pcrg biomass, lower row | y-axis title | Biomass [AU] | high |
| 38a110c5-024 | axis | Pcrg biomass, lower row | y-axis maximum | 800 | high |
| 38a110c5-025 | axis | Pcrg biomass, lower row | x-axis title | Time [h] | high |
| 38a110c5-026 | legend | Pcrg biomass, lower row | legend | + Glc: Pcrg, Prpl10; + Ara: Pcrg, Prpl10 | high |
| 38a110c5-027 | layout | Pcrg biomass, lower row | time axis range | 0 to 70 h | high |
| 38a110c5-028 | axis | Pcrg GFP, lower row | y-axis title | GFP [RFU] | high |
| 38a110c5-029 | axis | Pcrg GFP, lower row | y-axis maximum | 300 | high |
| 38a110c5-030 | axis | Pcrg GFP, lower row | x-axis title | Time [h] | high |
| 38a110c5-031 | legend | Pcrg GFP, lower row | legend | + Glc: Pcrg, Prpl10; + Ara: Pcrg, Prpl10 | high |
| 38a110c5-032 | layout | Pcrg GFP, lower row | time axis range | 0 to 70 h | high |
| 38a110c5-033 | axis | Pima1 biomass, lower row | y-axis title | Biomass [AU] | high |
| 38a110c5-034 | axis | Pima1 biomass, lower row | y-axis maximum | 800 | high |
| 38a110c5-035 | axis | Pima1 biomass, lower row | x-axis title | Time [h] | high |
| 38a110c5-036 | legend | Pima1 biomass, lower row | legend | + Glc: Pima1, Prpl10; + Malt: Pima1, Prpl10 | high |
| 38a110c5-037 | layout | Pima1 biomass, lower row | time axis range | 0 to 70 h | high |
| 38a110c5-038 | axis | Pima1 GFP, lower row | y-axis title | GFP [RFU] | high |
| 38a110c5-039 | axis | Pima1 GFP, lower row | y-axis maximum | 200 | high |
| 38a110c5-040 | axis | Pima1 GFP, lower row | x-axis title | Time [h] | high |
| 38a110c5-041 | legend | Pima1 GFP, lower row | legend | + Glc: Pima1, Prpl10; + Malt: Pima1, Prpl10 | high |
| 38a110c5-042 | layout | Pima1 GFP, lower row | time axis range | 0 to 70 h | high |
| 38a110c5-043 | layout | all 8 panels | marker | black arrow at about 25 h | medium |
| 38a110c5-044 | observation | all biomass panels | level at 70 h | Pcrg biomass plateaus near 500 AU, Pima1 biomass near 350-380 AU | medium |
| 38a110c5-045 | observation | Pcrg GFP, upper row | highest curve | + Ara Pcrg reaches about 1500 RFU (peak near 55 h) | medium |
| 38a110c5-046 | observation | Pima1 GFP, upper row | highest curve | + Malt Pima1 reaches about 1000 RFU | medium |

## biolector034:5c18fdef (38 facts)

| id | kind | locator | attribute | value | conf |
|---|---|---|---|---|---|
| 5c18fdef-001 | label | column heading | column heading | Biomass | high |
| 5c18fdef-002 | label | column heading | column heading | GFP | high |
| 5c18fdef-003 | label | column heading | column heading | GFP | high |
| 5c18fdef-004 | label | right of the upper row | row label | Promoter:eGFP | high |
| 5c18fdef-005 | label | right of the lower row | row label | Promoter:eGFP-d2-L | high |
| 5c18fdef-006 | axis | biomass, upper row | y-axis title | Biomass [AU] | high |
| 5c18fdef-007 | axis | biomass, upper row | y-axis maximum | 800 | high |
| 5c18fdef-008 | axis | biomass, upper row | x-axis title | Time [h] | high |
| 5c18fdef-009 | legend | biomass, upper row | legend | + H2O: Phsp70, Prpl10, Potef; + Nitrogen: Phsp70, Prpl10, Potef | high |
| 5c18fdef-010 | layout | biomass, upper row | time axis range | 0 to 70 h | high |
| 5c18fdef-011 | axis | GFP (Phsp70, Prpl10), upper row | y-axis title | GFP [RFU] | high |
| 5c18fdef-012 | axis | GFP (Phsp70, Prpl10), upper row | y-axis maximum | 1200 | high |
| 5c18fdef-013 | axis | GFP (Phsp70, Prpl10), upper row | x-axis title | Time [h] | high |
| 5c18fdef-014 | legend | GFP (Phsp70, Prpl10), upper row | legend | + H2O: Phsp70, Prpl10; + Nitrogen: Phsp70, Prpl10 | high |
| 5c18fdef-015 | layout | GFP (Phsp70, Prpl10), upper row | time axis range | 0 to 70 h | high |
| 5c18fdef-016 | axis | GFP (Potef), upper row | y-axis title | GFP [RFU] | high |
| 5c18fdef-017 | axis | GFP (Potef), upper row | y-axis maximum | 1200 | high |
| 5c18fdef-018 | axis | GFP (Potef), upper row | x-axis title | Time [h] | high |
| 5c18fdef-019 | legend | GFP (Potef), upper row | legend | + H2O: Potef; + Nitrogen: Potef | high |
| 5c18fdef-020 | layout | GFP (Potef), upper row | time axis range | 0 to 70 h | high |
| 5c18fdef-021 | axis | biomass, lower row | y-axis title | Biomass [AU] | high |
| 5c18fdef-022 | axis | biomass, lower row | y-axis maximum | 800 | high |
| 5c18fdef-023 | axis | biomass, lower row | x-axis title | Time [h] | high |
| 5c18fdef-024 | legend | biomass, lower row | legend | + H2O: Phsp70, Prpl10, Potef; + Nitrogen: Phsp70, Prpl10, Potef | high |
| 5c18fdef-025 | layout | biomass, lower row | time axis range | 0 to 70 h | high |
| 5c18fdef-026 | axis | GFP (Phsp70, Prpl10), lower row | y-axis title | GFP [RFU] | high |
| 5c18fdef-027 | axis | GFP (Phsp70, Prpl10), lower row | y-axis maximum | 200 | high |
| 5c18fdef-028 | axis | GFP (Phsp70, Prpl10), lower row | x-axis title | Time [h] | high |
| 5c18fdef-029 | legend | GFP (Phsp70, Prpl10), lower row | legend | + H2O: Phsp70, Prpl10; + Nitrogen: Phsp70, Prpl10 | high |
| 5c18fdef-030 | layout | GFP (Phsp70, Prpl10), lower row | time axis range | 0 to 70 h | high |
| 5c18fdef-031 | axis | GFP (Potef), lower row | y-axis title | GFP [RFU] | high |
| 5c18fdef-032 | axis | GFP (Potef), lower row | y-axis maximum | 200 | high |
| 5c18fdef-033 | axis | GFP (Potef), lower row | x-axis title | Time [h] | high |
| 5c18fdef-034 | legend | GFP (Potef), lower row | legend | + H2O: Potef; + Nitrogen: Potef | high |
| 5c18fdef-035 | layout | GFP (Potef), lower row | time axis range | 0 to 70 h | high |
| 5c18fdef-036 | layout | all 6 panels | marker | black arrow at about 43 h | medium |
| 5c18fdef-037 | observation | biomass panels | effect of nitrogen | after the arrow the + Nitrogen curves rise to about 700-750 AU while + H2O curves stay near 450-480 AU | medium |
| 5c18fdef-038 | observation | GFP (Phsp70, Prpl10) upper row | effect of nitrogen | + Nitrogen Phsp70 rises to about 1150 RFU after the arrow; + H2O Phsp70 about 750 RFU | medium |

## ux511:76a1dde7 (24 facts)

| id | kind | locator | attribute | value | conf |
|---|---|---|---|---|---|
| 76a1dde7-001 | label | lane label 1 | lane label | pUX782 | high |
| 76a1dde7-002 | label | lane label 2 | lane label | pUX783 | high |
| 76a1dde7-003 | label | lane label 3 | lane label | pUX784 | high |
| 76a1dde7-004 | label | lane label 4 | lane label | pUX785 | high |
| 76a1dde7-005 | label | lane label 5 | lane label | pUX786 | high |
| 76a1dde7-006 | label | lane label 6 | lane label | pUX787 | high |
| 76a1dde7-007 | mark | left side | size marker | 10000 bp | high |
| 76a1dde7-008 | mark | left side | size marker | 8000 bp | high |
| 76a1dde7-009 | mark | left side | size marker | 6000 bp | high |
| 76a1dde7-010 | mark | left side | size marker | 5000 bp | high |
| 76a1dde7-011 | mark | left side | size marker | 4000 bp | high |
| 76a1dde7-012 | mark | left side | size marker | 3000 bp | high |
| 76a1dde7-013 | mark | left side | size marker | 2500 bp | high |
| 76a1dde7-014 | mark | left side | size marker | 2000 bp | high |
| 76a1dde7-015 | mark | left side | size marker | 1500 bp | high |
| 76a1dde7-016 | mark | left side | size marker | 1000 bp | high |
| 76a1dde7-017 | mark | left side | size marker | 750 bp | high |
| 76a1dde7-018 | mark | left side | size marker | 500 bp | high |
| 76a1dde7-019 | mark | left side | size marker | 250 bp | high |
| 76a1dde7-020 | layout | gel | ladders | one ladder left and one ladder right of the six sample lanes | high |
| 76a1dde7-021 | observation | lane pUX782 | upper band | about 5500-6000 bp (smeared, between the 6000 and 5000 bp markers) | medium |
| 76a1dde7-022 | observation | lanes pUX783-pUX787 | upper band | about 8000-9000 bp (smeared, around and above the 8000 bp marker) | medium |
| 76a1dde7-023 | observation | all six lanes | middle band | about 2100-2200 bp | medium |
| 76a1dde7-024 | observation | all six lanes | lower band | about 600-650 bp | medium |

## ux511:e9e15b0e (27 facts)

| id | kind | locator | attribute | value | conf |
|---|---|---|---|---|---|
| e9e15b0e-001 | label | lane label 1 | lane label | pUX797 | high |
| e9e15b0e-002 | label | lane label 2 | lane label | pUX798 | high |
| e9e15b0e-003 | label | lane label 3 | lane label | pUX799 | high |
| e9e15b0e-004 | label | lane label 4 | lane label | pUX800 | high |
| e9e15b0e-005 | label | lane label 5 | lane label | pUX801 | high |
| e9e15b0e-006 | label | lane label 6 | lane label | pUX802 | high |
| e9e15b0e-007 | label | lane label 7 | lane label | pUX803 | high |
| e9e15b0e-008 | mark | left side | size marker | 10000 bp | high |
| e9e15b0e-009 | mark | left side | size marker | 8000 bp | high |
| e9e15b0e-010 | mark | left side | size marker | 6000 bp | high |
| e9e15b0e-011 | mark | left side | size marker | 5000 bp | high |
| e9e15b0e-012 | mark | left side | size marker | 4000 bp | high |
| e9e15b0e-013 | mark | left side | size marker | 3000 bp | high |
| e9e15b0e-014 | mark | left side | size marker | 2500 bp | high |
| e9e15b0e-015 | mark | left side | size marker | 2000 bp | high |
| e9e15b0e-016 | mark | left side | size marker | 1500 bp | high |
| e9e15b0e-017 | mark | left side | size marker | 1000 bp | high |
| e9e15b0e-018 | mark | left side | size marker | 750 bp | high |
| e9e15b0e-019 | mark | left side | size marker | 500 bp | high |
| e9e15b0e-020 | mark | left side | size marker | 250 bp | high |
| e9e15b0e-021 | layout | gel | ladders | one ladder left and one ladder right of the seven sample lanes | high |
| e9e15b0e-022 | observation | lane pUX797 | upper bands | several bands between about 6000 and 10000 bp (three bands), unlike the other lanes | medium |
| e9e15b0e-023 | observation | lanes pUX798, 799, 801, 802 | upper band | single band at about 7000-8000 bp | medium |
| e9e15b0e-024 | observation | lane pUX800 | upper band | single band slightly higher than its neighbours | medium |
| e9e15b0e-025 | observation | lane pUX803 | upper bands | band at about 7500 bp plus an extra fainter band at about 9000 bp | medium |
| e9e15b0e-026 | observation | all lanes | middle band | about 2100 bp | medium |
| e9e15b0e-027 | observation | all lanes | lower band | about 650 bp, faint in pUX797 and pUX803 | medium |

## ux511:bc82c478 (46 facts)

| id | kind | locator | attribute | value | conf |
|---|---|---|---|---|---|
| bc82c478-001 | label | bracket over the lanes | strain label | UX511 | high |
| bc82c478-002 | label | UX511 lane | clone number | 4 | high |
| bc82c478-003 | colour-code | UX511 clone 4 | marked as correct on blot image | yes | high |
| bc82c478-004 | label | UX511 lane | clone number | 7 | high |
| bc82c478-005 | colour-code | UX511 clone 7 | marked as correct on blot image | yes | high |
| bc82c478-006 | label | UX511 lane | clone number | 8 | high |
| bc82c478-007 | colour-code | UX511 clone 8 | marked as correct on blot image | yes | high |
| bc82c478-008 | label | bracket over the lanes | strain label | UX512 | high |
| bc82c478-009 | label | UX512 lane | clone number | 3 | high |
| bc82c478-010 | colour-code | UX512 clone 3 | marked as correct on blot image | no | high |
| bc82c478-011 | label | UX512 lane | clone number | 4 | high |
| bc82c478-012 | colour-code | UX512 clone 4 | marked as correct on blot image | yes | high |
| bc82c478-013 | label | UX512 lane | clone number | 6 | high |
| bc82c478-014 | colour-code | UX512 clone 6 | marked as correct on blot image | yes | high |
| bc82c478-015 | label | bracket over the lanes | strain label | UX513 | high |
| bc82c478-016 | label | UX513 lane | clone number | 2 | high |
| bc82c478-017 | colour-code | UX513 clone 2 | marked as correct on blot image | yes | high |
| bc82c478-018 | label | UX513 lane | clone number | 3 | high |
| bc82c478-019 | colour-code | UX513 clone 3 | marked as correct on blot image | yes | high |
| bc82c478-020 | label | UX513 lane | clone number | 4 | high |
| bc82c478-021 | colour-code | UX513 clone 4 | marked as correct on blot image | yes | high |
| bc82c478-022 | label | bracket over the lanes | strain label | UX514 | high |
| bc82c478-023 | label | UX514 lane | clone number | 3 | high |
| bc82c478-024 | colour-code | UX514 clone 3 | marked as correct on blot image | yes | high |
| bc82c478-025 | label | UX514 lane | clone number | 7 | high |
| bc82c478-026 | colour-code | UX514 clone 7 | marked as correct on blot image | yes | high |
| bc82c478-027 | label | UX514 lane | clone number | 8 | high |
| bc82c478-028 | colour-code | UX514 clone 8 | marked as correct on blot image | no | high |
| bc82c478-029 | label | lane after the clones | control lane label | UMa133 | high |
| bc82c478-030 | colour-code | UMa133 | marked as correct on blot image | no (black) | high |
| bc82c478-031 | mark | left side | size marker | 10000 | high |
| bc82c478-032 | mark | left side | size marker | 8000 | high |
| bc82c478-033 | mark | left side | size marker | 6000 | high |
| bc82c478-034 | mark | left side | size marker | 5000 | high |
| bc82c478-035 | mark | left side | size marker | 4000 | high |
| bc82c478-036 | mark | left side | size marker | 3500 | high |
| bc82c478-037 | mark | left side | size marker | 3000 | high |
| bc82c478-038 | mark | left side | size marker | 2500 | high |
| bc82c478-039 | mark | left side | size marker | 2000 | high |
| bc82c478-040 | mark | left side | size marker | 1500 | high |
| bc82c478-041 | layout | gel | ladders | one ladder left and one ladder right of the sample lanes | high |
| bc82c478-042 | colour-code | clone numbers | colour code | green clone numbers vs black clone numbers (green = marked correct) | high |
| bc82c478-043 | observation | lanes UX511 clones 4, 7, 8 | main band | about 6000 bp (at the 6000 marker) | medium |
| bc82c478-044 | observation | lanes UX512 clones 4, 6 | main band | about 6500-7000 bp | medium |
| bc82c478-045 | observation | lanes UX513 and UX514 | main band | about 9000 bp (between the 8000 and 10000 markers) | medium |
| bc82c478-046 | observation | UMa133 lane | bands | weak bands near 2000 and 3000 bp | medium |

## ux511:be57156f (39 facts)

| id | kind | locator | attribute | value | conf |
|---|---|---|---|---|---|
| be57156f-001 | label | bracket over the lanes | strain label | UX515 | high |
| be57156f-002 | label | UX515 lane | clone number | 1 | high |
| be57156f-003 | colour-code | UX515 clone 1 | marked as correct on blot image | yes | high |
| be57156f-004 | label | UX515 lane | clone number | 2 | high |
| be57156f-005 | colour-code | UX515 clone 2 | marked as correct on blot image | no | high |
| be57156f-006 | label | UX515 lane | clone number | 4 | high |
| be57156f-007 | colour-code | UX515 clone 4 | marked as correct on blot image | yes | high |
| be57156f-008 | label | UX515 lane | clone number | 5 | high |
| be57156f-009 | colour-code | UX515 clone 5 | marked as correct on blot image | yes | high |
| be57156f-010 | label | UX515 lane | clone number | 7 | high |
| be57156f-011 | colour-code | UX515 clone 7 | marked as correct on blot image | no | high |
| be57156f-012 | label | UX515 lane | clone number | 11 | high |
| be57156f-013 | colour-code | UX515 clone 11 | marked as correct on blot image | no | high |
| be57156f-014 | label | bracket over the lanes | strain label | UX516 | high |
| be57156f-015 | label | UX516 lane | clone number | 1 | high |
| be57156f-016 | colour-code | UX516 clone 1 | marked as correct on blot image | yes | high |
| be57156f-017 | label | UX516 lane | clone number | 5 | high |
| be57156f-018 | colour-code | UX516 clone 5 | marked as correct on blot image | no | high |
| be57156f-019 | label | UX516 lane | clone number | 11 | high |
| be57156f-020 | colour-code | UX516 clone 11 | marked as correct on blot image | yes | high |
| be57156f-021 | label | UX516 lane | clone number | 12 | high |
| be57156f-022 | colour-code | UX516 clone 12 | marked as correct on blot image | yes | high |
| be57156f-023 | label | lane after the clones | control lane label | UMa133 | high |
| be57156f-024 | colour-code | UMa133 | marked as correct on blot image | no (black) | high |
| be57156f-025 | mark | left side | size marker | 10000 | high |
| be57156f-026 | mark | left side | size marker | 8000 | high |
| be57156f-027 | mark | left side | size marker | 6000 | high |
| be57156f-028 | mark | left side | size marker | 5000 | high |
| be57156f-029 | mark | left side | size marker | 4000 | high |
| be57156f-030 | mark | left side | size marker | 3500 | high |
| be57156f-031 | mark | left side | size marker | 3000 | high |
| be57156f-032 | mark | left side | size marker | 2500 | high |
| be57156f-033 | mark | left side | size marker | 2000 | high |
| be57156f-034 | mark | left side | size marker | 1500 | high |
| be57156f-035 | layout | gel | ladders | one ladder left and one ladder right of the sample lanes | high |
| be57156f-036 | colour-code | clone numbers | colour code | green clone numbers vs black clone numbers (green = marked correct) | high |
| be57156f-037 | observation | UX515 clone 2 and clone 11 | signal | very strong band near the top (above 10000 bp) | medium |
| be57156f-038 | observation | UX515 clones 1, 4, 5, 7 and UX516 clones 1, 5, 11, 12 | main band | about 7500-8000 bp | medium |
| be57156f-039 | observation | UMa133 lane | band | about 5000 bp (a single strong band) | medium |

## ux511:6fed9d0a (44 facts)

| id | kind | locator | attribute | value | conf |
|---|---|---|---|---|---|
| 6fed9d0a-001 | label | bracket over the lanes | strain label | UX517 | high |
| 6fed9d0a-002 | label | UX517 lane | clone number | 1 | high |
| 6fed9d0a-003 | colour-code | UX517 clone 1 | marked as correct on blot image | no | high |
| 6fed9d0a-004 | label | UX517 lane | clone number | 9 | high |
| 6fed9d0a-005 | colour-code | UX517 clone 9 | marked as correct on blot image | yes | high |
| 6fed9d0a-006 | label | UX517 lane | clone number | 10 | high |
| 6fed9d0a-007 | colour-code | UX517 clone 10 | marked as correct on blot image | yes | high |
| 6fed9d0a-008 | label | bracket over the lanes | strain label | UX518 | high |
| 6fed9d0a-009 | label | UX518 lane | clone number | 5 | high |
| 6fed9d0a-010 | colour-code | UX518 clone 5 | marked as correct on blot image | yes | high |
| 6fed9d0a-011 | label | UX518 lane | clone number | 6 | high |
| 6fed9d0a-012 | colour-code | UX518 clone 6 | marked as correct on blot image | yes | high |
| 6fed9d0a-013 | label | UX518 lane | clone number | 9 | high |
| 6fed9d0a-014 | colour-code | UX518 clone 9 | marked as correct on blot image | no | high |
| 6fed9d0a-015 | label | bracket over the lanes | strain label | UX519 | high |
| 6fed9d0a-016 | label | UX519 lane | clone number | 3 | high |
| 6fed9d0a-017 | colour-code | UX519 clone 3 | marked as correct on blot image | no | high |
| 6fed9d0a-018 | label | UX519 lane | clone number | 5 | high |
| 6fed9d0a-019 | colour-code | UX519 clone 5 | marked as correct on blot image | yes | high |
| 6fed9d0a-020 | label | UX519 lane | clone number | 8 | high |
| 6fed9d0a-021 | colour-code | UX519 clone 8 | marked as correct on blot image | yes | high |
| 6fed9d0a-022 | label | bracket over the lanes | strain label | UX520 | high |
| 6fed9d0a-023 | label | UX520 lane | clone number | 1 | high |
| 6fed9d0a-024 | colour-code | UX520 clone 1 | marked as correct on blot image | yes | high |
| 6fed9d0a-025 | label | UX520 lane | clone number | 2 | high |
| 6fed9d0a-026 | colour-code | UX520 clone 2 | marked as correct on blot image | yes | high |
| 6fed9d0a-027 | label | UX520 lane | clone number | 5 | high |
| 6fed9d0a-028 | colour-code | UX520 clone 5 | marked as correct on blot image | no | high |
| 6fed9d0a-029 | label | lane after the clones | control lane label | UMa133 | high |
| 6fed9d0a-030 | colour-code | UMa133 | marked as correct on blot image | no (black) | high |
| 6fed9d0a-031 | mark | left side | size marker | 10000 | high |
| 6fed9d0a-032 | mark | left side | size marker | 8000 | high |
| 6fed9d0a-033 | mark | left side | size marker | 6000 | high |
| 6fed9d0a-034 | mark | left side | size marker | 5000 | high |
| 6fed9d0a-035 | mark | left side | size marker | 4000 | high |
| 6fed9d0a-036 | mark | left side | size marker | 3500 | high |
| 6fed9d0a-037 | mark | left side | size marker | 3000 | high |
| 6fed9d0a-038 | mark | left side | size marker | 2500 | high |
| 6fed9d0a-039 | mark | left side | size marker | 2000 | high |
| 6fed9d0a-040 | mark | left side | size marker | 1500 | high |
| 6fed9d0a-041 | layout | gel | ladders | one ladder left and one ladder right of the sample lanes | high |
| 6fed9d0a-042 | colour-code | clone numbers | colour code | green clone numbers vs black clone numbers (green = marked correct) | high |
| 6fed9d0a-043 | observation | all clone lanes | main band | about 8000 bp (just below the 8000 marker), lanes 3 of UX519 with an additional band near 10000 bp | medium |
| 6fed9d0a-044 | observation | UMa133 lane | bands | weak bands near 2000 and 2800 bp | medium |

## ux511:84dc38ff (39 facts)

| id | kind | locator | attribute | value | conf |
|---|---|---|---|---|---|
| 84dc38ff-001 | label | bracket over the lanes | strain label | UX521 | high |
| 84dc38ff-002 | label | UX521 lane | clone number | 1 | high |
| 84dc38ff-003 | colour-code | UX521 clone 1 | marked as correct on blot image | yes | high |
| 84dc38ff-004 | label | UX521 lane | clone number | 2 | high |
| 84dc38ff-005 | colour-code | UX521 clone 2 | marked as correct on blot image | yes | high |
| 84dc38ff-006 | label | UX521 lane | clone number | 6 | high |
| 84dc38ff-007 | colour-code | UX521 clone 6 | marked as correct on blot image | yes | high |
| 84dc38ff-008 | label | bracket over the lanes | strain label | UX522 | high |
| 84dc38ff-009 | label | UX522 lane | clone number | 1 | high |
| 84dc38ff-010 | colour-code | UX522 clone 1 | marked as correct on blot image | yes | high |
| 84dc38ff-011 | label | UX522 lane | clone number | 6 | high |
| 84dc38ff-012 | colour-code | UX522 clone 6 | marked as correct on blot image | yes | high |
| 84dc38ff-013 | label | UX522 lane | clone number | 7 | high |
| 84dc38ff-014 | colour-code | UX522 clone 7 | marked as correct on blot image | yes | high |
| 84dc38ff-015 | label | bracket over the lanes | strain label | UX523 | high |
| 84dc38ff-016 | label | UX523 lane | clone number | 6 | high |
| 84dc38ff-017 | colour-code | UX523 clone 6 | marked as correct on blot image | yes | high |
| 84dc38ff-018 | label | UX523 lane | clone number | 8 | high |
| 84dc38ff-019 | colour-code | UX523 clone 8 | marked as correct on blot image | no | high |
| 84dc38ff-020 | label | UX523 lane | clone number | 10 | high |
| 84dc38ff-021 | colour-code | UX523 clone 10 | marked as correct on blot image | no | high |
| 84dc38ff-022 | label | lane after the clones | control lane label | UMa133 | high |
| 84dc38ff-023 | colour-code | UMa133 | marked as correct on blot image | no (black) | high |
| 84dc38ff-024 | mark | left side | size marker | 10000 | high |
| 84dc38ff-025 | mark | left side | size marker | 8000 | high |
| 84dc38ff-026 | mark | left side | size marker | 6000 | high |
| 84dc38ff-027 | mark | left side | size marker | 5000 | high |
| 84dc38ff-028 | mark | left side | size marker | 4000 | high |
| 84dc38ff-029 | mark | left side | size marker | 3500 | high |
| 84dc38ff-030 | mark | left side | size marker | 3000 | high |
| 84dc38ff-031 | mark | left side | size marker | 2500 | high |
| 84dc38ff-032 | mark | left side | size marker | 2000 | high |
| 84dc38ff-033 | mark | left side | size marker | 1500 | high |
| 84dc38ff-034 | layout | gel | ladders | one ladder left and one ladder right of the sample lanes | high |
| 84dc38ff-035 | colour-code | clone numbers | colour code | green clone numbers vs black clone numbers (green = marked correct) | high |
| 84dc38ff-036 | observation | UX521 clones 1, 2, 6 | main band | about 7500 bp | medium |
| 84dc38ff-037 | observation | UX522 clones 1, 6, 7 | bands | main band about 5500 bp and a second band about 2000 bp | medium |
| 84dc38ff-038 | observation | UX523 clones 8 and 10 | signal | diffuse smear near the top (above 10000 bp) | medium |
| 84dc38ff-039 | observation | UX523 clone 6 | bands | bands near 8000 bp and above 10000 bp | medium |

## ux511:3acf4cbb (26 facts)

| id | kind | locator | attribute | value | conf |
|---|---|---|---|---|---|
| 3acf4cbb-001 | label | bracket over the lanes | strain label | UX523 | high |
| 3acf4cbb-002 | label | UX523 lane | clone number | 6 | high |
| 3acf4cbb-003 | colour-code | UX523 clone 6 | marked as correct on blot image | yes | high |
| 3acf4cbb-004 | label | UX523 lane | clone number | 8 | high |
| 3acf4cbb-005 | colour-code | UX523 clone 8 | marked as correct on blot image | no | high |
| 3acf4cbb-006 | label | UX523 lane | clone number | 10 | high |
| 3acf4cbb-007 | colour-code | UX523 clone 10 | marked as correct on blot image | yes | high |
| 3acf4cbb-008 | label | UX523 lane | clone number | 11 | high |
| 3acf4cbb-009 | colour-code | UX523 clone 11 | marked as correct on blot image | no | high |
| 3acf4cbb-010 | label | lane after the clones | control lane label | UMa133 | high |
| 3acf4cbb-011 | colour-code | UMa133 | marked as correct on blot image | no (black) | high |
| 3acf4cbb-012 | mark | left side | size marker | 10000 | high |
| 3acf4cbb-013 | mark | left side | size marker | 8000 | high |
| 3acf4cbb-014 | mark | left side | size marker | 6000 | high |
| 3acf4cbb-015 | mark | left side | size marker | 5000 | high |
| 3acf4cbb-016 | mark | left side | size marker | 4000 | high |
| 3acf4cbb-017 | mark | left side | size marker | 3500 | high |
| 3acf4cbb-018 | mark | left side | size marker | 3000 | high |
| 3acf4cbb-019 | mark | left side | size marker | 2500 | high |
| 3acf4cbb-020 | mark | left side | size marker | 2000 | high |
| 3acf4cbb-021 | mark | left side | size marker | 1500 | high |
| 3acf4cbb-022 | layout | gel | ladders | one ladder left and one ladder right of the sample lanes | high |
| 3acf4cbb-023 | colour-code | clone numbers | colour code | green clone numbers vs black clone numbers (green = marked correct) | high |
| 3acf4cbb-024 | observation | UX523 clone 6 | main band | about 7500-8000 bp | medium |
| 3acf4cbb-025 | observation | UX523 clone 10 | main band | about 8000-8500 bp | medium |
| 3acf4cbb-026 | observation | UX523 clone 11 | signal | very strong band near 10000 bp with a second band slightly below | medium |

## pux782:grafik (37 facts)

| id | kind | locator | attribute | value | conf |
|---|---|---|---|---|---|
| grafik-001 | label | top, above two lanes | plasmid label | pUX782 | high |
| grafik-002 | label | pUX782 lane | replicate label | #1 | high |
| grafik-003 | label | pUX782 lane | replicate label | #2 | high |
| grafik-004 | label | top, above two lanes | plasmid label | pUX783 | high |
| grafik-005 | label | pUX783 lane | replicate label | #1 | high |
| grafik-006 | label | pUX783 lane | replicate label | #2 | high |
| grafik-007 | label | top, above two lanes | plasmid label | pUX784 | high |
| grafik-008 | label | pUX784 lane | replicate label | #1 | high |
| grafik-009 | label | pUX784 lane | replicate label | #2 | high |
| grafik-010 | label | top, above two lanes | plasmid label | pUX785 | high |
| grafik-011 | label | pUX785 lane | replicate label | #1 | high |
| grafik-012 | label | pUX785 lane | replicate label | #2 | high |
| grafik-013 | label | top, above two lanes | plasmid label | pUX786 | high |
| grafik-014 | label | pUX786 lane | replicate label | #1 | high |
| grafik-015 | label | pUX786 lane | replicate label | #2 | high |
| grafik-016 | label | top, above two lanes | plasmid label | pUX787 | high |
| grafik-017 | label | pUX787 lane | replicate label | #1 | high |
| grafik-018 | label | pUX787 lane | replicate label | #2 | high |
| grafik-019 | mark | left side | size marker | 10000 bp | high |
| grafik-020 | mark | left side | size marker | 8000 bp | high |
| grafik-021 | mark | left side | size marker | 6000 bp | high |
| grafik-022 | mark | left side | size marker | 5000 bp | high |
| grafik-023 | mark | left side | size marker | 4000 bp | high |
| grafik-024 | mark | left side | size marker | 3000 bp | high |
| grafik-025 | mark | left side | size marker | 2500 bp | high |
| grafik-026 | mark | left side | size marker | 2000 bp | high |
| grafik-027 | mark | left side | size marker | 1500 bp | high |
| grafik-028 | mark | left side | size marker | 1000 bp | high |
| grafik-029 | mark | left side | size marker | 750 bp | high |
| grafik-030 | mark | left side | size marker | 500 bp | high |
| grafik-031 | mark | left side | size marker | 250 bp | high |
| grafik-032 | layout | gel | ladders | one ladder left and one ladder right of the 12 sample lanes | high |
| grafik-033 | layout | gel | number of sample lanes | 12 (6 plasmids x 2 colonies) | high |
| grafik-034 | observation | pUX782 #1, #2 | band | single strong band at about 2000 bp (#2 slightly higher than #1) | medium |
| grafik-035 | observation | pUX783, pUX784, pUX785 (#1, #2) | band | single strong band at about 2800-3000 bp | medium |
| grafik-036 | observation | pUX786, pUX787 (#1, #2) | band | single strong band at about 3000-3100 bp, slightly higher than pUX783-785 | medium |
| grafik-037 | observation | all lanes | extra bands | no additional bands visible; faint smear above the main band in pUX783-787 lanes | medium |
