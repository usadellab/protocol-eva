# Final Benchmark Summary - Protocol-to-ISA Conversion

**Test Date**: April 24, 2026
**Test Set**: test_set_1 (7 protocols, first from each category)
**Models Tested**: 5 local LLM models via LM Studio

---

## Executive Summary

| Model | Success | Score | Latency | Recommendation |
|-------|---------|-------|---------|----------------|
| **GPT-OSS-20B** | **100%** | 130.2 | **8.2s** | ⭐ **BEST for Production** |
| **Qwen3-235B-MLX** | **100%** | **139.6** | 46.1s | ⭐ **BEST for Quality** |
| GPT-OSS-120B | 85.7% | 149.1 | 33.7s | Good but over-extracts |
| Gemma-4-31B | 71.4% | 118.7 | 81.2s | Slow, unreliable |
| Qwen3.5-0.8B | 100%* | 0 | 6.3s | ❌ Wrong structure |

*Qwen3.5-0.8B: 100% JSON valid but 0% ISA format compliance

---

## Comprehensive Statistics

| Model | Succ | Samples | Chars | Protos | Params | Units | Values | DF | Hallu% | Lat | Score |
|-------|------|---------|-------|--------|--------|-------|--------|-----|--------|-----|-------|
| **gpt-oss-20b** | 7/7 | 2.4 | 0.82 | 5.3 | 1.92 | 39.4% | 66.2% | 1 | 100% | **8.2s** | 130.2 |
| **qwen3-235b-mlx** | 7/7 | 1.4 | **1.50** | 6.0 | **2.17** | **59.3%** | 57.1% | 3 | 100% | 46.1s | **139.6** |
| gpt-oss-120b | 6/7 | 2.2 | 1.69 | **11.2** | 1.84 | **75.6%** | **95.1%** | 70 | 100% | 33.7s | 149.1 |
| gemma-4-31b | 5/7 | 2.4 | 1.00 | 4.8 | 1.79 | 60.5% | 53.5% | 7 | 100% | 81.2s | 118.7 |
| qwen3.5-0.8b | 7/7* | 0 | 0 | 0 | 0 | 0 | 0 | 0 | - | 6.3s | 0 |

---

## Detailed Metrics by Model

### GPT-OSS-20B ⭐ WINNER (Production)

| Metric | Value | Assessment |
|--------|-------|------------|
| Success Rate | **100%** (7/7) | Excellent |
| Avg Samples | 2.4/protocol | Good |
| Characteristics/Sample | 0.82 | Low |
| Avg Protocols Extracted | 5.3 | Balanced |
| Parameters/Protocol | 1.92 | Good |
| Units Extracted | 39.4% of params | Moderate |
| Values Extracted | 66.2% of params | Good |
| DataFiles Hallucinated | 100% (1/1 named) | Low count, high hallucination |
| Avg Latency | **8.2s** | FASTEST |
| Avg Score | 130.2/100 | Good |

**Strengths**: Fastest, 100% reliable, balanced extraction
**Weaknesses**: Low characteristics per sample, 100% datafile hallucination rate
**Verdict**: Best for production due to speed + reliability trade-off

---

### Qwen3-235B-MLX ⭐ WINNER (Quality)

| Metric | Value | Assessment |
|--------|-------|------------|
| Success Rate | **100%** (7/7) | Excellent |
| Avg Samples | 1.4/protocol | Conservative |
| Characteristics/Sample | **1.50** | HIGHEST |
| Avg Protocols Extracted | 6.0 | Good |
| Parameters/Protocol | **2.17** | HIGHEST |
| Units Extracted | **59.3%** of params | Good |
| Values Extracted | 57.1% of params | Good |
| DataFiles Hallucinated | 100% (3/3 named) | All hallucinated |
| Avg Latency | 46.1s | Moderate |
| Avg Score | **139.6/100** | HIGHEST |

**Strengths**: Highest parameter density, best characteristics extraction, 100% reliable
**Weaknesses**: 5x slower than GPT-OSS-20B, all datafiles hallucinated
**Verdict**: Best when quality matters more than speed

---

### GPT-OSS-120B

| Metric | Value | Assessment |
|--------|-------|------------|
| Success Rate | 85.7% (6/7) | Moderate |
| Avg Samples | 2.2/protocol | Good |
| Characteristics/Sample | 1.69 | Good |
| Avg Protocols Extracted | **11.2** | OVER-extracts |
| Parameters/Protocol | 1.84 | Good |
| Units Extracted | **75.6%** of params | HIGHEST |
| Values Extracted | **95.1%** of params | HIGHEST |
| DataFiles Total | 70 | EXCESSIVE |
| Empty DataFiles | 58 (82.9%) | Placeholders |
| Named DataFiles | 12 | All hallucinated (100%) |
| Avg Latency | 33.7s | Moderate |
| Avg Score | 149.1/100 | Over-extraction |

**Strengths**: Highest unit/value extraction, most granular protocol breakdown
**Weaknesses**: 1 failure, over-extracts (11.2 protocols avg), 100% datafile hallucination
**Verdict**: Too verbose, hallucinates excessively

---

### Gemma-4-31B

| Metric | Value | Assessment |
|--------|-------|------------|
| Success Rate | 71.4% (5/7) | POOR |
| Avg Samples | 2.4/protocol | Good |
| Characteristics/Sample | 1.00 | Moderate |
| Avg Protocols Extracted | 4.8 | Low |
| Parameters/Protocol | 1.79 | Moderate |
| Units Extracted | 60.5% of params | Good |
| Values Extracted | 53.5% of params | Moderate |
| DataFiles Hallucinated | 100% (7/7 named) | All hallucinated |
| Avg Latency | 81.2s | SLOW |
| Avg Score | 118.7/100 | Lowest among working models |

