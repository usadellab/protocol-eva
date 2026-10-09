#!/opt/homebrew/bin/python3.13
"""Send one request to Kimi-K3 through the Kimi Code CLI (coding plan, NOT together.ai) in an empty temp dir; write the final message to a file.
  ask_kimi_cli.py <request.md> <answer.md>     request.md = the whole prompt; no tools needed. A quota/HTTP error aborts (nothing is written)."""
import subprocess, sys, tempfile
from pathlib import Path
req, ans = Path(sys.argv[1]), Path(sys.argv[2])
with tempfile.TemporaryDirectory() as empty:
    p = subprocess.run(["kimi-cli", "--print", "--final-message-only", "-m", "kimi-code/k3", "-y", "-p", req.read_text()], cwd=empty, capture_output=True, text=True)
if p.returncode != 0 or "Error code" in p.stdout[:200]:
    sys.exit(f"kimi-cli failed (exit {p.returncode}): {(p.stdout[:300] + p.stderr[-300:])}")
ans.write_text(p.stdout)
print(f"{ans}: {len(p.stdout)} chars")
