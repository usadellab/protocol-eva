# Protocol-to-ISA Benchmark Framework - Project Documentation

## Overview

This project benchmarks local LLM models for converting free-text microbiology protocols from protocols.io into structured ISA-JSON format.

---

## 0. Target Protocols (Reference Examples)

**Purpose**: Real-world elabFTW experiment records used as selection criteria for finding similar protocols.

**Location**: `target_protocol/`

**Source**: elabFTW exports (HTML → converted to TXT)

### Protocol Summary

| Experiment | Category | Size | Purpose |
|------------|----------|------|---------|
| Experiment-1 | Bacterial_Cultivation | 1,589 chars | E. coli K-12 growth monitoring |
| Experiment-2 | DNA_Extraction | 1,132 chars | Genomic DNA extraction with kit |
| Experiment-3 | Library_Preparation | 1,007 chars | FFPE repair, A-tailing, adapter ligation |
| Experiment-4 | Sequencing | **610 chars** | Illumina NovaSeq run (SMALLEST) |
| Experiment-5 | Bioinformatics | 1,045 chars | Data analysis pipeline |

### Size Threshold Determination

**Minimum Threshold**: **610 characters** (Experiment-4: Sequencing Run)

This became the lower bound for filtering protocols.io collection:
- Below 610 chars → discarded (too brief)
- Above 2000 chars → discarded (too verbose)
- Range: **600-2000 chars** selected

### Target Protocol Content Examples

#### Experiment 1: Bacterial Cultivation (1,589 chars)
```
Title: Experiment 1: Bacterial Cultivation

Bacterial cultivation of E. coli Strain K-12 (n=10)

Goal:
To cultivate Escherichia coli K-12 under controlled conditions...

Procedure:
Strains: E. coli K-12
Medium: LB broth, 10 mL per culture
Conditions: 37 °C, 180 rpm, 16 h
Inoculation: 1:100 dilution from overnight culture (OD600 = 2.5)
Sampling: OD600 measurements taken every hour for 8 hours.

[TABLE] - Growth curve data for 10 samples over 8 hours

Notes: Cultures harvested at 6 hours (5,000 g, 10 min, 4 °C)
```

#### Experiment 4: Sequencing Run (610 chars - THRESHOLD)
```
Title: Experiment 4: Sequencing Run

Illumina NovaSeq 6000 sequencing

Goal:
Sequencing of samples from Assay - Experiment 3

Methods:
Sequencing Platform: Illumina NovaSeq 6000
Flow Cell: SP Flow Cell (Lot No. NV-FC-20250622A)
Chemistry: NovaSeq 6000 S1 Reagent Kit v1.5 (300 cycles)
Loading Concentration: 200 pM
Read Length: 2x150 bp paired-end reads

Results:
Yield: Approximately 10-15 Gb per sample.
Q30 Score: >90% across all samples.
Data Location: FASTQ files stored on institutional server
```

### Why These Were Used as Search Criteria

1. **Real experimental data** - Not synthetic or test protocols
2. **Complete workflow coverage** - Cultivation → Extraction → Library → Sequencing → Analysis
3. **Typical microbiology format** - Goal, Procedure, Results structure
4. **Size range representative** - 610-1589 chars matches realistic experiment notes
5. **Contains tables** - Experiments 1 and 2 have measurement tables (tests table extraction)

---

## 1. Data Collection

### Source: protocols.io API

**Collection Date**: January 2026

**Method**:
- Downloaded via protocols.io API export
- Raw JSON files stored in `rawdata/protocols_io_raw/`
- Total raw protocols: 25,136 JSON files

**Raw Data Structure**:
```json
{
  "id": "PROTO-MB-XXX",
  "name": "Protocol title",
  "protocol_text": "Introduction/summary text",
  "original_steps": [
    {
      "step": "{...Draft.js JSON...}",
      "section": "<p>Section name</p>",
      "duration": 60,
      ...
    }
  ],
  ...
}
```

**Draft.js Format**: Step content embedded in Draft.js editor format:
```json
{
  "blocks": [{"text": "Step description...", "type": "unstyled"}],
  "entityMap": {
    "0": {"type": "tables", "data": {...}},
    "1": {"type": "reagents", "data": {...}}
  }
}
```

---

## 2. Data Cleaning

### Parser Development

**Tool**: `protocol_parser.py`