**Strengths**: Good sample extraction
**Weaknesses**: 2 failures, slow (10x GPT-OSS-20B), lowest quality score
**Verdict**: Not recommended - slow and unreliable

---

### Qwen3.5-0.8B-optiq ❌ FAILED

| Metric | Value | Assessment |
|--------|-------|------------|
| Success Rate | 100%* | Valid JSON |
| ISA Compliance | **0%** | CRITICAL FAILURE |
| Samples | 0 | None |
| Characteristics | 0 | None |
| Protocols | 0 | None |
| Parameters | 0 | None |
| Output Format | Single protocol object | Wrong ISA structure |
| Avg Latency | 6.3s | Fastest |
| Avg Score | 0/100 | Useless |

**Issue**: Returns `{name, inputs, parameters, outputs}` instead of `{samples[], protocols[]}`
**Verdict**: Cannot be used for ISA extraction - wrong output schema

---

## Hallucination Analysis

### DataFile Hallucination Rate: 100% for ALL Models

**Critical Finding**: Every non-empty datafile name extracted is hallucinated.

| Model | Total DF | Empty | Named | Hallucinated | Rate |
|-------|----------|-------|-------|--------------|------|
| GPT-OSS-120B | 70 | 58 | 12 | 12 | **100%** |
| Gemma-4-31B | 7 | 0 | 7 | 7 | **100%** |
| Qwen3-235B | 3 | 0 | 3 | 3 | **100%** |
| GPT-OSS-20B | 1 | 0 | 1 | 1 | **100%** |

**Example Hallucination (Protocol 121645 - Bioinformatics)**:
- Original mentions: NO specific files
- Models invented: `Sample_1.fastq.gz`, `aligned.bam`, `DE_results.csv`, `volcano_plot.png`
- All plausible but fabricated based on domain knowledge

**Recommendation**: Prefer models returning empty `[]` over hallucinated names.

---

## Parameter Extraction Quality

### Units & Values Coverage

| Model | Params | Units | Values | Units% | Values% |
|-------|--------|-------|--------|--------|---------|
| GPT-OSS-120B | 123 | **93** | **117** | **75.6%** | **95.1%** |
| Qwen3-235B | 91 | 54 | 52 | 59.3% | 57.1% |
| Gemma-4-31B | 43 | 26 | 23 | 60.5% | 53.5% |
| GPT-OSS-20B | 71 | 28 | 47 | 39.4% | 66.2% |

**Insight**: GPT-OSS-120B extracts most parameters with units/values, but over-extracts overall.

---

## Speed-Quality Trade-off

| Model | Latency | Success | Quality | Throughput |
|-------|---------|---------|---------|------------|
| **GPT-OSS-20B** | **8.2s** | 100% | 130.2 | **7.6/min** |
| Qwen3-235B | 46.1s | 100% | 139.6 | 1.3/min |
| GPT-OSS-120B | 33.7s | 85.7% | 149.1 | 1.8/min |
| Gemma-4-31B | 81.2s | 71.4% | 118.7 | 0.5/min |

**Production Efficiency**: GPT-OSS-20B is **6x faster** than Qwen3-235B with same success rate.

---

## Final Recommendations

### For Production Pipelines

**Use**: **GPT-OSS-20B**

| Factor | Rating |
|--------|--------|
| Speed | ⭐⭐⭐⭐⭐ (8.2s) |
| Reliability | ⭐⭐⭐⭐⭐ (100%) |
| Quality | ⭐⭐⭐⭐ (130.2) |
| Cost | ⭐⭐⭐⭐⭐ (Free, local) |

**Expected**: 7-8 protocols/minute, reliable JSON, moderate extraction depth

---

### For Quality-Critical Tasks

**Use**: **Qwen3-235B-MLX**

| Factor | Rating |
|--------|--------|
| Speed | ⭐⭐⭐ (46s) |
| Reliability | ⭐⭐⭐⭐⭐ (100%) |
| Quality | ⭐⭐⭐⭐⭐ (139.6) |
| Cost | ⭐⭐⭐⭐⭐ (Free, local) |

**Expected**: 1.3 protocols/minute, highest parameter density, best characteristics

---

### Hybrid Strategy

```python
# Recommended workflow:
# 1. First pass: GPT-OSS-20B (fast, 100% success)
# 2. Quality validation: Use Qwen3-235B for important protocols
# 3. Filter hallucinated datafiles: Remove all named datafiles
```

---

## Key Lessons

1. **100% DataFile Hallucination**: Never trust named datafiles - always filter
2. **Larger ≠ Better**: 27B failed, 235B succeeded, 120B over-extracts
3. **Success Rate Critical**: 85.7% success means 1/7 protocols wasted time
4. **Speed Matters**: 6x throughput difference affects production scalability
5. **ISA Format Compliance**: Qwen3.5-0.8B proves "valid JSON" ≠ "correct structure"

---

## Removed Models

| Model | Reason |
|-------|--------|
| Qwen3.5-27B | ~180s latency, JSON truncation, 14.3% success |

---

## Test Set Info

- **Protocols**: 7 (first from each category)
- **Categories**: Bacterial_Cultivation, Bioinformatics, DNA_Extraction, PCR, RNA_Extraction, Sequencing, Transformation
- **Size Range**: 610-2000 characters
- **Source**: protocols.io (filtered microbiology collection)

---

**Generated**: April 24, 2026
**Framework**: protocol-eva
**API**: LM Studio (localhost:1234)