#!/usr/bin/env python3
"""Compare the Table S11-2 printed in README.md with the Table S11-2 of the supplement (docs/Supplement_S11_manual_annotation_comparison.docx), cell by cell. Standard library only.
    python3 scripts/check_table_s11_2.py"""
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

SECTION = Path(__file__).resolve().parents[1]
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def docx_table(path):
    root = ET.fromstring(zipfile.ZipFile(path).read("word/document.xml"))
    for tbl in root.iter(W + "tbl"):
        rows = [[" / ".join("".join(t.text or "" for t in p.iter(W + "t")) for p in tc.iter(W + "p")) for tc in tr.findall(W + "tc")] for tr in tbl.findall(W + "tr")]
        if len(rows[0]) == 13:
            return rows
    raise SystemExit("no 13-column table in the docx")


def readme_table(path):
    text = Path(path).read_text()
    block = text.split("<!-- table-s11-2 -->")[1].split("<!-- /table-s11-2 -->")[0]
    lines = [l for l in block.strip().splitlines() if l.startswith("|")]
    return [[c.strip().replace("<br>", " / ") for c in l.strip("|").split("|")] for l in lines if not re.match(r"^\|[-| ]+\|$", l)]


a, b = docx_table(SECTION / "docs/Supplement_S11_manual_annotation_comparison.docx"), readme_table(SECTION / "README.md")
assert len(a) == len(b), (len(a), len(b))
bad = [(i, j, x, y) for i, (ra, rb) in enumerate(zip(a, b)) for j, (x, y) in enumerate(zip(ra, rb)) if x != y]
print(f"docx table {len(a)} rows x {len(a[0])} columns, README table {len(b)} rows x {len(b[0])} columns; {len(bad)} cells differ")
for i, j, x, y in bad:
    print(f"  row {i} column {j}: docx {x!r} README {y!r}")
sys.exit(1 if bad else 0)
