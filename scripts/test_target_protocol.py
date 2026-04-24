#!/usr/bin/env python3
"""Test updated prompt on target_protocol examples."""

import requests
import json
import time
import os

TARGET_DIR = "/Users/xr/git/protocolrender/microbe_protocols/protocol-eva/datasets/target_protocol"

def run_extraction(protocol_file):
    protocol_text = open(protocol_file).read()

    prompt = '''You are a scientific data extraction assistant. Analyze this experimental protocol and extract structured information.

Protocol Text:
"""
''' + protocol_text + '''
"""

Extract and return ONLY a JSON object (no markdown, no explanation) with this structure:
{
  "samples": [
    {
      "name": "Sample identifier or name",
      "organism": "Organism or source",
      "characteristics": [
        {
          "category": "Characteristic category",
          "value": "Characteristic value",
          "unit": "Unit if applicable"
        }
      ]
    }
  ],
  "protocols": [
    {
      "name": "Protocol step name",
      "description": "Brief description",
      "inputs": ["array of input names"],
      "parameters": [
        {
          "name": "parameter name",
          "value": "actual value or empty string",
          "unit": "unit or empty string",
          "description": "description"
        }
      ],
      "outputs": ["array of output names"],
      "dataFiles": []
    }
  ]
}

CRITICAL - PARAMETER EXTRACTION RULES:
1. Extract ALL parameters mentioned: temperatures, times, concentrations, volumes, equipment settings
2. For bioinformatics protocols: extract software names, versions, command-line arguments, thresholds
3. If a parameter value is mentioned, include it in the description field
4. Even if parameters array would be empty, try to infer 2-3 key parameters from context

IMPORTANT - SAMPLE EXTRACTION:
1. Extract sample information: names, organism, characteristics (age, tissue type, genotype, treatment)
2. If no specific samples mentioned, create generic samples (e.g., "Sample_1", "Sample_2")

IMPORTANT - PROTOCOL LINKING:
1. Link protocols sequentially - OUTPUT of one protocol MUST EXACTLY MATCH INPUT of next
2. Use clear names (e.g., "Sample Preparation", "Measurement", "Analysis")
3. First protocol inputs should reference sample names from samples array

Return ONLY valid JSON, no additional text.'''

    url = "http://localhost:1234/v1/chat/completions"
    payload = {
        "model": "qwen3-235b-a22b-instruct-2507-mlx",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 4096
    }

    start = time.time()
    response = requests.post(url, json=payload, timeout=180)
    latency = time.time() - start

    if response.status_code == 200:
        content = response.json()["choices"][0]["message"]["content"]

        if '```json' in content:
            start_idx = content.find('```json')
            json_start = content.find('{', start_idx)
            content = content[json_start:]
            if '```' in content:
                content = content[:content.find('```')]
        elif '```' in content:
            start_idx = content.find('```')
            json_start = content.find('{', start_idx)
            content = content[json_start:]
            if '```' in content:
                content = content[:content.find('```')]

        brace_count = 0
        json_end = 0
        for i, c in enumerate(content):
            if c == '{': brace_count += 1
            elif c == '}': brace_count -= 1
            if brace_count == 0 and i > 0:
                json_end = i + 1
                break

        data = json.loads(content[:json_end])
        return data, latency
    else:
        return None, latency


print("=== Testing target_protocol with updated prompt ===\n")

results = []
for filename in sorted(os.listdir(TARGET_DIR)):
    if not filename.endswith('.txt'):
        continue

    filepath = os.path.join(TARGET_DIR, filename)
    data, latency = run_extraction(filepath)

    if data:
        chars = len(data['samples'][0].get('characteristics', []))
        params = sum(len(p.get('parameters', [])) for p in data['protocols'])
        named_dfs = [df for p in data['protocols'] for df in p.get('dataFiles', []) if df]

        results.append({
            'file': filename,
            'latency': latency,
            'samples': len(data['samples']),
            'chars': chars,
            'protocols': len(data['protocols']),
            'params': params,
            'datafiles': len(named_dfs),
            'named_files': named_dfs
        })

        print(f"✓ {filename}")
        print(f"  Latency: {latency:.1f}s")
        print(f"  Samples: {len(data['samples'])}, Characteristics: {chars}")
        print(f"  Protocols: {len(data['protocols'])}, Parameters: {params}")
        print(f"  Named DataFiles: {len(named_dfs)}")
        if named_dfs:
            print(f"  ⚠️  Files: {named_dfs}")
        print()

print("=== SUMMARY ===")
print(f"| Experiment | Latency | Samples | Characteristics | Protocols | Parameters | Named DataFiles |")
print(f"|------------|---------|---------|-----------------|-----------|------------|-----------------|")
for r in results:
    status = "✓" if r['datafiles'] == 0 else "⚠️"
    print(f"| {r['file'][:35]} | {r['latency']:.1f}s | {r['samples']} | {r['chars']} | {r['protocols']} | {r['params']} | {r['datafiles']} {status} |")

total_named = sum(r['datafiles'] for r in results)
print(f"\nTotal named DataFiles across all experiments: {total_named}")
if total_named == 0:
    print("✓ No hallucinated files - all dataFiles arrays empty")
else:
    print(f"⚠️  {total_named} potentially hallucinated files found")