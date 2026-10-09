#!/bin/bash
#$ -N vllm_env
#$ -q Default.q
#$ -pe smp 4
#$ -l h_vmem=16G
#$ -j y
#$ -o $LLM_ROOT/logs/vllm_env.$JOB_ID.out
set -euo pipefail
cd $LLM_ROOT
export UV_CACHE_DIR=$PWD/env/uv_cache TMPDIR=$PWD/env/tmp
UV=$CLUSTER_HOME/tools/bin/uv
hostname; date
$UV pip install -p env/vllm/bin/python "vllm==0.31.0" --torch-backend=cu130
$UV pip freeze -p env/vllm/bin/python > env/vllm_requirements.lock.txt
env/vllm/bin/python -c "import vllm,torch;print(\"vllm\",vllm.__version__,\"torch\",torch.__version__,\"cuda\",torch.version.cuda)"
date; echo ALLDONE
