# Protocol-to-ISA Conversion Evaluation Report

**Generated:** 2025-12-02
**Dataset:** BioProt (10 protocols)
**Models Evaluated:** 9 configurations across 5 model families

---

## Executive Summary

| Rank | Model | Success Rate | Parameters Extracted | Params/Step | Avg Latency |
|------|-------|-------------|---------------------|-------------|-------------|
| 1 | **Opus 4.5** | 100% (10/10) | 240 | 3.2 | N/A (API) |
| 2 | **Qwen3-80B** | 100% (10/10) | 215 | 2.5 | 30.5s |
| 3 | **Qwen3-235B** | 100% (10/10) | 210 | 2.7 | 117.6s |
| 4 | **MiniMax-M2 (Nov)** | 90% (9/10) | 196 | 2.2 | 193.3s |
| 5 | **Qwen3-30B** | 90% (9/10) | 116 | 2.4 | 10.8s |
| 6 | **GPT-OSS-120B (Nov)** | 50% (5/10) | 97 | 2.1 | 48.3s |
| 7 | MiniMax-M2 (Dec) | 0% | 0 | - | - |
| 8 | GPT-OSS-120B (Dec) | 0% | 0 | - | - |
| 9 | GPT-OSS-20B (Dec) | 0% | 0 | - | - |

**Key Findings:**
- Opus 4.5 extracts 11.6% more parameters than Qwen3-80B with higher granularity (3.2 vs 2.5 params/step)
- Qwen3-235B (MoE: 235B total, 22B active) achieves 100% success but extracts fewer parameters than 80B variant
- Qwen3-235B extracts significantly more samples (41) than other models - treats reagents as samples

---

## Per-Protocol Success Matrix

| Protocol | Title | Opus | Q235B | Q80B | Q30B | MM-Nov | GPT-Nov |
|----------|-------|:----:|:-----:|:----:|:----:|:------:|:-------:|
| 10051 | eDNA 12S Metabarcoding | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ |
| 1007 | Virus Enumeration | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 10157 | Flow Cytometry | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 10176 | Fish Personality | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 10238 | NAQ Assay | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| 10256 | Gel Electrophoresis | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 10279 | Digital PCR | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| 10606 | Mealybug Sex Ratio | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| 10614 | E. coli Transformation | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 10626 | Cell Isolation | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |

**Hardest Protocol:** 10051 (eDNA NGS) - only Opus 4.5, Qwen3-235B, Qwen3-80B, and MiniMax-M2 (Nov) succeed.

---

## Extraction Quality Comparison

### Protocol 10051: eDNA 12S Metabarcoding (Most Complex)

| Metric | Opus 4.5 | Qwen3-235B | Qwen3-80B | MiniMax-M2 |
|--------|----------|------------|-----------|------------|
| Samples | 3 | 3 | 3 | 3 |
| Protocol Steps | 10 | 7 | 9 | 8 |
| Parameters | 48 | 49 | 51 | 50 |
| PCR Cycling Params | Complete | Complete | Complete | Complete |
| Sequencing Params | Detailed | Basic | Basic | Basic |

**Samples Extracted:**
- gDNA extract template / Environmental sample
- Positive control / Artificial community
- No template control (NTC)

**Key Parameters (all models captured):**
- Reaction volume: 20 µL
- Template volume: 2 µL (1:10 dilution)
- Primer volume: 0.8 µL each (10 µM)
- MasterMix: 10 µL (2X Hotstar)
- PCR Cycling: 95°C/5min → 40× [95°C/15s, 55°C/30s, 72°C/30s] → 4°C

### Aggregate Extraction by Model

| Model | Samples | Protocol Steps | Parameters | Params/Step | Avg Latency |
|-------|---------|----------------|------------|-------------|-------------|
| Opus 4.5 | 19 | 74 | 240 | 3.2 | N/A (API) |
| Qwen3-235B | 41 | 77 | 210 | 2.7 | 117.6s |
| Qwen3-80B | 20 | 87 | 215 | 2.5 | 30.5s |
| Qwen3-30B | 13 | 49 | 116 | 2.4 | 10.8s |
| MiniMax-M2 (Nov) | 31 | 89 | 196 | 2.2 | 193.3s |
| GPT-OSS-120B (Nov) | 12 | 46 | 97 | 2.1 | 48.3s |

**Observations:**
1. **Opus 4.5** has highest params/step ratio (3.2) - most granular extraction
2. **Qwen3-235B** extracts the most samples (41) - includes reagents/materials as samples
3. **Qwen3-80B** extracts more protocol steps (87) but less detailed parameters
4. **MiniMax-M2** also extracts many samples (31) - similar to 235B behavior
5. **Qwen3-30B** loses significant detail on complex protocols
6. **Qwen3-235B** is 4x slower than 80B (117.6s vs 30.5s) with similar parameter extraction

