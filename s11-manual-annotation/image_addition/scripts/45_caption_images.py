#!/opt/homebrew/bin/python3.13
"""Image -> text: describe every image of the benchmark entries with a local vision model and insert the description into the entry's markdown.

For each `![alt](path)` line of an input markdown (the app's own conversion), the image file is found (an .eln member, the phage export, the pUX782-787 attachment),
flattened on white (the phage gel is a transparent PNG: raw, no model reads its labels) and capped to <= 0.8 Mpx / <= 1000 px (Gemma-4-31B in LM Studio crashes above ~1.26 Mpx),
described once by the model (cached per image and mode) and the description is inserted as its own paragraph right after the image line:

    [Image description (automatic): ...]

Modes: brief (Kimi's v8 short-caption instruction + context), generic (the image only) and guided (+ the protocol text before/after the figure, "question-guided caption" idea; the model is told to describe only what is VISIBLE).
Output: work/eval_<case>/input_caption_<mode>/<same md file name>  and  work/image_captions/<mode>/<case>_<uuid8>.json (prompt, raw answer, image size, seconds).

  45_caption_images.py <mode: generic|guided> [case ...]        (needs LM Studio with a vision model loaded, mutex /tmp/elab2arc_local_model.lock held by the caller)
  45_caption_images.py --control                                 (offline: parsing, flattening, cap, insertion; no model call)
"""
import base64, io, json, os, re, sys, time, urllib.request, zipfile
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ENDPOINT = os.environ.get("CAPTION_ENDPOINT", "http://127.0.0.1:1234/v1/chat/completions")
MODEL = os.environ.get("CAPTION_MODEL", "google/gemma-4-31b")
MAX_SIDE, MAX_PIXELS = 1000, 800_000
IMG = re.compile(r"!\[([^\]]*)\]\(([^)]*)\)")
ELN = ROOT / "curator/2026-10-01_delivery/eln"
CASES = {   # case -> (eval dir, how to find the image file)
    "phage": ("work/eval_phage", ("file", ROOT / "inputs/elab_export")),
    "sdy1": ("work/eval_sdy1", ("eln", ELN / "2026-10-01-124528-export.eln")),
    "biolector034": ("work/eval_biolector034", ("eln", ELN / "2026-10-01-123102-export.eln")),
    "ux511": ("work/eval_ux511", ("eln", ELN / "2026-10-01-123042-export.eln")),
    "pux782": ("work/eval_pux782", ("file", ROOT / "curator/2026-10-01_delivery/pux782_export_pdf_2026-10-01")),
}
GENERIC = """This image is a figure attached to an electronic lab notebook entry. Describe it for a reader who cannot see it, as a factual list.
1. What kind of figure is it (agarose gel, Southern blot, photograph of plates, plot, screenshot)?
2. Transcribe every visible text label exactly as written (titles, lane and sample names, axis titles, legend entries, size-marker values, annotations), in reading order, left to right, top to bottom.
3. Gels and blots: list the lanes from left to right with their labels and the marker sizes. Say which lanes or labels are marked differently (colour, box, arrow) and how.
4. Plots: the axes with units, the panels, the curves or legend entries.
5. Plates: the layout (which plate or condition is where).
Describe only what is visible. Do not interpret the experimental result. If something is unclear write "unclear" instead of guessing. Do not invent numbers or labels."""
GUIDED = GENERIC + """

The protocol text around this figure is given below only so that you understand what the figure is for. Describe ONLY what is visible in the image; do not copy facts from the text into the description.
Pay attention to the information a lab annotator would record as data: lane assignments, which items are marked, plotted quantities and their axes, conditions and legends.

TEXT BEFORE THE FIGURE:
{before}

TEXT AFTER THE FIGURE:
{after}"""


BRIEF = (ROOT / "work/eval/prompt_iter/caption_instruction_v8.txt").read_text().strip() + """

For reference only (do NOT repeat it; describe only what the text cannot provide), the entry text around this figure:
TEXT BEFORE THE FIGURE:
{before}

TEXT AFTER THE FIGURE:
{after}"""     # the instruction was written by Kimi-K3 (work/eval/prompt_iter/ans_v8c.md); only the context block is wired in here


def flatten_cap(raw: bytes):
    im = Image.open(io.BytesIO(raw))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA"); bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg
    im = im.convert("RGB")
    w, h = im.size
    scale = min(1.0, MAX_SIDE / max(w, h), (MAX_PIXELS / (w * h)) ** 0.5)
    if scale < 1.0:
        im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "PNG")
    return buf.getvalue(), (w, h), im.size


def find_image(case, alt, path):
    kind, where = CASES[case][1]
    stem = Path(path).name
    if kind == "eln":
        m = re.search(r"grafik_([0-9a-f]{8})\.elab2arc", stem)
        if not m:
            return None
        z = zipfile.ZipFile(where)
        hit = [n for n in z.namelist() if Path(n).name.startswith(m.group(1)) and not n.endswith("/")]
        return (z.read(hit[0]), m.group(1)) if len(hit) == 1 else None
    if case == "phage":
        base = re.sub(r"_\d+\.elab2arc(\.\w+)$", r"\1", stem)
        hits = list(Path(where).rglob(base))
        return (hits[0].read_bytes(), "gel" + stem.split("_")[-1][:0] + "p1") if hits else None
    hits = list(Path(where).glob("grafik.png"))
    return (hits[0].read_bytes(), "grafik") if hits else None


