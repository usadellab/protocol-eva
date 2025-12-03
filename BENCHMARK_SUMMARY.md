# Protocol-to-ISA Benchmark Summary

**Date:** 2025-12-02
**Dataset:** BioProt (10 protocols)
**Task:** Convert free-text scientific protocols to structured ISA JSON format

---

## Complete Model Performance Overview

### Latest Run (Dec 1, 2025) - 50/50 Context Split

| Model | Size | Success Rate | Avg Latency | Schema Score | Failure Mode |
|-------|------|-------------|-------------|--------------|--------------|
| **Claude Opus 4.5** | - | **100% (10/10)** | N/A | 100% | None |
| **Qwen3-80B-4bit** | 80B | **100% (10/10)** | 30.5s | 100% | None |
| **Qwen3-30B-4bit** | 30B | 90% (9/10) | 10.8s | 100% | Malformed JSON |
| **MiniMax-M2-4bit** | 235B | 0% (0/10) | 234s | 0% | `</think>` prefix |
| **GPT-OSS-120B-8bit** | 120B | 0% (0/10) | 55.7s | 0% | CoT leakage |
| **GPT-OSS-20B-Q8** | 20B | 0% (0/10) | 76.9s | 0% | CoT leakage |

### Earlier Run (Nov 28, 2025) - 4096 max_tokens

| Model | Success Rate | Avg Latency | Notes |
|-------|-------------|-------------|-------|
| **MiniMax-M2-4bit** | 90% (9/10) | 193.3s | Better with lower token limit |
| **GPT-OSS-120B-8bit** | 50% (5/10) | 48.3s | CoT leakage on long protocols |
| **GPT-OSS-20B** | Not tested | - | - |

---

## Failure Mode Analysis

### 1. Chain-of-Thought Leakage (GPT-OSS Models)

**Symptom:** Output starts with `{analysis<|message|>` instead of JSON

**Example (GPT-OSS-120B):**
```
{analysis<|message|>We need to parse protocol, extract samples: The text mentions
environmental samples, positive control (artificial community), no-template control (NTC)...
[continues analyzing until token limit]
```

**Root Cause:** These models use special tokens for "analysis mode" that gets triggered when asked to produce structured output. The model spends all tokens on analysis, never generating the actual JSON.

**Mitigation Attempted:** `force_json=True` (prefill with `{`) - but model still outputs analysis tokens

---

### 2. Think Tag Contamination (MiniMax-M2)

**Symptom:** Output contains `</think>` tag followed by duplicate JSON

**Example (MiniMax-M2):**
```json
{"samples": [], "protocols": [] }
</think>

{
  "samples": [],
  "protocols": [
    {
      "name": "Primary PCR amplification...
```

**Root Cause:** Model outputs thinking/stub JSON, then a `</think>` tag, then real JSON. The JSON extractor only finds the first `{...}` block which is empty or incomplete.

**Interesting Finding:** With lower max_tokens (4096), MiniMax-M2 achieved 90% success. Higher token limits allow more "thinking" which causes the issue.

---

### 3. Malformed JSON (Qwen3-30B on Protocol 10051)

**Symptom:** Missing object brace in nested array

**Example:**
```json
"parameters": [
  { "name": "forward primer concentration", "value": "10", "unit": "µM" },
  "forward primer volume", "value": "0.8", "unit": "µl" },  // Missing { "name":
  { "name": "reverse primer concentration", ... }
```

**Root Cause:** Model loses track of structure during long nested output generation.

---

## Detailed Protocol Extraction Summary

### Protocol 10051: eDNA 12S Metabarcoding (Most Complex)

| Model | Status | Samples | Protocols | Parameters |
|-------|--------|---------|-----------|------------|
| Opus 4.5 | SUCCESS | 3 | 10 | 52 |
| Qwen3-80B | SUCCESS | 3 | 8 | 45 |
| Qwen3-30B | **FAILED** | - | - | - |
| MiniMax-M2 | **FAILED** | - | - | - |
| GPT-OSS-120B | **FAILED** | - | - | - |
| GPT-OSS-20B | **FAILED** | - | - | - |

**Key Parameters Extracted (Opus 4.5):**

| Category | Parameters |
|----------|------------|
| PCR Cycling | Initial denat: 95°C/5min, 40 cycles [95°C/15s, 55°C/30s, 72°C/30s], Hold 4°C |
| Reaction Mix | 20µl total: 2µl template, 10µl MasterMix, 0.8µl primers (10µM), 7.2µl water |
| Secondary PCR | 20 cycles, 57°C annealing |
| Sequencing | MiSeq v2, 2x250bp, 20% PhiX |
| Barcodes | FK: CTTGTA, MB: GCCAAT |

---

### Protocol 1007: Virus Enumeration

| Model | Status | Samples | Protocols | Parameters |
|-------|--------|---------|-----------|------------|
| Opus 4.5 | SUCCESS | 1 | 8 | 24 |
| Qwen3-80B | SUCCESS | 1 | 2 | 12 |
| Qwen3-30B | SUCCESS | 1 | 2 | 12 |
| MiniMax-M2 (Nov) | SUCCESS | 1 | 2 | ~10 |
| GPT-OSS-120B (Nov) | SUCCESS | 1 | ~5 | ~15 |

**Key Parameters:**
- Iron Chloride: 1 µL
- Centrifugation: 14,000 RCF × 20 min
- SYBR Gold incubation: 15 min (dark)
- Microscopy: 495nm excitation, 1000X mag

