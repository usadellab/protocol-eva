#!/bin/bash
#$ -N vllm_serve
#$ -P GPU_express.p
#$ -pe smp 1
#$ -l h=!belfast.plabipd.de
#$ -j y
#$ -o $LLM_ROOT/logs/vllm_serve.$JOB_ID.out
# Generic vLLM server. Submit: qsub -q GPU_express.q[@hosts] -l gpu=N -l h_rt=05:30:00 -l h_vmem=250G -v CFG=<name> vllm_serve.qsub.sh
# Config file llm/jobs/cfg_<name>.sh defines: MODEL_DIR NAME TP MIN_FREE_MIB and optionally EXTRA_ENV (shell code) and EXTRA_ARGS (bash array),
# SMOKE_BODY_EXTRA (JSON fragment merged into each chat request, e.g. thinking switch).
LLM=$LLM_ROOT
source $LLM/jobs/cfg_$CFG.sh
PY=$LLM/env/${VENV:-vllm}/bin/python
ENDPOINT=$LLM/logs/vllm_endpoint_$JOB_ID.txt
SLOG=$LLM/logs/vllm_server.$JOB_ID.log

export HF_HOME=$LLM/env/hf_home HF_HUB_OFFLINE=1 TMPDIR=$LLM/env/tmp
export CUDA_HOME=/usr/local/cuda-13.1 PATH=$LLM/env/${VENV:-vllm}/bin:/usr/local/cuda-13.1/bin:$PATH
export VLLM_CACHE_ROOT=$LLM/env/vllm_cache XDG_CACHE_HOME=$LLM/env/xdg_cache
mkdir -p "$VLLM_CACHE_ROOT" "$XDG_CACHE_HOME" "$TMPDIR"
eval "$EXTRA_ENV"

echo "== host/date/job"; hostname; date; echo "JOB_ID=$JOB_ID CFG=$CFG CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES TP=$TP"
nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free,driver_version --format=csv
$PY --version; $PY -c "import vllm;print('vllm',vllm.__version__)" 2>&1 | tail -1

# every allocated GPU must have >= MIN_FREE_MIB free
OK=1; TOTAL=0; FREEMIN=999999999
for d in ${CUDA_VISIBLE_DEVICES//,/ }; do
  f=$(nvidia-smi -i $d --query-gpu=memory.free --format=csv,noheader,nounits | tr -d ' ')
  t=$(nvidia-smi -i $d --query-gpu=memory.total --format=csv,noheader,nounits | tr -d ' ')
  echo "gpu $d free=$f total=$t"; TOTAL=$t; [ "$f" -lt "$FREEMIN" ] && FREEMIN=$f
  [ "$f" -lt "$MIN_FREE_MIB" ] && OK=0
done
if [ $OK = 0 ]; then echo "EXIT: a GPU has < ${MIN_FREE_MIB} MiB free"; printf 'status=exited_not_enough_vram job=%s\n' "$JOB_ID" > "$ENDPOINT"; exit 0; fi
UTIL=$($PY -c "print(min(0.90, int((($FREEMIN-2500)/$TOTAL)*100)/100))")
PORT=$($PY -c 'import socket;s=socket.socket();s.bind(("",0));print(s.getsockname()[1])')
IP=$(getent ahostsv4 $(hostname) | awk '{print $1; exit}')
printf 'host=%s\nip=%s\nport=%s\nendpoint=%s:%s\nmodel=%s\njob=%s\nstatus=starting\n' "$(hostname)" "$IP" "$PORT" "$IP" "$PORT" "$NAME" "$JOB_ID" > "$ENDPOINT"

T0=$(date +%s)
vllm serve "$MODEL_DIR" --served-model-name "$NAME" --host 0.0.0.0 --port "$PORT" \
  --tensor-parallel-size "$TP" --max-model-len "${MAXLEN:-65536}" --gpu-memory-utilization "$UTIL" "${EXTRA_ARGS[@]}" >> "$SLOG" 2>&1 &
VPID=$!; echo "started vllm pid=$VPID port=$PORT util=$UTIL"
until curl -s --max-time 5 "http://127.0.0.1:$PORT/v1/models" | grep -q "$NAME"; do
  kill -0 $VPID 2>/dev/null || { echo "server died before ready"; printf 'status=failed job=%s\n' "$JOB_ID" > "$ENDPOINT"; exit 1; }
  sleep 10
done
LOAD=$(( $(date +%s) - T0 )); echo "READY after ${LOAD}s"
printf 'host=%s\nip=%s\nport=%s\nendpoint=%s:%s\nmodel=%s\njob=%s\nload_seconds=%s\nstatus=ready\n' "$(hostname)" "$IP" "$PORT" "$IP" "$PORT" "$NAME" "$JOB_ID" "$LOAD" > "$ENDPOINT"
cat "$ENDPOINT"

echo "== smoke test (invented toy data only)"
PORT=$PORT NAME=$NAME EXTRA="$SMOKE_BODY_EXTRA" $PY - <<'PYEOF'
import json, os, time, urllib.request
url = f"http://127.0.0.1:{os.environ['PORT']}/v1/chat/completions"
extra = json.loads(os.environ.get("EXTRA") or "{}")
def ask(prompt, max_tokens):
    body = {"model": os.environ["NAME"], "messages": [{"role": "user", "content": prompt}],
            "temperature": 1.0, "top_p": 0.95, "max_tokens": max_tokens, **extra}
    t = time.time()
    r = json.load(urllib.request.urlopen(urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})))
    dt = time.time() - t
    n = r["usage"]["completion_tokens"]
    print(f"[{dt:.1f}s, {n} tokens, {n/dt:.1f} tok/s, prompt_tokens={r['usage']['prompt_tokens']}]")
    print(r["choices"][0]["message"]["content"])
ask("Reply with OK", 64)
ask("Extract JSON {\"steps\":[{\"name\":str,\"temperature_c\":number,\"duration_min\":number}]} from this invented protocol: "
    "Step 1 Incubation: mix buffer A with sample X and incubate at 37 C for 30 min. "
    "Step 2 Wash: rinse twice with cold buffer B at 4 C, 5 min each. Return only JSON.", 600)
PYEOF
echo "== server stays up until h_rt (job $JOB_ID, $IP:$PORT)"; date
wait $VPID
echo "server exited"; date
