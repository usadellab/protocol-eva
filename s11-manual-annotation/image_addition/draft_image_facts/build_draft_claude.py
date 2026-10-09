#!/opt/homebrew/bin/python3.13
"""Draft of the image-fact annotation (phase 2 of PLAN_images_in_prompt.md): facts read from the 13 images with vision by Claude (this window).
NOT a manual annotation, NOT manual annotation. Output: image_facts_draft_by_claude.json / .md (same folder). Needs human review before any use.
Fact = {id, figure, kind, locator, attribute, value, confidence}.
  kind: label (text printed in the image), mark (size-marker value), legend, axis, value (number printed in the image), layout, condition, colour-code, observation (what the picture shows, not printed)
  confidence: high = printed text or unambiguous; medium = a reading of band position / colour / growth against the markers or neighbours (approximate)
"""
import json
from pathlib import Path

F = []
def add(fig, kind, locator, attribute, value, conf="high"):
    F.append({"id": f"{fig.split(':')[1]}-{sum(1 for x in F if x['figure'] == fig) + 1:03d}", "figure": fig, "kind": kind, "locator": locator,
              "attribute": attribute, "value": value, "confidence": conf})

# ---------- phage gelp1: agarose gel of extracted phage DNA
g = "phage:gelp1"
lanes = ["BD_R1", "BD_R2", "BD_R3", "B_R1", "B_R2", "B_R3", "1kb Plus ladder"]
for i, l in enumerate(lanes, 1): add(g, "label", f"lane {i}", "lane label", l)
add(g, "layout", "gel", "number of lanes", "7 (6 samples + 1 ladder)")
add(g, "layout", "gel", "ladder position", "right-most lane (lane 7)")
for m in ["20 kb", "5 kb", "1.5 kb", "0.5 kb"]: add(g, "mark", "right side, lines to the ladder", "size mark", m)
add(g, "observation", "lanes 1-6", "signal type", "broad smear from the wells to below 0.5 kb in every sample lane; no discrete band", "high")
add(g, "observation", "lane 1 (BD_R1)", "signal intensity", "strongest smear of all lanes, most intense between about 5 kb and 1.5 kb", "medium")
add(g, "observation", "lanes 2-6", "signal intensity", "weaker smears than lane 1; lane 5 (B_R2) and lane 6 (B_R3) denser than lanes 2-4", "medium")
add(g, "observation", "ladder lane", "ladder", "about 15 discrete bands; brightest at the 5 kb, 1.5 kb and 0.5 kb marks", "medium")
add(g, "observation", "wells", "faint band", "faint high-molecular-weight band near the wells (about 20 kb mark) in several lanes", "medium")
add(g, "layout", "image", "transparency", "RGBA PNG; labels are black text on a transparent background (not readable on black)")

