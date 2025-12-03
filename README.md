# Protocol-to-ISA Benchmark Evaluation Results

Benchmark evaluation comparing LLM performance on converting free-text scientific protocols to structured ISA (Investigation-Study-Assay) JSON format.

**Date:** December 2025
**Dataset:** BioProt (10 protocols from protocols.io)
**Task:** Extract samples, protocol steps, and parameters from natural language protocols

## Results Summary

| Rank | Model | Success Rate | Parameters | Params/Step | Latency |
|------|-------|-------------|------------|-------------|---------|
| 1 | **Claude Opus 4.5** | 100% | 240 | 3.2 | API |
| 2 | **Qwen3-80B** | 100% | 215 | 2.5 | 30.5s |
| 3 | **Qwen3-235B** | 100% | 210 | 2.7 | 117.6s |
| 4 | MiniMax-M2 | 90% | 196 | 2.2 | 193.3s |
| 5 | Qwen3-30B | 90% | 116 | 2.4 | 10.8s |
| 6 | GPT-OSS-120B | 50% | 97 | 2.1 | 48.3s |

## Key Findings

1. **Opus 4.5** achieves highest parameter granularity (3.2 params/step vs 2.5 for Qwen3-80B)
2. **Qwen3-235B** extracts 2x more samples by treating intermediate products as distinct samples
3. **Step granularity varies 5x** across models (3-16 steps for same protocol)
4. **Protocol 10051** (eDNA NGS) is hardest - only 4 models succeed
5. **GPT-OSS models** suffer from chain-of-thought leakage issues

## Files

### Reports
| File | Description |
|------|-------------|
| `BENCHMARK_SUMMARY.md` | Detailed benchmark methodology and failure analysis |
| `EVALUATION_REPORT.md` | Per-protocol comparison and recommendations |
| `EXTRACTION_PATTERN_ANALYSIS.md` | Analysis of extraction pattern differences |

### Raw Results (JSON)
| File | Model | Quantization |
|------|-------|--------------|
| `opus45_results.json` | Claude Opus 4.5 | API |
| `qwen3_235b_results.json` | Qwen3-235B-A22B | 4-bit MLX |
| `qwen3_80b_results.json` | Qwen3-80B | 4-bit MLX |
| `qwen3_30b_results.json` | Qwen3-30B | 4-bit MLX |
| `minimax_m2_results.json` | MiniMax-M2 | 4-bit MLX |
| `minimax_m2_v2.json` | MiniMax-M2 (v2 run) | 4-bit MLX |
| `gpt_oss_120b_results.json` | GPT-OSS-120B | 8-bit MLX |
| `gpt_oss_120b_v2.json` | GPT-OSS-120B (v2 run) | 8-bit MLX |
| `gpt_oss_20b_results.json` | GPT-OSS-20B | Q8 MLX |
| `gpt_oss_20b_v2.json` | GPT-OSS-20B (v2 run) | Q8 MLX |

## Protocol Coverage

| ID | Protocol | Domain |
|----|----------|--------|
| 10051 | eDNA 12S Metabarcoding | NGS/Genomics |
| 1007 | Virus Enumeration | Microscopy |
| 10157 | Flow Cytometry | Cell Biology |
| 10176 | Fish Personality Assay | Behavioral |
| 10238 | NAQ Assay | Biochemistry |
| 10256 | Gel Electrophoresis | Molecular Biology |
| 10279 | Digital PCR | Genomics |
| 10606 | Mealybug Sex Ratio | Entomology |
| 10614 | E. coli Transformation | Microbiology |
| 10626 | Cell Isolation | Cell Biology |

## Recommendations

| Use Case | Recommended Model |
|----------|-------------------|
| Highest accuracy | Claude Opus 4.5 |
| Local inference | Qwen3-80B (best speed/quality) |
| Sample-centric extraction | Qwen3-235B |
| Fast processing | Qwen3-30B |

## Citation

If you use this benchmark data, please cite:

```
Protocol-to-ISA Benchmark Evaluation (2025)
Usadel Lab, Forschungszentrum Jülich
https://github.com/usadellab/protocol-eva
```

## License

MIT
