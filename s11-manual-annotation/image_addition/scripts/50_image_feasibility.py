#!/opt/homebrew/bin/python3.13
"""Phase 3 of PLAN_images_in_prompt.md: feasibility of reading the 13 images, one describe-and-list prompt, n = 1 per image and route.

Routes (one at a time; the caller holds the mutex /tmp/elab2arc_local_model.lock):
  lmstudio   http://127.0.0.1:1234  google/gemma-4-31b, context 131072, images flattened + capped to <= 1000 px (48_prepare_images.py)
  omlx       http://127.0.0.1:8082  MiniMax-M3-4bit
Crash policy (LM Studio): HTTP 400 "model has crashed" is an infrastructure event, not a model failure: log it, unload + reload the model, retry up to 2 times;
a failure that persists after 2 retries is recorded as failed. Every event goes to work/image_phase3/<route>/crashes.jsonl. oMLX: HTTP >= 500 / connection errors: same retry, no reload.
Output: work/image_phase3/<route>/<case>_<figure>.json (prompt, answer, usage, seconds, attempts); existing records are skipped (resumable).

  50_image_feasibility.py run <lmstudio|omlx>
  50_image_feasibility.py --control      crash policy against a local fake server (no model)
"""
import base64, http.server, json, subprocess, sys, threading, time, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LMS = str(Path.home() / ".lmstudio/bin/lms")
ROUTES = {"lmstudio": {"endpoint": "http://127.0.0.1:1234/v1/chat/completions", "model": "google/gemma-4-31b", "reload": True},
          "omlx": {"endpoint": "http://127.0.0.1:8082/v1/chat/completions", "model": "MiniMax-M3-4bit", "reload": False}}
CASES = {"phage": "work/eval_phage", "sdy1": "work/eval_sdy1", "biolector034": "work/eval_biolector034", "ux511": "work/eval_ux511", "pux782": "work/eval_pux782"}
PROMPT = """This picture is attached to an electronic lab notebook entry. Answer in exactly this format and describe only what is visible; write "unclear" instead of guessing; never invent labels or numbers.
TYPE: one line (what kind of figure).
TEXT: every printed text label, one per line, verbatim, in reading order (top to bottom, left to right).
LANES: for a gel or blot: the lane labels from left to right, one per line as "n. label"; add "(green)" after a label printed in green; for any other figure write NONE.
MARKERS: the size-marker labels, one per line (NONE if there are none).
NUMBERS: every other printed number with what it belongs to (axis maxima, concentrations, OD values).
OBSERVATIONS: up to 8 short lines on what the picture shows that is not printed text (band positions against the markers, which lanes differ, growth or no growth, curve levels); write "approximate" for estimates."""


def reload_model(route):
    cfg = ROUTES[route]
    subprocess.run([LMS, "unload", "--all"], capture_output=True)
    time.sleep(3)
    subprocess.run([LMS, "load", cfg["model"], "--context-length", "131072", "-y"], capture_output=True)


def request(route, png_bytes, run_dir, tag, retries=2, post=None, reload=None, max_tokens=6000):
    """one request with the crash policy; post / reload can be replaced for the control"""
    cfg = ROUTES[route]
    body = {"model": cfg["model"], "temperature": 0, "max_tokens": max_tokens, "stream": False,
            "messages": [{"role": "user", "content": [{"type": "text", "text": PROMPT},
                         {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(png_bytes).decode()}}]}]}
    post = post or (lambda b: json.load(urllib.request.urlopen(urllib.request.Request(cfg["endpoint"], json.dumps(b).encode(), {"Content-Type": "application/json"}), timeout=3600)))
    reload = reload or (lambda: reload_model(route))
    for attempt in range(retries + 1):
        t0 = time.time()
        try:
            j = post(body)
            m = j["choices"][0]["message"]
            return {"ok": True, "attempts": attempt + 1, "seconds": round(time.time() - t0, 1), "usage": j.get("usage"), "finish": j["choices"][0].get("finish_reason"),
                    "answer": m.get("content") or "", "reasoning_chars": len(m.get("reasoning_content") or m.get("reasoning") or "")}
        except urllib.error.HTTPError as e:
            txt = e.read().decode("utf8", "replace")[:500]; kind = "crash" if (e.code == 400 and "crash" in txt.lower()) else f"http{e.code}"
        except Exception as e:
            txt, kind = f"{type(e).__name__}: {e}", "error"
        with open(run_dir / "crashes.jsonl", "a") as fh:
            fh.write(json.dumps({"time": time.strftime("%F %T"), "tag": tag, "attempt": attempt + 1, "kind": kind, "detail": txt}) + "\n")
        if attempt < retries and (cfg["reload"] and kind == "crash" or not cfg["reload"] or kind != "crash"):
            if cfg["reload"] and kind == "crash": reload()
            else: time.sleep(5)
    return {"ok": False, "attempts": retries + 1, "answer": "", "error": f"{kind}: {txt}"}