# ---------- sdy1 4355ff27 (first spotting, 48h CM 28 C)
s = "sdy1:4355ff27"
add(s, "label", "top left", "title", "48h, CM, 28°C")
for st in ["AB33", "UMa2700", "UMa2950"]: add(s, "label", "top left list", "strain listed", st)
add(s, "label", "top", "culture note", "over night main culture in glucose and/or arabinose")
add(s, "label", "dilution wedge", "dilution range", "10^7 to 10^2")
plates1 = [("CM", "[glucose]"), ("CM", "[arabinose]"), ("CFW", "[20 µM]"), ("Congo red", "[150 µM]"), ("caspofungin", "[500 nM]"), ("Nikkomycin Z", "[5 µM]"), ("SDS", "[0.1%]"), ("SDS", "[0.05%]")]
for i, (a, b) in enumerate(plates1, 1): add(s, "label", f"upper row, plate {i}", "plate title", f"{a} {b}")
for lab in ["AB33", "Pssd1-SSD1-GFP", "Pcrg1-SSD1-GFP (OFF)", "Pcrg1-SSD1-GFP (ON)"]: add(s, "label", "row labels, left", "row label", lab)
add(s, "layout", "upper row of plates", "spot rows per plate", "6 (AB33, Pssd1-SSD1-GFP, 2 x Pcrg1 OFF, 2 x Pcrg1 ON; the vertical bars mark the OFF rows and the ON rows)", "medium")
for i, (a, b) in enumerate([("CM", "[glucose]"), ("CFW", "[20 µM]"), ("caspofungin", "[500 nM]"), ("Nikkomycin Z", "[5 µM]")], 1): add(s, "label", f"lower row, plate {i}", "plate title", f"{a} {b}")
add(s, "label", "lower row, right", "annotation", "glucose Pcrg1-OFF condition")
add(s, "label", "bottom text", "conclusion 1", "conditional SSD1-mutant sensitive to chitin synthase inhibitor Nikkomycin Z but not CFW which binds to chitin, looks slightly more growth; surprisingly the conditional SSD1-mutant was way more resistant to ß-glucan inhibitor CR")
add(s, "label", "bottom text", "conclusion 2", "overexpression of SSD1 (only in pre-culture) was sufficient to produce a strong sensitivity phenotype in presence of caspofungin, inhibiting ß-glucan synthesis not present in the conditional-mutant")
add(s, "observation", "SDS [0.1%] and SDS [0.05%] plates", "growth", "no visible growth in any row", "high")
add(s, "observation", "Nikkomycin Z [5 µM] plate", "growth by row", "Pcrg1 OFF rows: strongly reduced (almost no spots); Pcrg1 ON, AB33 and Pssd1 rows: growth", "medium")
add(s, "observation", "caspofungin [500 nM] plate", "growth by row", "Pcrg1 ON rows: strongly reduced (only small colonies at low dilution); other rows: growth", "medium")
add(s, "observation", "CFW [20 µM] plate", "growth", "reduced in all rows (first one or two spots only)", "medium")
add(s, "observation", "Congo red [150 µM] plate", "growth by row", "only the Pcrg1 OFF rows show faint spots; other rows no growth", "medium")
add(s, "observation", "CM [glucose] and CM [arabinose] plates", "growth", "all rows grow with dilution series visible", "high")

# ---------- sdy1 3bc807ec (30.01.25 48h)
s = "sdy1:3bc807ec"
add(s, "label", "top left", "title", "30.01.25 48h")
plates2 = [("CM", "[glucose]"), ("CM", "[arabinose]"), ("CFW", "[10 µM]"), ("CFW", "[20 µM]"), ("caspofungin", "[100 nM]"), ("caspofungin", "[500 nM]"), ("Nikkomycin Z", "[2.5 µM]"), ("Nikkomycin Z", "[5 µM]")]
for i, (a, b) in enumerate(plates2, 1): add(s, "label", f"plate {i}", "plate title", f"{a} {b}")
for lab in ["AB33", "Pssd1-SSD1-GFP", "Pcrg1-SSD1-GFP (OFF)", "Pcrg1-SSD1-GFP (ON)"]: add(s, "label", "row labels, left", "row label", lab)
add(s, "layout", "plates", "spot rows per plate", "5 visible rows (Pssd1-SSD1-GFP, 2 x OFF, 2 x ON); AB33 row without growth", "medium")
for t, v in [("Congo red", "[150 µM]"), ("SDS", "[0.1%]"), ("SDS", "[0.05%]")]: add(s, "legend", "legend below the plates", "inhibitor without growth", f"{t} {v}")
add(s, "legend", "legend below the plates", "symbol", "arrow followed by 'no growth'")
add(s, "label", "bottom text", "bullet 1", "conditional mutant phenotype is reproducible on Nikkomycin Z, with lower inhibitor concentration still significant growth defect")
add(s, "label", "bottom text", "bullet 2", "overexpression phenotype is also reproducible on caspofungin, but not at lower inhibitor concentration")
add(s, "label", "bottom text", "bullet 3", "AB33 control strain did not grow, but starting OD was very low")
for strain, od in [("AB33", "0.165"), ("2700", "0.696"), ("2950glc", "0.505"), ("2950ara", "0.552")]:
    add(s, "value", f"OD600 table, row {strain}", "OD600 (start)", od)
add(s, "label", "OD600 table", "table heading", "OD600")
add(s, "observation", "Nikkomycin Z [2.5 µM] and [5 µM] plates", "growth by row", "Pcrg1 OFF rows: strongly reduced; Pcrg1 ON and Pssd1 rows: growth", "medium")
add(s, "observation", "caspofungin [500 nM] plate", "growth by row", "Pcrg1 ON rows reduced; caspofungin [100 nM] plate: no clear difference between rows", "medium")
add(s, "observation", "CFW [20 µM] plate", "growth", "strongly reduced in all rows", "medium")