---

## Parameter Type Distribution (Opus 4.5 Reference)

| Category | Count | % of Total |
|----------|-------|-----------|
| Other/Equipment | 97 | 40.4% |
| Volume | 45 | 18.8% |
| Time | 40 | 16.7% |
| Temperature | 30 | 12.5% |
| Concentration | 10 | 4.2% |
| Speed/Rate | 9 | 3.8% |
| Count/Cycles | 5 | 2.1% |
| Wavelength | 4 | 1.7% |

### Unit Types Extracted

| Unit | Count | Category |
|------|-------|----------|
| µL / µl | 40 | Volume |
| °C | 27 | Temperature |
| minutes | 27 | Time |
| seconds | 10 | Time |
| nm | 5 | Wavelength |
| x g | 5 | Centrifugation |
| mL | 5 | Volume |
| µM / mM | 6 | Concentration |
| rpm | 2 | Speed |

---

## Head-to-Head: Opus 4.5 vs Qwen3-80B

| Protocol | Opus Params | Qwen Params | Difference |
|----------|-------------|-------------|------------|
| 10051 (eDNA) | 48 | 51 | -3 |
| 10238 (NAQ) | 30 | 24 | +6 |
| 10614 (Transform) | 25 | 29 | -4 |
| 10626 (Cell Iso) | 25 | 15 | +10 |
| 10279 (dPCR) | 18 | 12 | +6 |
| 10606 (Mealybug) | 16 | 12 | +4 |
| **TOTAL** | **240** | **215** | **+25** |

**Analysis:**
- Opus 4.5 extracts more parameters on 7/10 protocols
- Qwen3-80B wins on 3 protocols (10051, 10157, 10614)
- Opus 4.5 has more granular step decomposition (fewer steps, more params per step)

---

## Failure Analysis

### Failed Protocols by Model

| Model | Failed | Failure Mode |
|-------|--------|--------------|
| Qwen3-30B | 10051 | Malformed JSON - dropped `{` in nested array |
| MiniMax-M2 (Nov) | 10238 | Token limit (4096) hit |
| GPT-OSS-120B (Nov) | 10051, 10238, 10279, 10606, 10626 | Chain-of-thought leakage |
| MiniMax-M2 (Dec) | ALL | `</think>` tag contamination |
| GPT-OSS (Dec) | ALL | Chain-of-thought leakage |

### December Run Failures

The Dec 1 run with higher token limits (50/50 context split) caused:
1. **MiniMax-M2**: Model outputs `{stub}</think>{real JSON}` - extractor found empty stub
2. **GPT-OSS**: Model outputs `{analysis<|message|>...` - spends all tokens on analysis

**Fix Applied:** Updated `extract_json()` to check JSON both before and after `</think>` tag.

---

## Recommendations

### For Production Use

| Scenario | Recommended Model | Reason |
|----------|-------------------|--------|
| Highest accuracy | Opus 4.5 | Most granular parameters (240, 3.2/step) |
| Local inference | Qwen3-80B | 100% success, best speed/quality tradeoff |
| Sample-centric | Qwen3-235B | 100% success, extracts most samples (41) |
| Fast processing | Qwen3-30B | 3x faster, 90% success |
| Avoid | GPT-OSS, MiniMax-M2 | Unreliable output format |

**Note:** Qwen3-235B (MoE architecture with 22B active parameters) is 4x slower than Qwen3-80B but extracts more samples. Better suited for protocols where material/reagent enumeration is important.

### For Improvement

1. **Ontology Mapping**: Add post-processing to map extracted terms to:
   - NCBI Taxonomy (organisms)
   - Units Ontology (units)
   - ChEBI (chemicals)
   - OBI (instruments, protocols)

2. **JSON Repair**: Implement bracket-balancing repair for Qwen3-30B failures

3. **Chunking**: Split long protocols into sections for more reliable extraction

4. **Validation**: Add semantic validation against ISA-Tab schema

---

## Appendix: Raw Data Files

| File | Description |
|------|-------------|
| `opus45_results.json` | Claude Opus 4.5 benchmark results |
| `qwen3_235b_results.json` | Qwen3-235B (MoE 22B active) benchmark results |
| `qwen3_80b_results.json` | Qwen3-80B benchmark results |
| `qwen3_30b_results.json` | Qwen3-30B benchmark results |
| `minimax_m2_results.json` | MiniMax-M2 (Dec) results |
| `gpt_oss_120b_results.json` | GPT-OSS-120B (Dec) results |
| `../results/benchmark_Qwen3-235B-A22B-4bit_*.json` | Qwen3-235B Dec 2 benchmark |
| `../automated_test/*.json` | November 28 benchmark results |