**Key Functions**:
- `extract_text_from_draftjs()` - Parse Draft.js blocks to plain text
- `extract_table_data()` - Extract tables from entityMap
- `extract_reagents()` - Extract reagent information
- `parse_section_html()` - Clean HTML section names

**Output Formats**:
| File | Content |
|------|---------|
| `*_complete.txt` | Full protocol text (LLM input) |
| `*_structured.json` | Sections, tables, reagents |
| `*_raw_steps.json` | Original Draft.js preserved |
| `*_tables.json` | Extracted tables only |
| `*_reagents.json` | Extracted reagents only |

### Processing Results

- **Input**: 100 protocol JSON files (`input/`)
- **Output**: 100 complete text files (`example_protocol/`)
  - 17 with tables
  - 15 with reagents

**Example Output**:
```
Title: PrimalSeq: Generation of tiled virus amplicons...

=== PROTOCOL STEPS ===

## Step 1: Generation of barcode spike-ins
Step description text...

[TABLE]
Column1 | Column2 | Column3
...

=== MATERIALS ===
- Q5 High-Fidelity 2X Master Mix (Thermo Fisher) [SKU: 4444556]
```

---

## 3. Data Selection

### Size Criteria

**Target**: Protocols similar to elabFTW experiments (600-2000 characters)

**Threshold**: 610 chars (smallest elabFTW experiment: Experiment-4-Sequencing)

### Category Classification

**Categories** (7 total):
1. Bacterial_Cultivation
2. Bioinformatics
3. DNA_Extraction
4. PCR
5. RNA_Extraction
6. Sequencing
7. Transformation

### Selection Process

1. Parse all 25,136 raw protocols → text
2. Filter by length: 600-2000 chars
3. Classify by keywords/title analysis
4. Result: **3,040 protocols** in `microbiology_protocols/`

**Distribution**:
| Category | Count |
|----------|-------|
| Bacterial_Cultivation | ~430 |
| Bioinformatics | ~430 |
| DNA_Extraction | ~430 |
| PCR | ~430 |
| RNA_Extraction | ~430 |
| Sequencing | ~430 |
| Transformation | ~430 |

### Test Set Creation

**Method**: Random selection, 10 per category

**Sets Created**: 5 test sets (`test_set_1/` through `test_set_5/`)
- Each: 70 protocols (10 × 7 categories)
- Structure: Category folders + `all_protocols/` flat folder

---

## 4. Model Selection

### Why Local Models (Not API)?

**Critical Reason: Reproducibility**

| Issue | Closed API Models | Local Models |
|-------|-------------------|--------------|
| **Discontinuation Risk** | HIGH - models deprecated frequently | LOW - persist on disk |
| **Version Control** | IMPOSSIBLE - forced updates | FULL CONTROL - pin versions |
| **Rate Limits** | STRICT - costs per request | NONE - unlimited |
| **Speed** | LIMITED by network/API | LOCAL - GPU speed only |
| **Privacy** | Data sent to cloud | STAYS LOCAL |
| **Cost** | Recurring API fees | ONE-TIME hardware |

**Historical Examples**:
- GPT-3.5 deprecated → broke reproducibility
- Claude 2 → Claude 3 forced migration
- Model pricing changes unpredictably

**Conclusion**: For scientific benchmarking reproducibility, **LOCAL models are mandatory**.

### Why LM Studio?

**Benefits**:
- Unified interface for multiple model formats (MLX, GGUF)
- OpenAI-compatible API at `localhost:1234`
- No coding overhead - simple HTTP calls
- Hot-swap models without code changes
- Built-in JSON mode support

### LM Studio Settings & Configuration

**API Endpoint**: `http://localhost:1234/v1/chat/completions`

**OpenAI-Compatible Parameters**:
```json
{
  "model": "model_id",
  "messages": [{"role": "user", "content": "prompt"}],
  "max_tokens": 4096,
  "temperature": 0.1,
  "top_p": 0.9
}
```

**Temperature Settings**:
| Parameter | Value | Reason |
|-----------|-------|--------|
| `temperature` | **0.1** | Low for deterministic JSON extraction |
| `top_p` | 0.9 | Standard nucleus sampling |
| `max_tokens` | 4096-8192 | Depends on model output capacity |

**Critical Settings per Model**:

| Model Key | force_json_prefix | json_handler | max_tokens | Notes |
|-----------|-------------------|--------------|------------|-------|
| `gpt-oss-20b` | **FALSE** | `gpt_oss` | 8192 | NO `{` prefix - triggers CoT |
| `gpt-oss-120b` | **FALSE** | `gpt_oss` | 8192 | NO `{` prefix |
| `qwen3-235b-mlx` | TRUE | `qwen` | 4096 | Prefix `{` required |
| `qwen3.5-0.8b-optiq` | TRUE | `qwen` | 4096 | Prefix `{` required |
| `gemma-4-31b` | TRUE | `standard` | 4096 | Prefix `{` required |

**Why `force_json_prefix` Matters**:
```python
# For GPT-OSS models (FALSE):
prompt = "Extract JSON..."  # NO prefix added
# GPT-OSS uses <|channel|>final<|message|> markers

# For Qwen/Gemma models (TRUE):
prompt = "Extract JSON...\n{"  # ADD prefix
# Forces model to start output with JSON object
```

**GPT-OSS Chain-of-Thought Issue**:
- Adding `{` prefix to GPT-OSS triggers extended reasoning mode
- This causes slower response and potential JSON truncation
- Solution: Extract JSON from `<|channel|>final<|message|>` marker

**LM Studio GUI Settings** (for loading models):
- Context length: 131072 (max)
- GPU layers: All available
- Thread count: Auto
- Flash attention: Enabled

**Model Storage Location**:
```
~/.lmstudio/models/
├── lmstudio-community/
│   ├── gpt-oss-120b-mlx-8bit/
│   └── Qwen3-235B-A22B-Instruct-2507-MLX-4bit/
├── mlx-community/
│   └── gpt-oss-20b-MXFP4-Q8/
└── .../
```

### Model Criteria Analysis

**Hypothesis**: "Large coding-focused models best for JSON extraction"

**Reality Check**: FAILED

| Model | Size | Focus | Success Rate | Issue |
|-------|------|-------|--------------|-------|
| Qwen3.5-27B | 27B | General | 14.3% | Too slow, truncated JSON |
| GPT-OSS-120B | 120B | Coding | 85.7% | Good but slow |
| GPT-OSS-20B | 20B | Coding | **100%** | FAST + reliable |
| Qwen3-235B | 235B | General | **100%** | Highest quality |

**Key Insight**:
- **Larger ≠ Better** - 27B failed, 235B succeeded
- **Coding focus ≠ Best for structured extraction**
- **Success rate > Model size**

### Selection Results

**Models Tested**:
| Model | Type | Chosen | Reason |
|-------|------|--------|--------|
| gemma-4-31b | MLX | Yes | Good quality, moderate speed |
| qwen3.5-27b | GGUF | **REMOVED** | Timeout, truncated output |
| qwen3.5-0.8b-optiq | GGUF | Yes | Speed test, fails ISA format |
| gpt-oss-120b | MLX | Yes | Quality test |
| gpt-oss-20b | MLX | Yes | **WINNER** - speed + reliability |
| qwen3-235b-mlx | MLX | Yes | **WINNER** - quality + reliability |

**Removed Models**:
- `qwen3.5-27b` - ~180s latency, JSON truncation, 14.3% success

---

## 5. Test Script Preparation

### Script: `lmstudio_model_benchmark.py`

**Architecture**:
```python
MODEL_CONFIGS = {
    "gpt-oss-20b": {
        "model_id": "openai/gpt-oss-20b",
        "force_json_prefix": False,  # Critical for GPT-OSS
        "json_handler": "gpt_oss",
    },
    "qwen3-235b-mlx": {
        "force_json_prefix": True,   # Prefix { for JSON
        "json_handler": "qwen",
    },
    ...
}
```

### Model-Specific JSON Handling

**Critical Discovery**: Different models need different JSON extraction

| Handler | Models | Method |
|---------|--------|--------|
| `standard` | Gemma | Brace-counting JSON extraction |
| `qwen` | Qwen | Handle markdown code blocks, preamble |
| `gpt_oss` | GPT-OSS | Extract from `<|channel|>final<|message|>` markers |

**GPT-OSS Special Case**:
```python
# DO NOT add "{" prefix for GPT-OSS
# Adding prefix triggers chain-of-thought mode!
if config["force_json_prefix"]:
    prompt = prompt + "\n{"  # Only for Qwen/Gemma
else:
    prompt = prompt  # NO prefix for GPT-OSS
```

### Prompt Template

**ISA Extraction Prompt**: Based on elab2arc ISA schema