# ---------- biolector034 38a110c5: Pcrg / Pima1
b = "biolector034:38a110c5"
add(b, "label", "top left", "heading", "Pcrg"); add(b, "label", "top right", "heading", "Pima1")
panels = [  # (name, y title, y max, legend groups)
    ("Pcrg biomass, upper row", "Biomass [AU]", "800", "+ Glc: Pcrg, Prpl10; + Ara: Pcrg, Prpl10"),
    ("Pcrg GFP, upper row", "GFP [RFU]", "1600", "+ Glc: Pcrg, Prpl10; + Ara: Pcrg, Prpl10"),
    ("Pima1 biomass, upper row", "Biomass [AU]", "800", "+ Glc: Pima1, Prpl10, Pima1short; + Malt: Pima1, Prpl10, Pima1short"),
    ("Pima1 GFP, upper row", "GFP [RFU]", "1200", "+ Glc: Pima1, Prpl10, Pima1short; + Malt: Pima1, Prpl10, Pima1short"),
    ("Pcrg biomass, lower row", "Biomass [AU]", "800", "+ Glc: Pcrg, Prpl10; + Ara: Pcrg, Prpl10"),
    ("Pcrg GFP, lower row", "GFP [RFU]", "300", "+ Glc: Pcrg, Prpl10; + Ara: Pcrg, Prpl10"),
    ("Pima1 biomass, lower row", "Biomass [AU]", "800", "+ Glc: Pima1, Prpl10; + Malt: Pima1, Prpl10"),
    ("Pima1 GFP, lower row", "GFP [RFU]", "200", "+ Glc: Pima1, Prpl10; + Malt: Pima1, Prpl10")]
for name, yt, ymax, leg in panels:
    add(b, "axis", name, "y-axis title", yt); add(b, "axis", name, "y-axis maximum", ymax); add(b, "axis", name, "x-axis title", "Time [h]")
    add(b, "legend", name, "legend", leg); add(b, "layout", name, "time axis range", "0 to 70 h")
add(b, "layout", "all 8 panels", "marker", "black arrow at about 25 h", "medium")
add(b, "observation", "all biomass panels", "level at 70 h", "Pcrg biomass plateaus near 500 AU, Pima1 biomass near 350-380 AU", "medium")
add(b, "observation", "Pcrg GFP, upper row", "highest curve", "+ Ara Pcrg reaches about 1500 RFU (peak near 55 h)", "medium")
add(b, "observation", "Pima1 GFP, upper row", "highest curve", "+ Malt Pima1 reaches about 1000 RFU", "medium")

# ---------- biolector034 5c18fdef: Potef / Phsp70
b = "biolector034:5c18fdef"
for h in ["Biomass", "GFP", "GFP"]: add(b, "label", "column heading", "column heading", h)
add(b, "label", "right of the upper row", "row label", "Promoter:eGFP"); add(b, "label", "right of the lower row", "row label", "Promoter:eGFP-d2-L")
panels = [("biomass, upper row", "Biomass [AU]", "800", "+ H2O: Phsp70, Prpl10, Potef; + Nitrogen: Phsp70, Prpl10, Potef"),
          ("GFP (Phsp70, Prpl10), upper row", "GFP [RFU]", "1200", "+ H2O: Phsp70, Prpl10; + Nitrogen: Phsp70, Prpl10"),
          ("GFP (Potef), upper row", "GFP [RFU]", "1200", "+ H2O: Potef; + Nitrogen: Potef"),
          ("biomass, lower row", "Biomass [AU]", "800", "+ H2O: Phsp70, Prpl10, Potef; + Nitrogen: Phsp70, Prpl10, Potef"),
          ("GFP (Phsp70, Prpl10), lower row", "GFP [RFU]", "200", "+ H2O: Phsp70, Prpl10; + Nitrogen: Phsp70, Prpl10"),
          ("GFP (Potef), lower row", "GFP [RFU]", "200", "+ H2O: Potef; + Nitrogen: Potef")]
for name, yt, ymax, leg in panels:
    add(b, "axis", name, "y-axis title", yt); add(b, "axis", name, "y-axis maximum", ymax); add(b, "axis", name, "x-axis title", "Time [h]")
    add(b, "legend", name, "legend", leg); add(b, "layout", name, "time axis range", "0 to 70 h")