def run(route):
    run_dir = ROOT / "work/image_phase3" / route; run_dir.mkdir(parents=True, exist_ok=True)
    for case, d in CASES.items():
        for e in json.loads((ROOT / d / "images/manifest.json").read_text()):
            fig = Path(e["file"]).stem; out = run_dir / f"{case}_{fig}.json"
            if out.exists() and json.loads(out.read_text()).get("ok"):
                print("skip", out.name); continue
            rec = request(route, (ROOT / d / e["file"]).read_bytes(), run_dir, f"{case}:{fig}")
            rec.update(route=route, model=ROUTES[route]["model"], figure=f"{case}:{fig}", sent_size=e["sent_size"], prompt=PROMPT)
            out.write_text(json.dumps(rec, indent=1, ensure_ascii=False))
            print(out.name, rec["ok"], rec.get("seconds"), "s", rec.get("usage") and rec["usage"].get("prompt_tokens"), "attempts", rec["attempts"], flush=True)


def control():
    import tempfile
    bad = 0
    def check(name, ok):
        nonlocal bad
        print(("ok   " if ok else "FAIL ") + name); bad += (not ok)
    png = b"\x89PNG fake"
    def fake(sequence):
        calls = {"n": 0, "reloads": 0}
        def post(b):
            r = sequence[min(calls["n"], len(sequence) - 1)]; calls["n"] += 1
            if r == "ok": return {"choices": [{"message": {"content": "TYPE: x"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 1}}
            raise urllib.error.HTTPError("u", r[0], "x", {}, __import__("io").BytesIO(r[1].encode()))
        return calls, post, (lambda: calls.__setitem__("reloads", calls["reloads"] + 1))
    crash = (400, '{"error":"The model has crashed without additional information. (Exit code: null)"}')
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        c, p, rl = fake([crash, "ok"]); r = request("lmstudio", png, td, "t1", post=p, reload=rl)
        check("one crash then ok: result ok, 2 attempts, 1 reload, 1 crash logged", r["ok"] and r["attempts"] == 2 and c["reloads"] == 1 and len((td / "crashes.jsonl").read_text().splitlines()) == 1)
        (td / "crashes.jsonl").unlink()
        c, p, rl = fake([crash, crash, "ok"]); r = request("lmstudio", png, td, "t2", post=p, reload=rl)
        check("two crashes then ok: result ok, 3 attempts, 2 reloads, 2 crashes logged", r["ok"] and r["attempts"] == 3 and c["reloads"] == 2 and len((td / "crashes.jsonl").read_text().splitlines()) == 2)
        (td / "crashes.jsonl").unlink()
        c, p, rl = fake([crash]); r = request("lmstudio", png, td, "t3", post=p, reload=rl)
        check("persistent crash: recorded as failed after 3 attempts, 2 reloads", (not r["ok"]) and r["attempts"] == 3 and c["reloads"] == 2 and "crash" in r["error"])
        c, p, rl = fake([(400, '{"error":"bad request"}'), "ok"]); r = request("lmstudio", png, td, "t4", post=p, reload=rl, retries=0)
        check("a 400 that is not a crash is not treated as one (no reload)", (not r["ok"]) and c["reloads"] == 0 and "http400" in r["error"])
    print("50 controls " + ("OK" if not bad else f"FAILED ({bad})")); sys.exit(1 if bad else 0)


if __name__ == "__main__":
    if sys.argv[1:] == ["--control"]: control()
    elif len(sys.argv) == 3 and sys.argv[1] == "run" and sys.argv[2] in ROUTES: run(sys.argv[2])
    else: sys.exit(__doc__)