```python
ISA_PROMPT_TEMPLATE = '''
Extract JSON with structure:
{
  "samples": [{name, organism, characteristics[]}],
  "protocols": [{name, description, inputs[], parameters[], outputs[], dataFiles[]}]
}

CRITICAL RULES:
1. Link protocols sequentially (output of step N = input of step N+1)
2. Extract ALL parameters (temperature, time, concentration)
3. Create samples if not mentioned
'''
```

### Incremental Saving

**State Management**: Resume interrupted runs

**Structure**:
```
lmstudio_results/           # Output directory
├── <model_key>/            # Per-model folder
│   ├── <protocol_id>.json  # Individual results
│   └── summary.json        # Final summary
└── BENCHMARK_SUMMARY.md    # Human-readable

.benchmark_state/           # Hidden state
└── <model_key>/progress.json  # Resume tracking
```

---

## 6. Running Benchmarks

### Execution Process

**One-at-a-time**: Models must be loaded in LM Studio sequentially

```bash
# Load model in LM Studio GUI first
python3 lmstudio_model_benchmark.py --model-key gpt-oss-20b
python3 lmstudio_model_benchmark.py --model-key qwen3-235b-mlx
...
```

**Resume Capability**:
```bash
# If interrupted, run same command - skips completed
python3 lmstudio_model_benchmark.py --model-key gemma-4-31b
# Output: "[1/7] 121743: SKIPPED (already completed)"
```

### Success Criteria

| Level | Definition |
|-------|------------|
| **API Success** | HTTP 200, response received |
| **JSON Success** | Valid JSON parsed |
| **ISA Success** | Correct `{samples, protocols}` structure |

---

## 7. Statistical Analysis

### 7.1 Collection Quantity Metrics

**Primary Metrics** (count-based):

| Metric | Description | Weight |
|--------|-------------|--------|
| `step_preservation` | Protocols extracted / Original steps | 40% |
| `parameter_extraction` | Parameters extracted / Original numbers | 25% |
| `component_extraction` | Components extracted / Original materials | 20% |
| `sequence_order` | Sequential linking preserved | 15% |

**Calculation**:
```python
overall = (step_preservation * 0.40
         + parameter_extraction * 0.25
         + component_extraction * 0.20
         + sequence_order * 0.15)
```

### 7.2 Correctness vs Hallucination Metrics

**Critical Discovery**: More extraction ≠ Better quality

**Hallucination Types Identified**:

| Type | Example | Model(s) Affected |
|------|---------|-------------------|
| **DataFile Hallucination** | Inventing `Sample_1.fastq.gz` | GPT-OSS-120B, Gemma-4-31B |
| **Structure Violation** | Single protocol object instead of array | Qwen3.5-0.8B |
| **Truncation** | JSON cut mid-generation | Qwen3.5-27B |

**DataFile Hallucination Analysis**:
```
Model            | Total DF | Empty | Real | Hallucinated | % Real Hallucinated
-----------------|----------|-------|------|--------------|--------------------
GPT-OSS-120B     | 70       | 58    | 12   | 12 (100%)    | ALL invented names
Gemma-4-31B      | 7        | 0     | 7    | 7 (100%)     | ALL invented
Qwen3-235B-MLX   | 3        | 0     | 3    | 3 (100%)     | ALL invented
GPT-OSS-20B      | 1        | 0     | 1    | 1 (100%)     | ALL invented
```

**Key Insight**: Empty `[]` is MORE ACCURATE than invented file names.

**Corrected Quality Metric**:
```
quality = extraction_score - hallucination_penalty
```

Where:
- `extraction_score` = correctly mentioned items
- `hallucination_penalty` = invented items × 2

### 7.3 Detailed Output Analysis

**Per-Protocol Metrics**:

| Metric | GPT-OSS-20B | Qwen3-235B | GPT-OSS-120B | Gemma-4-31B |
|--------|-------------|------------|--------------|-------------|
| Avg Samples | 2.4 | 1.4 | 2.2 | 2.4 |
| Chars/Sample | 0.8 | 1.5 | 1.7 | 1.0 |
| Avg Protocols | 5.3 | 6.0 | 11.2 | 4.8 |
| Params/Protocol | 1.9 | **2.2** | 1.8 | 1.8 |

**Interpretation**:
- GPT-OSS-120B: Most granular (11.2 protocols) but hallucinates files
- Qwen3-235B: Best parameter density (2.2/protocol)
- GPT-OSS-20B: Balanced extraction, minimal hallucination

