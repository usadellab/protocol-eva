# LM Studio Benchmark Results

**Test Set**: 7 protocols (first from each category in test_set_1)
**Date**: 2026-04-24

## Model Performance Summary

| Model | Success | Avg Score | Latency | Params | Units | Values | DF Hallu |
|-------|---------|-----------|---------|--------|-------|--------|----------|
| **GPT-OSS-20B** | **100%** | 130.2 | **8.2s** | 1.92/proto | 39.4% | 66.2% | 100% |
| **Qwen3-235B** | **100%** | **139.6** | 46.1s | **2.17/proto** | 59.3% | 57.1% | 100% |
| GPT-OSS-120B | 85.7% | 149.1 | 33.7s | 1.84/proto | **75.6%** | **95.1%** | 100% |
| Gemma-4-31B | 71.4% | 118.7 | 81.2s | 1.79/proto | 60.5% | 53.5% | 100% |
| Qwen3.5-0.8B | 100%* | 0 | 6.3s | 0 | 0 | 0 | - |

*Valid JSON but wrong ISA structure

## Ranking

| Rank | Model | Recommendation |
|------|-------|----------------|
| **1** | GPT-OSS-20B | ⭐ **BEST for Production** |
| **2** | Qwen3-235B-MLX | ⭐ **BEST for Quality** |
| **3** | GPT-OSS-120B | Good, over-extracts |
| **4** | Gemma-4-31B | Slow, unreliable |
| **5** | Qwen3.5-0.8B | ❌ Wrong schema |
| - | Qwen3.5-27B | REMOVED (timeout) |

## Extraction Metrics

### Samples & Characteristics

| Model | Samples | Characteristics | Chars/Sample |
|-------|---------|-----------------|--------------|
| GPT-OSS-20B | 17 (2.4 avg) | 14 | 0.82 |
| Qwen3-235B | 10 (1.4 avg) | **15** | **1.50** |
| GPT-OSS-120B | 13 (2.2 avg) | 22 | 1.69 |
| Gemma-4-31B | 12 (2.4 avg) | 12 | 1.00 |

### Protocols & Parameters

| Model | Protocols | Parameters | Params/Proto | Units% | Values% |
|-------|-----------|------------|--------------|--------|---------|
| GPT-OSS-120B | **67** (11.2 avg) | **123** | 1.84 | **75.6%** | **95.1%** |
| Qwen3-235B | 42 (6.0 avg) | 91 | **2.17** | 59.3% | 57.1% |
| GPT-OSS-20B | 37 (5.3 avg) | 71 | 1.92 | 39.4% | 66.2% |
| Gemma-4-31B | 24 (4.8 avg) | 43 | 1.79 | 60.5% | 53.5% |

## Timing Analysis

### Per-Protocol Latency (seconds)

| Protocol | GPT-OSS-20B | Qwen3-235B | GPT-OSS-120B | Gemma-4-31B |
|----------|-------------|------------|--------------|-------------|
| 121743 | **7.3s** | 65.0s | 28.1s ❌ | 77.5s |
| 103062 | **8.6s** | 46.8s | 25.1s | 95.1s |
| 105043 | **13.3s** | 33.3s | 22.4s | 168.2s ❌ |
| 102038 | **6.1s** | 48.4s | 22.9s | 83.0s |
| 12716 | **6.2s** | 29.6s | 40.9s | 80.2s |
| 11015 | **12.1s** | 64.6s | 67.2s | 164.5s ❌ |
| 121645 | **3.7s** | 34.9s | 23.6s | 70.2s |

## Critical Findings

### 1. 100% DataFile Hallucination

**All named datafiles are fabricated:**
| Model | Total DF | Empty | Named | All Hallucinated |
|-------|----------|-------|-------|------------------|
| GPT-OSS-120B | 70 | 58 | 12 | **YES (100%)** |
| Gemma-4-31B | 7 | 0 | 7 | **YES (100%)** |
| Qwen3-235B | 3 | 0 | 3 | **YES (100%)** |
| GPT-OSS-20B | 1 | 0 | 1 | **YES (100%)** |

**Action**: Filter all named datafiles from output.

### 2. GPT-OSS-120B Over-Extracts

- 11.2 protocols avg (others: 4.8-6.0)
- Score 149.1 indicates verbosity
- 82.9% datafiles are empty placeholders

### 3. Qwen3.5-0.8B Wrong Schema

Returns `{name, inputs, outputs}` instead of `{samples[], protocols[]}`

## Recommendations

| Use Case | Model | Reason |
|----------|-------|--------|
| **Production** | GPT-OSS-20B | 8s latency, 100% success |
| **Quality** | Qwen3-235B | Highest extraction quality |
| **Avoid** | Gemma-4-31B | Slow (81s), 2 failures |
| **Avoid** | Qwen3.5-0.8B | Wrong ISA format |

## Files

```
lmstudio_results/
├── gpt-oss-20b/           # 7 protocol results
├── qwen3-235b-mlx/
├── gpt-oss-120b/
├── gemma-4-31b/
├── qwen3.5-0.8b-optiq/
└── *.md                   # Analysis reports
```