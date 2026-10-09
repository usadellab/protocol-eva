#!/bin/bash
#$ -S /bin/bash
#$ -N llm_client
#$ -j y
#$ -o $LLM_ROOT/logs/client_$JOB_ID.out
#$ -q Default.q
#$ -l h_vmem=4G
# CPU job: sends the prepared prompts to the vLLM server(s) given in URLS (space separated base URLs, IPs because compute nodes cannot resolve host names), THREADS streams each. No project data leaves the cluster.
hostname; date; echo "URLS=$URLS THREADS=$THREADS"
/usr/bin/python3 $LLM_ROOT/data/client2.py $LLM_ROOT/data/requests_$SET $LLM_ROOT/data/responses_$SET ${THREADS:-4} $URLS
