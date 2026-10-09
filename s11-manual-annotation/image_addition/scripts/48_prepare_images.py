#!/opt/homebrew/bin/python3.13
"""Phase 1 of PLAN_images_in_prompt.md: the image files of the five entries, prepared once for every route.

For each `![alt](path)` of work/eval_<case>/input/*.md the upload is found (helpers of 45_caption_images.py: .eln member, phage export, pUX782 attachment),
flattened on white (alpha = 255) and capped to <= 1000 px long edge and <= 0.8 Mpx (Gemma-4-31B in LM Studio crashes above ~1.26 Mpx), PNG.
Output per case: work/eval_<case>/images/<uuid8>.png and work/eval_<case>/images/manifest.json
  [{index, alt, path, file, source_sha256, original_size, sent_size, sha256}]   (the resolver of 47_image_parts.js reads path -> file)

  48_prepare_images.py [case ...]     prepare (default: all five)
  48_prepare_images.py --control      mechanical controls of phase 1 (needs the 5 manifests; compiles 49_ocr_vision.swift if /tmp/ocr_vision is missing)
"""
import hashlib, importlib.util, io, json, re, subprocess, sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("cap45", ROOT / "scripts" / "45_caption_images.py")
C = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(C)
CASES = list(C.CASES)
EXPECTED = {"phage": 1, "sdy1": 2, "biolector034": 2, "ux511": 7, "pux782": 1}
OCR = Path("/tmp/ocr_vision")


def prepare(case):
    d = ROOT / C.CASES[case][0]
    md = next((d / "input").glob("*.md")).read_text()
    out = d / "images"; out.mkdir(exist_ok=True)
    manifest = []
    for i, m in enumerate(C.IMG.finditer(md)):
        alt, path = m.group(1), m.group(2)
        found = C.find_image(case, alt, path)
        if not found:
            print(f"  {case}: NOT FOUND {path}"); continue
        raw, uid = found
        png, orig, sent = C.flatten_cap(raw)
        name = f"{uid}.png"
        (out / name).write_bytes(png)
        manifest.append({"index": i, "alt": alt, "path": path, "file": f"images/{name}", "source_sha256": hashlib.sha256(raw).hexdigest(),
                         "original_size": list(orig), "sent_size": list(sent), "sha256": hashlib.sha256(png).hexdigest()})
        print(f"  {case}: {path.split('/')[-1]} {orig} -> {sent}")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return manifest


def ocr(png_bytes, rotate=False):
    if not OCR.exists():
        subprocess.run(["swiftc", "-O", str(ROOT / "scripts/49_ocr_vision.swift"), "-o", str(OCR)], check=True)
    tmp = Path("/tmp/_ocr_in.png"); tmp.write_bytes(png_bytes)
    return subprocess.run([str(OCR), str(tmp)] + (["--rotate"] if rotate else []), capture_output=True, text=True).stdout


def control():
    bad = 0
    def check(name, ok, detail=""):
        nonlocal bad
        print(("ok   " if ok else "FAIL ") + name + ("" if ok else "  " + str(detail))); bad += (not ok)
    manifests = {c: json.loads((ROOT / C.CASES[c][0] / "images/manifest.json").read_text()) for c in CASES}
    for c in CASES:
        check(f"{c}: every ![]() line resolved ({EXPECTED[c]})", len(manifests[c]) == EXPECTED[c], len(manifests[c]))
    files = [(c, e) for c in CASES for e in manifests[c]]
    for c, e in files:
        im = Image.open(ROOT / C.CASES[c][0] / e["file"])
        w, h = im.size
        ok = im.mode == "RGB" and max(w, h) <= 1000 and w * h <= 800_000
        check(f"{c} {Path(e['file']).name}: opaque RGB, cap respected {im.size}", ok, (im.mode, im.size))
        if not ok: continue
        check(f"{c} {Path(e['file']).name}: sha256 matches the manifest", hashlib.sha256((ROOT / C.CASES[c][0] / e["file"]).read_bytes()).hexdigest() == e["sha256"])
    # the cap check must fail on an uncapped image, the flatten check on an RGBA one
    raw = C.find_image("phage", "", "x/Bacteriophages_extracted_DNA_Gel_403059.elab2arc.png")[0]
    big = Image.open(io.BytesIO(raw))
    check("control: the cap check fails on the raw 1741x2158 gel", not (max(big.size) <= 1000), big.size)
    check("control: the opaque check fails on the raw gel (mode RGBA)", big.mode != "RGB", big.mode)
    check("control: a wrong path is not found", C.find_image("sdy1", "", "x/grafik_deadbeef.elab2arc.png") is None)
    # OCR on the prepared phage gel reads the 7 lane labels and 4 size marks; on the raw gel it reads none
    gel = ROOT / C.CASES["phage"][0] / manifests["phage"][0]["file"]
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    truth = ["BD_R1", "BD_R2", "BD_R3", "B_R1", "B_R2", "B_R3", "1kb Plus ladder", "20 kb", "5 kb", "1.5 kb", "0.5 kb"]
    t = norm(ocr(gel.read_bytes(), rotate=True)); tr = norm(ocr(raw, rotate=True))
    got = [x for x in truth if norm(x) in t]
    check(f"OCR reads the phage labels on the prepared gel ({len(got)}/11; need >= 10)", len(got) >= 10, [x for x in truth if x not in got])
    rawgot = [x for x in truth if norm(x) in tr]
    check(f"control: OCR reads (almost) none of them on the raw RGBA gel ({len(rawgot)}/11)", len(rawgot) <= 2, rawgot)
    # the builder resolves the real prompts through the manifests (47_image_parts.js via node)
    js = r"""
const P=require('./47_image_parts.js'),fs=require('fs'),path=require('path');
const cases={phage:'work/eval_phage',sdy1:'work/eval_sdy1',biolector034:'work/eval_biolector034',ux511:'work/eval_ux511',pux782:'work/eval_pux782'};const out={};
for(const [c,d] of Object.entries(cases)){const dir=path.join('..',d);const f=fs.readdirSync(path.join(dir,'input')).find(x=>x.endsWith('.md'));const md=fs.readFileSync(path.join(dir,'input',f),'utf8');
const man=JSON.parse(fs.readFileSync(path.join(dir,'images/manifest.json')));const map=new Map(man.map(e=>[e.path,e.file]));
const r=P.buildContent(md,(a,p)=>map.has(p)?'data:image/png;base64,'+fs.readFileSync(path.join(dir,map.get(p))).toString('base64'):null);
out[c]={images:r.report.images.length,unresolved:r.report.unresolved.length,parts:Array.isArray(r.content)?r.content.length:0};}
console.log(JSON.stringify(out));"""
    r = json.loads(subprocess.run(["node", "-e", js], cwd=ROOT / "scripts", capture_output=True, text=True, check=True).stdout)
    for c, v in r.items():
        check(f"{c}: builder + manifest resolves {EXPECTED[c]} images, 0 unresolved", v["images"] == EXPECTED[c] and v["unresolved"] == 0 and v["parts"] >= 2 * EXPECTED[c], v)
    print("48 controls " + ("OK" if not bad else f"FAILED ({bad})")); sys.exit(1 if bad else 0)


if __name__ == "__main__":
    if sys.argv[1:] == ["--control"]:
        control()
    for c in (sys.argv[1:] or CASES):
        prepare(c)
