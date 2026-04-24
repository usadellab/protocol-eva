# LM Studio Benchmark Timing Summary

**Test Set**: 7 protocols (first from each category in test_set_1)

## Results

| Model | Avg Latency | Success Rate | Avg Score |
|-------|-------------|--------------|-----------|
| **gpt-oss-20b** | 6-8s | 100% ✅ | 130.2/100 |
| qwen3.5-0.8b-optiq | 2-24s | 85.7% | 0.0/100* |
| gemma-4-31b | 70-168s | 71.4% | 118.7/100 |

*Note: qwen3.5-0.8b-optiq produces valid JSON but doesn't follow ISA structure, hence 0 score.

## Detailed Timing

### gpt-oss-20b (FASTEST)
| Protocol | Latency | Status |
|----------|---------|--------|
| 121743 (Bacterial_Cultivation) | 7.35s | OK |
| 103062 (DNA_Extraction) | 8.58s | OK |
| 105043 (Transformation) | 13.27s | OK |
| 102038 (Sequencing) | 6.1s | OK |
| 12716 (PCR) | 6.19s | OK |
| 11015 (RNA_Extraction) | 12.11s | OK |
| 121645 (Bioinformatics) | 3.66s | OK |

### qwen3.5-0.8b-optiq
| Protocol | Latency | Status |
|----------|---------|--------|
| 121743 | 2.6s | OK (wrong format) |
| 103062 | 2.24s | OK (wrong format) |
| 105043 | 2.18s | OK (wrong format) |
| 102038 | 3.14s | OK (wrong format) |
| 12716 | 24.76s | OK (wrong format) |
| 11015 | 4.85s | OK (wrong format) |
| 121645 | 4.36s | OK (wrong format) |

### gemma-4-31b
| Protocol | Latency | Status |
|----------|---------|--------|
| 121743 | 77.5s | OK |
| 103062 | 95.09s | OK |
| 105043 | 168.24s | FAIL (JSON parse) |
| 102038 | 83.0s | OK |
| 12716 | 80.24s | OK |
| 11015 | 164.47s | FAIL (JSON parse) |
| 121645 | 70.2s | OK |

### qwen3.5-27b (REMOVED - too slow, truncated output)
| Protocol | Latency | Status |
|----------|---------|--------|
| 103062 | 179.53s | OK |
| 121743 | 188.12s | FAIL (empty response) |
| 105043 | 187.09s | FAIL (truncated) |
| 102038 | 186.79s | FAIL (truncated) |
| 12716 | 187.11s | FAIL (truncated) |
| 11015 | 185.06s | FAIL (truncated) |

**Issue**: qwen3.5-27b takes ~3min/request, JSON gets truncated mid-generation.

## Remaining Models to Test

- gpt-oss-120b
- qwen3-235b-mlx

## Key Findings

1. **GPT-OSS-20B is the fastest** - 3-13s per protocol, 100% success
2. **Gemma-4-31B is slow** - 70-168s, but produces quality output
3. **Small models (0.8B) don't follow complex ISA structure**
4. **Large models (27B+) may timeout/truncate** - removed qwen3.5-27b