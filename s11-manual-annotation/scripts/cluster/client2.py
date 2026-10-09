#!/usr/bin/env python3
"""Cluster-side client: sends every request file of requests/ to one or more vLLM endpoints (OpenAI chat API), THREADS streams per endpoint, and saves the full response JSON to responses/<name>.json. Resume-safe (finished names are skipped).
Order: repeat, then prompt, then entry (partial results cover all prompts once before the second repeat starts). A failed request goes back into the queue; an endpoint with 3 failures in a row is dropped; the client ends when the queue is empty or no endpoint is left.
usage: client.py <requests_dir> <responses_dir> <threads_per_endpoint> <base_url> [<base_url> ...]       No data leaves the cluster; no timeout."""
import json, sys, time, threading, urllib.request
from pathlib import Path
req_dir, out_dir, threads, bases = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]), sys.argv[4:]
def key(p):
    case, prompt, rep = p.stem.split("_"); return (rep, prompt, case)
import os
todo = [p for p in sorted(req_dir.glob("*.json"), key=key, reverse=bool(os.environ.get("REVERSE"))) if not (out_dir / p.name).exists()]
lock = threading.Lock(); dead = set(); fails = {b: 0 for b in bases}
def worker(base):
    while True:
        with lock:
            if base in dead or not todo: return
            p = todo.pop(0)
        if (out_dir / p.name).exists(): continue          # another client finished it meanwhile
        job = json.loads(p.read_text()); t0 = time.time()
        try:
            r = urllib.request.Request(base + "/v1/chat/completions", json.dumps(job["body"]).encode(), {"Content-Type": "application/json"})
            with urllib.request.urlopen(r) as resp: answer = json.load(resp)
        except Exception as e:                                     # endpoint error: nothing saved, request back into the queue
            with lock:
                todo.append(p); fails[base] += 1
                if fails[base] >= 3: dead.add(base)
            print(time.strftime("%H:%M:%S"), base, p.stem, "ENDPOINT ERROR", repr(e)[:160], flush=True); time.sleep(20); continue
        with lock: fails[base] = 0
        (out_dir / p.name).write_text(json.dumps({"name": p.stem, "seconds": round(time.time() - t0), "endpoint": base, "response": answer}))
        u = answer.get("usage", {}); print(time.strftime("%H:%M:%S"), p.stem, round(time.time() - t0), "s", u.get("completion_tokens"), "tok", answer["choices"][0].get("finish_reason"), base, flush=True)
ts = [threading.Thread(target=worker, args=(b,)) for b in bases for _ in range(threads)]
[t.start() for t in ts]; [t.join() for t in ts]
print("ALL DONE" if not todo else f"STOPPED with {len(todo)} requests left (no endpoint reachable)", flush=True)