### 7.4 Timing Analysis

**Latency Comparison**:

| Model | Avg Latency | Range | Success |
|-------|-------------|-------|---------|
| GPT-OSS-20B | **8.2s** | 3-13s | 100% |
| Qwen3.5-0.8B | 3.5s | 2-25s | 14.3%* |
| GPT-OSS-120B | 32.9s | 22-67s | 85.7% |
| Qwen3-235B | 46.1s | 29-65s | 100% |
| Gemma-4-31B | 105.5s | 70-168s | 71.4% |
| Qwen3.5-27B | ~180s | - | REMOVED |

*Wrong structure, not ISA format

**Speed-Quality Trade-off**:
```
GPT-OSS-20B: 8s latency × 100% success = BEST production choice
Qwen3-235B: 46s latency × 100% success × highest params = BEST quality choice
```

---

## 8. Final Recommendations

### Model Ranking

| Use Case | Recommended Model | Reason |
|----------|-------------------|--------|
| **Production** | GPT-OSS-20B | Fastest (8s), 100% success, reliable |
| **Quality** | Qwen3-235B-MLX | Highest extraction, 100% success |
| **Avoid** | Qwen3.5-27B | Timeout, truncation |
| **Avoid** | Qwen3.5-0.8B | Wrong structure |

### Key Lessons

1. **Reproducibility**: Use local models, not API
2. **Size ≠ Quality**: 27B failed, 235B succeeded
3. **More extraction ≠ Better**: DataFile hallucination is misleading
4. **Model-specific handling**: JSON extraction differs per model
5. **Success rate > Speed**: 100% success worth 46s latency

---

## Directory Structure

```
microbe_protocols/
├── target_protocol/             # Reference examples (elabFTW exports)
│   ├── Experiment-1-Bacterial-Cultivation.txt    # 1,589 chars
│   ├── Experiment-2-DNA-Extraction.txt           # 1,132 chars
│   ├── Experiment-3-Library-Preparation...txt    # 1,007 chars
│   ├── Experiment-4-Sequencing-Run.txt           # 610 chars (THRESHOLD)
│   ├── Experiment-5-Bioinformatic-Analysis.txt   # 1,045 chars
│   └── extracted/               # Original elabFTW JSON exports
├── rawdata/
│   └── protocols_io_raw/       # 25,136 raw JSON
├── input/                      # 100 selected protocols
├── example_protocol/           # Parsed outputs
│   ├── PROTO-MB-001_complete.txt
│   ├── PROTO-MB-001_structured.json
│   └── ...
├── microbiology_protocols/     # 3,040 filtered protocols
│   ├── Bacterial_Cultivation/
│   ├── DNA_Extraction/
│   └── ...
├── test_set_1/ ... test_set_5/ # 5 test sets (70 each)
│   ├── Bacterial_Cultivation/
│   └── all_protocols/
├── lmstudio_results/           # Benchmark outputs
│   ├── gpt-oss-20b/
│   │   ├── 121743.json
│   │   └── summary.json
│   ├── BENCHMARK_SUMMARY.md
│   ├── OUTPUT_ANALYSIS.md
│   └── DATAFILE_HALLUCINATION.md
│   └── TIMING_SUMMARY.md
├── .benchmark_state/           # Hidden state
├── protocol_parser.py          # Parser tool
├── lmstudio_model_benchmark.py # Benchmark runner
└── CLAUDE.md                   # This file
```

---

## Scripts Usage

```bash
# Parse protocols
python3 protocol_parser.py --input input/ --output example_protocol/

# Run benchmark (load model in LM Studio first)
python3 lmstudio_model_benchmark.py --model-key gpt-oss-20b

# List available models
python3 lmstudio_model_benchmark.py --list-models

# Check results
cat lmstudio_results/BENCHMARK_SUMMARY.md
```

---

## Version History

| Date | Change |
|------|--------|
| 2026-04-24 | Initial benchmark creation |
| 2026-04-24 | Removed qwen3.5-27b (timeout issues) |
| 2026-04-24 | Added DataFile hallucination analysis |
| 2026-04-24 | Unified output structure |
| 2026-04-24 | Added target_protocol reference examples |
| 2026-04-24 | Added LM Studio settings documentation |
| 2026-04-24 | Added detailed parameter/characteristics analysis |

---

## References

- Protocols.io API documentation
- ISA-JSON specification
- LM Studio documentation
- elab2arc conversion pipeline