add(b, "layout", "all 6 panels", "marker", "black arrow at about 43 h", "medium")
add(b, "observation", "biomass panels", "effect of nitrogen", "after the arrow the + Nitrogen curves rise to about 700-750 AU while + H2O curves stay near 450-480 AU", "medium")
add(b, "observation", "GFP (Phsp70, Prpl10) upper row", "effect of nitrogen", "+ Nitrogen Phsp70 rises to about 1150 RFU after the arrow; + H2O Phsp70 about 750 RFU", "medium")

# ---------- ux511 gels
def gel(fig, lane_labels, markers, unit, notes):
    for i, l in enumerate(lane_labels, 1): add(fig, "label", f"lane label {i}", "lane label", l)
    for m in markers: add(fig, "mark", "left side", "size marker", f"{m}{unit}")
    for n in notes: add(fig, *n)
bp = ["10000", "8000", "6000", "5000", "4000", "3000", "2500", "2000", "1500", "1000", "750", "500", "250"]
gel("ux511:76a1dde7", ["pUX782", "pUX783", "pUX784", "pUX785", "pUX786", "pUX787"], bp, " bp",
    [("layout", "gel", "ladders", "one ladder left and one ladder right of the six sample lanes", "high"),
     ("observation", "lane pUX782", "upper band", "about 5500-6000 bp (smeared, between the 6000 and 5000 bp markers)", "medium"),
     ("observation", "lanes pUX783-pUX787", "upper band", "about 8000-9000 bp (smeared, around and above the 8000 bp marker)", "medium"),
     ("observation", "all six lanes", "middle band", "about 2100-2200 bp", "medium"),
     ("observation", "all six lanes", "lower band", "about 600-650 bp", "medium")])
gel("ux511:e9e15b0e", ["pUX797", "pUX798", "pUX799", "pUX800", "pUX801", "pUX802", "pUX803"], bp, " bp",
    [("layout", "gel", "ladders", "one ladder left and one ladder right of the seven sample lanes", "high"),
     ("observation", "lane pUX797", "upper bands", "several bands between about 6000 and 10000 bp (three bands), unlike the other lanes", "medium"),
     ("observation", "lanes pUX798, 799, 801, 802", "upper band", "single band at about 7000-8000 bp", "medium"),
     ("observation", "lane pUX800", "upper band", "single band slightly higher than its neighbours", "medium"),
     ("observation", "lane pUX803", "upper bands", "band at about 7500 bp plus an extra fainter band at about 9000 bp", "medium"),
     ("observation", "all lanes", "middle band", "about 2100 bp", "medium"),
     ("observation", "all lanes", "lower band", "about 650 bp, faint in pUX797 and pUX803", "medium")])
