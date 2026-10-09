#!/bin/bash
#$ -N vllm_gemma2
#$ -q GPU_express.q
#$ -P GPU_express.p
#$ -pe smp 1
#$ -l gpu=1
#$ -l h_rt=05:30:00
#$ -l h=!belfast.plabipd.de
#$ -l h_vmem=250G
#$ -j y
#$ -o $LLM_ROOT/logs/vllm_gemma.$JOB_ID.out
# vLLM server for Gemma 4 31B-it: BF16 if >= 74 GB free on the allocated GPU, else QAT w4a16 (compressed-tensors).
LLM=$LLM_ROOT
PY=$LLM/env/vllm/bin/python
ENDPOINT=$LLM/logs/vllm_endpoint_$JOB_ID.txt
SLOG=$LLM/logs/vllm_server.$JOB_ID.log
BF16=$LLM/models/gemma-4-31B-it
QAT=$LLM/models/gemma-4-31B-it-qat-w4a16-ct
NAME=gemma-4-31b-it
MIN_BF16_MIB=74000
MIN_QAT_MIB=34000

export HF_HOME=$LLM/env/hf_home HF_HUB_OFFLINE=1 TMPDIR=$LLM/env/tmp
export CUDA_HOME=/usr/local/cuda-13.1 PATH=$LLM/env/vllm/bin:/usr/local/cuda-13.1/bin:$PATH
export VLLM_CACHE_ROOT=$LLM/env/vllm_cache XDG_CACHE_HOME=$LLM/env/xdg_cache
mkdir -p "$VLLM_CACHE_ROOT" "$XDG_CACHE_HOME" "$TMPDIR"

echo "== host/date/job"; hostname; date; echo "JOB_ID=$JOB_ID CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
echo "== nvidia-smi"; nvidia-smi --query-gpu=index,name,memory.total,memory.used,memory.free,driver_version --format=csv
nvidia-smi | head -20; $PY --version; df -h $CLUSTER_DATA | tail -1

FREE=$(nvidia-smi -i "${CUDA_VISIBLE_DEVICES%%,*}" --query-gpu=memory.free --format=csv,noheader,nounits | tr -d ' ')
TOTAL=$(nvidia-smi -i "${CUDA_VISIBLE_DEVICES%%,*}" --query-gpu=memory.total --format=csv,noheader,nounits | tr -d ' ')
echo "free=${FREE} MiB total=${TOTAL} MiB"

pick_free_port() { $PY -c 'import socket;s=socket.socket();s.bind(("",0));print(s.getsockname()[1])'; }

start_server() {  # $1 = variant (bf16|qat), $2 = model dir, $3 = gpu util
  PORT=$(pick_free_port)
  printf 'host=%s\nport=%s\nendpoint=%s:%s\nmodel=%s\nvariant=%s\njob=%s\nstatus=starting\n' \
    "$(hostname)" "$PORT" "$(hostname)" "$PORT" "$NAME" "$1" "$JOB_ID" > "$ENDPOINT"
  T0=$(date +%s)
  $LLM/env/vllm/bin/vllm serve "$2" --served-model-name "$NAME" --host 0.0.0.0 --port "$PORT" \
    --max-model-len 65536 --gpu-memory-utilization "$3" --max-num-seqs 8 >> "$SLOG" 2>&1 &
  VPID=$!
  echo "started vllm pid=$VPID variant=$1 port=$PORT util=$3 (log $SLOG)"
}

wait_ready() {
  until curl -s --max-time 5 "http://127.0.0.1:$PORT/v1/models" | grep -q "$NAME"; do
    kill -0 $VPID 2>/dev/null || { echo "server died before ready"; return 1; }
    sleep 10
  done
  LOAD=$(( $(date +%s) - T0 )); echo "READY after ${LOAD}s"
}

if   [ "$FREE" -ge "$MIN_BF16_MIB" ]; then VARIANT=bf16; DIR=$BF16
elif [ "$FREE" -ge "$MIN_QAT_MIB" ];  then VARIANT=qat;  DIR=$QAT
else echo "EXIT: only ${FREE} MiB free on the allocated GPU, QAT needs >= ${MIN_QAT_MIB} MiB"; \
     printf 'status=exited_not_enough_vram free_mib=%s job=%s\n' "$FREE" "$JOB_ID" > "$ENDPOINT"; exit 0; fi

util_for() { $PY -c "print(min(0.90, int((($FREE-2500)/$TOTAL)*100)/100))"; }
start_server $VARIANT "$DIR" "$(util_for)"
if ! wait_ready && [ "$VARIANT" = bf16 ] && [ "$FREE" -ge "$MIN_QAT_MIB" ]; then
  echo "BF16 start failed (see $SLOG); falling back to QAT w4a16"
  VARIANT=qat; DIR=$QAT; start_server $VARIANT "$DIR" "$(util_for)"
  wait_ready || { printf 'status=failed job=%s\n' "$JOB_ID" > "$ENDPOINT"; exit 1; }
elif ! kill -0 $VPID 2>/dev/null; then printf 'status=failed job=%s\n' "$JOB_ID" > "$ENDPOINT"; exit 1; fi

printf 'host=%s\nport=%s\nendpoint=%s:%s\nmodel=%s\nvariant=%s\njob=%s\nload_seconds=%s\nstatus=ready\n' \
  "$(hostname)" "$PORT" "$(hostname)" "$PORT" "$NAME" "$VARIANT" "$JOB_ID" "$LOAD" > "$ENDPOINT"
cat "$ENDPOINT"

echo "== smoke test (invented toy data only)"
PORT=$PORT NAME=$NAME $PY - <<'PYEOF'
import json, os, time, urllib.request
url = f"http://127.0.0.1:{os.environ['PORT']}/v1/chat/completions"
def ask(prompt, max_tokens):
    body = {"model": os.environ["NAME"], "messages": [{"role": "user", "content": prompt}],
            "temperature": 1.0, "top_p": 0.95, "top_k": 64, "max_tokens": max_tokens}
    t = time.time()
    r = json.load(urllib.request.urlopen(urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})))
    dt = time.time() - t
    n = r["usage"]["completion_tokens"]
    print(f"[{dt:.1f}s, {n} tokens, {n/dt:.1f} tok/s, prompt_tokens={r['usage']['prompt_tokens']}]")
    print(r["choices"][0]["message"]["content"])
ask("Reply with OK", 16)
ask("Extract JSON {\"steps\":[{\"name\":str,\"temperature_c\":number,\"duration_min\":number}]} from this invented protocol: "
    "Step 1 Incubation: mix buffer A with sample X and incubate at 37 C for 30 min. "
    "Step 2 Wash: rinse twice with cold buffer B at 4 C, 5 min each. Return only JSON.", 300)
PYEOF

echo "== server stays up until h_rt (job $JOB_ID, $(hostname):$PORT)"; date
wait $VPID
echo "server exited"; date