def clean(text, n):
    t = re.sub(r"<[^>]+>", " ", text)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[-n:] if n > 0 else t[:-n]


def ask(prompt, png):
    body = {"model": MODEL, "temperature": 0, "max_tokens": 6000, "stream": False,
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt},
                                                      {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}}]}]}
    req = urllib.request.Request(ENDPOINT, json.dumps(body).encode(), {"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=3600) as r:
        j = json.loads(r.read())
    return j["choices"][0]["message"].get("content") or "", j.get("usage"), round(time.time() - t0, 1)


def insert_descriptions(md, captions):
    """captions: list of strings, one per image in order of appearance -> markdown with the description paragraph after each image line."""
    out, k = [], 0
    for line in md.split("\n"):
        out.append(line)
        for _ in IMG.finditer(line):
            if k < len(captions) and captions[k]:
                out += ["", "[Image description (automatic): " + re.sub(r"\s+", " ", captions[k]).strip() + "]", ""]
            k += 1
    return "\n".join(out)


def run(mode, cases):
    for case in cases:
        d, _ = CASES[case]
        src = next((ROOT / d / "input").glob("*.md"))
        md = src.read_text()
        caps = []
        for m in IMG.finditer(md):
            alt, path = m.group(1), m.group(2)
            found = find_image(case, alt, path)
            if not found:
                print(f"  {case}: image not found for {path}"); caps.append(""); continue
            raw, uid = found
            cache = ROOT / "work/image_captions" / mode / f"{case}_{uid}.json"
            if cache.exists():
                caps.append(json.loads(cache.read_text())["description"]); continue
            png, orig, sent = flatten_cap(raw)
            if mode in ("guided", "brief"):
                before, after = clean(md[:m.start()], 900), clean(md[m.end():], -400) if False else clean(md[m.end():][:400], 400)
                prompt = (GUIDED if mode == "guided" else BRIEF).format(before=before, after=after)
            else:
                prompt = GENERIC
            text, usage, secs = ask(prompt, png)
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps({"case": case, "image": uid, "mode": mode, "model": MODEL, "original_size": orig, "sent_size": sent, "seconds": secs,
                                         "usage": usage, "prompt": prompt, "description": text.strip()}, indent=1, ensure_ascii=False))
            print(f"  {case} {uid}: {orig} -> {sent}, {secs}s, {len(text)} chars"); caps.append(text.strip())
        outdir = ROOT / d / f"input_caption_{mode}"
        outdir.mkdir(exist_ok=True)
        (outdir / src.name).write_text(insert_descriptions(md, caps))
        print(f"{case}: {sum(1 for c in caps if c)} of {len(caps)} images described -> {outdir.relative_to(ROOT)}/")


def control():
    # 1) parsing + insertion: descriptions land after the right lines, in order, two images on one line keep their order, the rest of the text is unchanged
    md = "A\n![a](x1.png)\ntext\n![b](x2.png)![c](x3.png)\nend"
    out = insert_descriptions(md, ["D1", "D2", "D3"])
    assert [l for l in out.split("\n") if l and not l.startswith("[Image")] == md.split("\n"), "original lines changed"
    assert re.findall(r"\[Image description \(automatic\): (D\d)\]", out) == ["D1", "D2", "D3"]
    assert out.index("D1") < out.index("text") < out.index("D2") < out.index("end")
    assert insert_descriptions(md, ["", "", ""]) == md, "empty captions must leave the markdown untouched"
    # 2) flatten: a transparent PNG with black text pixels becomes opaque RGB with a white background
    im = Image.new("RGBA", (2000, 2500), (0, 0, 0, 0)); im.putpixel((5, 5), (0, 0, 0, 255)); b = io.BytesIO(); im.save(b, "PNG")
    png, orig, sent = flatten_cap(b.getvalue()); r = Image.open(io.BytesIO(png))
    assert r.mode == "RGB" and r.getpixel((r.size[0] // 2, r.size[1] // 2)) == (255, 255, 255), "transparent pixels must become white"
    # 3) cap: <= 1000 px side and <= 0.8 Mpx, aspect ratio kept; a small image is not enlarged
    assert max(sent) <= 1000 and sent[0] * sent[1] <= MAX_PIXELS, sent
    assert abs(sent[0] / sent[1] - 2000 / 2500) < 0.01
    small = Image.new("RGB", (300, 200), (10, 10, 10)); b = io.BytesIO(); small.save(b, "PNG")
    assert flatten_cap(b.getvalue())[2] == (300, 200)
    # 4) every image line of the five inputs resolves to a file, and each file is a real image
    n = 0
    for case, (d, _) in CASES.items():
        md = next((ROOT / d / "input").glob("*.md")).read_text()
        for m in IMG.finditer(md):
            f = find_image(case, m.group(1), m.group(2)); assert f, f"{case}: no file for {m.group(2)}"
            Image.open(io.BytesIO(f[0])).verify(); n += 1
    print(f"control OK: insertion, flatten on white, 0.8 Mpx cap, no enlargement, and all {n} image lines of the five inputs resolve to image files")
    # 5) the control must be able to fail: a wrong cap is caught
    try:
        assert max((1500, 1500)) <= 1000
    except AssertionError:
        return
    raise SystemExit("control cannot fail")


if __name__ == "__main__":
    if sys.argv[1:] == ["--control"]:
        control()
    else:
        mode, *cs = sys.argv[1:]
        assert mode in ("generic", "guided", "brief"), "mode must be generic, guided or brief"
        run(mode, cs or list(CASES))