# ---------- ux511 Southern blots: (figure, groups: strain -> [(clone, green?)], markers, notes)
bl = ["10000", "8000", "6000", "5000", "4000", "3500", "3000", "2500", "2000", "1500"]
blots = {
 "ux511:bc82c478": ([("UX511", [(4, 1), (7, 1), (8, 1)]), ("UX512", [(3, 0), (4, 1), (6, 1)]), ("UX513", [(2, 1), (3, 1), (4, 1)]), ("UX514", [(3, 1), (7, 1), (8, 0)])],
                    [("observation", "lanes UX511 clones 4, 7, 8", "main band", "about 6000 bp (at the 6000 marker)", "medium"),
                     ("observation", "lanes UX512 clones 4, 6", "main band", "about 6500-7000 bp", "medium"),
                     ("observation", "lanes UX513 and UX514", "main band", "about 9000 bp (between the 8000 and 10000 markers)", "medium"),
                     ("observation", "UMa133 lane", "bands", "weak bands near 2000 and 3000 bp", "medium")]),
 "ux511:be57156f": ([("UX515", [(1, 1), (2, 0), (4, 1), (5, 1), (7, 0), (11, 0)]), ("UX516", [(1, 1), (5, 0), (11, 1), (12, 1)])],
                    [("observation", "UX515 clone 2 and clone 11", "signal", "very strong band near the top (above 10000 bp)", "medium"),
                     ("observation", "UX515 clones 1, 4, 5, 7 and UX516 clones 1, 5, 11, 12", "main band", "about 7500-8000 bp", "medium"),
                     ("observation", "UMa133 lane", "band", "about 5000 bp (a single strong band)", "medium")]),
 "ux511:6fed9d0a": ([("UX517", [(1, 0), (9, 1), (10, 1)]), ("UX518", [(5, 1), (6, 1), (9, 0)]), ("UX519", [(3, 0), (5, 1), (8, 1)]), ("UX520", [(1, 1), (2, 1), (5, 0)])],
                    [("observation", "all clone lanes", "main band", "about 8000 bp (just below the 8000 marker), lanes 3 of UX519 with an additional band near 10000 bp", "medium"),
                     ("observation", "UMa133 lane", "bands", "weak bands near 2000 and 2800 bp", "medium")]),
 "ux511:84dc38ff": ([("UX521", [(1, 1), (2, 1), (6, 1)]), ("UX522", [(1, 1), (6, 1), (7, 1)]), ("UX523", [(6, 1), (8, 0), (10, 0)])],
                    [("observation", "UX521 clones 1, 2, 6", "main band", "about 7500 bp", "medium"),
                     ("observation", "UX522 clones 1, 6, 7", "bands", "main band about 5500 bp and a second band about 2000 bp", "medium"),
                     ("observation", "UX523 clones 8 and 10", "signal", "diffuse smear near the top (above 10000 bp)", "medium"),
                     ("observation", "UX523 clone 6", "bands", "bands near 8000 bp and above 10000 bp", "medium")]),
 "ux511:3acf4cbb": ([("UX523", [(6, 1), (8, 0), (10, 1), (11, 0)])],
                    [("observation", "UX523 clone 6", "main band", "about 7500-8000 bp", "medium"),
                     ("observation", "UX523 clone 10", "main band", "about 8000-8500 bp", "medium"),
                     ("observation", "UX523 clone 11", "signal", "very strong band near 10000 bp with a second band slightly below", "medium")]),
}
for fig, (groups, notes) in blots.items():
    for strain, clones in groups:
        add(fig, "label", "bracket over the lanes", "strain label", strain)
        for c, green in clones:
            add(fig, "label", f"{strain} lane", "clone number", str(c))
            add(fig, "colour-code", f"{strain} clone {c}", "marked as correct on blot image", "yes" if green else "no")
    add(fig, "label", "lane after the clones", "control lane label", "UMa133")
    add(fig, "colour-code", "UMa133", "marked as correct on blot image", "no (black)")
    for m in bl: add(fig, "mark", "left side", "size marker", m)
    add(fig, "layout", "gel", "ladders", "one ladder left and one ladder right of the sample lanes")
    add(fig, "colour-code", "clone numbers", "colour code", "green clone numbers vs black clone numbers (green = marked correct)")
    for n in notes: add(fig, *n)
# ---------- pux782 grafik: colony PCR gel
x = "pux782:grafik"
for p in ["pUX782", "pUX783", "pUX784", "pUX785", "pUX786", "pUX787"]:
    add(x, "label", "top, above two lanes", "plasmid label", p)
    for r in ("#1", "#2"): add(x, "label", f"{p} lane", "replicate label", r)
for m in bp: add(x, "mark", "left side", "size marker", f"{m} bp")
add(x, "layout", "gel", "ladders", "one ladder left and one ladder right of the 12 sample lanes")
add(x, "layout", "gel", "number of sample lanes", "12 (6 plasmids x 2 colonies)")
add(x, "observation", "pUX782 #1, #2", "band", "single strong band at about 2000 bp (#2 slightly higher than #1)", "medium")
add(x, "observation", "pUX783, pUX784, pUX785 (#1, #2)", "band", "single strong band at about 2800-3000 bp", "medium")
add(x, "observation", "pUX786, pUX787 (#1, #2)", "band", "single strong band at about 3000-3100 bp, slightly higher than pUX783-785", "medium")
add(x, "observation", "all lanes", "extra bands", "no additional bands visible; faint smear above the main band in pUX783-787 lanes", "medium")

by = {}
for f in F: by.setdefault(f["figure"], []).append(f)
out = {"name": "image_facts_draft_by_claude",
       "status": "DRAFT. Read from the images with vision by Claude (Sonnet 5.5, window image-reading session, 2026-10-06). NOT a manual annotation, NOT manual annotation, not to be mixed with annotations A and B. Needs review by the curator / user before any use in a manuscript.",
       "method": "images opened and viewed (prepared flat PNG or original; label rows of the blots enlarged 2x); every fact is one read-off. Second independent readings and the per-image agreement are in image_facts_agreement.md.",
       "counts": {k: len(v) for k, v in by.items()}, "total": len(F), "facts": F}
here = Path(__file__).parent
(here / "image_facts_draft_by_claude.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(out["total"], out["counts"])