---

### Protocol 10157: Flow Cytometry

| Model | Status | Samples | Protocols | Parameters |
|-------|--------|---------|-----------|------------|
| Opus 4.5 | SUCCESS | 2 | 8 | 22 |
| Qwen3-80B | SUCCESS | 2 | 7 | 20 |
| Qwen3-30B | SUCCESS | 2 | 7 | 20 |

**Key Parameters:**
- Antibiotic: 50 µg/mL chloramphenicol
- IPTG: 0-1 mM range
- aTc: 0-200 ng/mL range
- FACS: 488nm laser, FL-1 515-545nm, FL-2 585-610nm
- Events: 50,000 per sample

---

### Protocol 10614: E. coli Transformation

| Model | Status | Samples | Protocols | Parameters |
|-------|--------|---------|-----------|------------|
| Opus 4.5 | SUCCESS | 2 | 11 | 30 |
| Qwen3-80B | SUCCESS | 2 | 9 | 25 |
| Qwen3-30B | SUCCESS | 2 | 9 | 25 |

**Key Parameters:**
- Heat shock: 42°C × 30 sec (exact)
- Ice incubation: 30 min
- Outgrowth: 37°C × 60 min @ 250 rpm
- Plating: 50-100 µL per plate

---

## Aggregate Extraction Statistics

### Total Extraction Counts (Successful Models Only)

| Metric | Opus 4.5 | Qwen3-80B | Qwen3-30B* |
|--------|----------|-----------|------------|
| **Total Samples** | 19 | 19 | 16 |
| **Total Protocols** | 73 | 57 | 49 |
| **Total Parameters** | 255 | ~220 | ~180 |
| **Protocols/Protocol** | 7.3 avg | 5.7 avg | 5.4 avg |
| **Params/Protocol** | 3.5 avg | 3.9 avg | 3.7 avg |

*Excludes failed protocol 10051

---

### Parameter Type Distribution (Opus 4.5)

| Category | Count | Examples |
|----------|-------|----------|
| **Volume** | 62 | Reaction volume, sample volume, buffer |
| **Temperature** | 41 | Cycling, incubation, storage |
| **Time/Duration** | 47 | Minutes, seconds, overnight |
| **Concentration** | 26 | µM, mM, µg/mL, ng/mL |
| **Speed/Rate** | 16 | RCF, rpm, events/s |
| **Wavelength** | 11 | Excitation, emission, OD |
| **Count/Cycles** | 13 | PCR cycles, events, replicates |
| **Equipment** | 31 | Instruments, kits, reagents |
| **Dimensions** | 8 | Tank size, arena dimensions |

---

### Unit Types Extracted

```
Volume:        µL, mL, L
Mass:          g, µg, ng, pg
Concentration: µM, mM, ng/mL, µg/mL, U/µL, mg/mL
Temperature:   °C
Time:          seconds, minutes, hours, overnight
Speed:         rpm, RCF, × g, events/second
Wavelength:    nm
Dimensions:    cm, mm
Magnification: X
Percentage:    %
Dilution:      fold, ratio (e.g., 1:10)
```

---

## Model-Specific Recommendations

### Qwen3 Models (Best Local Option)
- **80B**: Recommended for production - 100% success, good parameter extraction
- **30B**: Good for shorter protocols, faster but may fail on complex nested output

### GPT-OSS Models (Not Recommended)
- Critical issue with chain-of-thought leakage
- Need model-specific prompting to suppress analysis mode
- Or use with very low max_tokens to force immediate JSON output

### MiniMax-M2 (Conditional)
- Works better with lower max_tokens (4096)
- `</think>` tag extraction logic needed in post-processing
- Very slow (193-234s per protocol)

### Claude Opus 4.5 (Best Overall)
- Perfect success rate
- Most granular parameter extraction
- Handles complex nested structures reliably
- Best for production/reference benchmarks

---

## Ontology Mapping Gap

**Current State:** Raw values extracted, no ontology mapping

**Recommended Mappings:**

| Category | Ontology | Example |
|----------|----------|---------|
| Organisms | NCBI Taxonomy | E. coli → NCBITaxon:562 |
| Instruments | OBI | Flow cytometer → OBI:0400044 |
| Units | UO | µL → UO:0000101 |
| Chemicals | ChEBI | IPTG → CHEBI:61448 |
| Protocols | OBI/EXACT | PCR → OBI:0000415 |

---

## Benchmark Configuration Reference

| Parameter | Nov 28 Run | Dec 1 Run |
|-----------|------------|-----------|
| max_tokens | 4096 | 50% of context |
| context_window | Model default | Model spec |
| top_p | 0.9 | 0.9 |
| temperature | 0.1 | 0.1 |
| json_token_bias | Not used | 2.0 (7 tokens) |
| force_json | No | Yes (except GPT-OSS) |

---

## Key Findings

1. **Context allocation matters**: 50/50 input/output split works for Qwen but breaks MiniMax
2. **Model-specific failure modes**: GPT-OSS has unfixable CoT leakage with current approach
3. **Protocol complexity**: 10051 (eDNA NGS) is the hardest - only Qwen3-80B and Opus succeed
4. **Parameter granularity**: Opus extracts ~15% more parameters than Qwen models
5. **Speed vs accuracy tradeoff**: Qwen3-30B (10.8s) vs Qwen3-80B (30.5s) - 3x slower for 10% more reliability
