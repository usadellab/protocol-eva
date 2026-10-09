# Protocol Evaluation (protocol-eva)

Benchmark framework for evaluating LLM models on protocol-to-ISA conversion.

## Structure

```
protocol-eva/
├── datasets/                    # Protocol test data
│   ├── test_set_1/              # 70 protocols (10 per category)
│   ├── test_set_2/
│   ├── test_set_3/
│   ├── test_set_4/
│   ├── test_set_5/              # 5 × 70 = 350 total test protocols
│   └── target_protocol/         # Reference examples (elabFTW)
│
├── scripts/                     # Evaluation tools
│   ├── lmstudio_model_benchmark.py  # Main benchmark runner
│   └── protocol_parser.py           # Protocol text extraction
│
├── results/                     # Benchmark outputs
│   ├── lmstudio_results/        # Model outputs
│   │   ├── gpt-oss-20b/
│   │   ├── qwen3-235b-mlx/
│   │   └── ...
│   ├── .benchmark_state/        # Progress tracking
│   ├── FINAL_SUMMARY.md         # Complete evaluation report
│   ├── OUTPUT_ANALYSIS.md
│   └── DATAFILE_HALLUCINATION.md
│
├── docs/                        # Documentation
│   └── CLAUDE.md                # Full project documentation
│
└── s11-manual-annotation/   # Benchmark against manual annotations (Supplement S11), see below
```

## s11-manual-annotation

Five eLabFTW entries converted to ISA assay tables by LLMs and scored (record precision, recall, F1) against manual annotations. Material of Supplement S11 of the elab2arc publication: the scores of prompt version 6 on 10 model rows, the per-run scores, the other prompt versions, evidence-quote and figure experiments, and the code. See `s11-manual-annotation/README.md`.

## Quick Start

```bash
# Run benchmark (load model in LM Studio first)
cd scripts
python3 lmstudio_model_benchmark.py --model-key gpt-oss-20b

# List available models
python3 lmstudio_model_benchmark.py --list-models

# Parse raw protocols
python3 protocol_parser.py --input ../datasets/raw/ --output parsed/
```

## Test Sets

| Set | Protocols | Categories |
|-----|-----------|------------|
| test_set_1 | 70 | 7 categories × 10 |
| test_set_2 | 70 | Random selection |
| test_set_3 | 70 | Random selection |
| test_set_4 | 70 | Random selection |
| test_set_5 | 70 | Random selection |
| **Total** | **350** | |

## Categories

- Bacterial_Cultivation
- Bioinformatics
- DNA_Extraction
- PCR
- RNA_Extraction
- Sequencing
- Transformation

## Models Tested

| Model | Success Rate | Avg Score | Avg Latency |
|-------|--------------|-----------|-------------|
| GPT-OSS-20B | 100% | 130.2/100 | 8.2s |
| Qwen3-235B-MLX | 100% | 139.6/100 | 46.1s |
| GPT-OSS-120B | 85.7% | 149.1/100 | 32.9s |
| Gemma-4-31B | 71.4% | 118.7/100 | 105.5s |

**Best for Production**: GPT-OSS-20B (fastest + reliable)
**Best for Quality**: Qwen3-235B-MLX (highest extraction)

## Documentation

See `docs/CLAUDE.md` for full documentation including:
- Data collection methodology
- Model selection criteria
- LM Studio settings
- Statistical analysis
- Hallucination detection