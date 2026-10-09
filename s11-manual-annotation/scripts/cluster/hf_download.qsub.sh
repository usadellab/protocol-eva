#!/bin/bash
#$ -N hf_dl
#$ -q Default.q
#$ -pe smp 2
#$ -l h_vmem=16G
#$ -j y
#$ -o $LLM_ROOT/logs/hf_download.$JOB_ID.out
# usage: qsub -v REPO=org/name hf_download.qsub.sh   (downloads into llm/models/<name>)
cd $LLM_ROOT
export HF_HOME=$PWD/env/hf_home TMPDIR=$PWD/env/tmp HF_XET_NUM_CONCURRENT_RANGE_GETS=4
hostname; date; echo REPO=$REPO
nice -n 19 env/dl/bin/hf download $REPO --local-dir models/$(basename $REPO) --max-workers 2
echo EXIT=$?; date; echo ALLDONE
