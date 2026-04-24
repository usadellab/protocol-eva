#!/usr/bin/env python3
"""Test updated prompt on single protocol to check datafile hallucination."""

import requests
import json
import time

# Read protocol
protocol_text = open('/Users/xr/git/protocolrender/microbe_protocols/protocol-eva/datasets/test_set_1/Bacterial_Cultivation/121743.txt').read()

# Updated prompt with datafile rule (using string concatenation to avoid f-string issues)
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
      "characteristics": []
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
      "dataFiles": ["array of data file names or empty strings"]
    }
  ]
}

CRITICAL - PARAMETER EXTRACTION RULES:
1. Extract ALL parameters mentioned: temperatures, times, concentrations, volumes, equipment settings
2. For bioinformatics protocols: extract software names, versions, thresholds

NOTE: The "dataFiles" field should only contain file names explicitly written in the text. If none are mentioned, use empty array [].

Return ONLY valid JSON, no additional text.'''

# Call LM Studio API (qwen3-235B)
url = "http://localhost:1234/v1/chat/completions"
payload = {
    "model": "qwen3-235b-a22b-instruct-2507-mlx",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.1,
    "max_tokens": 4096
}

print("Calling LM Studio API for qwen3-235B...")
print("Testing protocol 121743 with updated DATAFILES rule...")
start = time.time()
response = requests.post(url, json=payload, timeout=180)
latency = time.time() - start

if response.status_code == 200:
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    print(f"\nLatency: {latency:.1f}s")
    print(f"Raw response length: {len(content)} chars")

    # Extract JSON (handle markdown code blocks)
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

    # Find first complete JSON
    brace_count = 0
    json_end = 0
    for i, c in enumerate(content):
        if c == '{': brace_count += 1
        elif c == '}': brace_count -= 1
        if brace_count == 0 and i > 0:
            json_end = i + 1
            break

    json_str = content[:json_end]

    try:
        data = json.loads(json_str)
        print("\n✓ JSON parsed successfully")

        # Count datafiles
        total_df = 0
        named_df = []
        for p in data.get('protocols', []):
            for df in p.get('dataFiles', []):
                total_df += 1
                if df and str(df).strip():
                    named_df.append({"protocol": p.get('name'), "file": df})

        print(f"\n--- DATAFILES CHECK ---")
        print(f"Total datafiles: {total_df}")
        print(f"Named datafiles: {len(named_df)}")
        if named_df:
            print("⚠️  Hallucinated files found:")
            for n in named_df:
                print(f"  - {n['protocol']}: '{n['file']}'")
        else:
            print("✓ No hallucinated files! (empty arrays only)")

        print(f"\n--- EXTRACTION SUMMARY ---")
        print(f"Protocols extracted: {len(data.get('protocols', []))}")
        print(f"Samples extracted: {len(data.get('samples', []))}")

        # Count parameters
        total_params = 0
        for p in data.get('protocols', []):
            total_params += len(p.get('parameters', []))
        print(f"Parameters extracted: {total_params}")

    except json.JSONDecodeError as e:
        print(f"\n✗ JSON parse error: {e}")
        print(f"JSON string preview: {json_str[:500]}...")
else:
    print(f"✗ API error: {response.status_code}")
    print(response.text)