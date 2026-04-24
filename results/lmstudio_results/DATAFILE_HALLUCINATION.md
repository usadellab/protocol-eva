# DataFile Hallucination Analysis

## Critical Finding: ALL non-empty dataFiles are HALLUCINATED

**Summary**: None of the actual file names extracted by any model are mentioned in the original protocol texts. Models invent plausible file names based on domain knowledge.

## DataFile Extraction Statistics

| Model | Total | Empty Strings | Real Names | Hallucinated | % Hallucinated |
|-------|-------|---------------|------------|--------------|----------------|
| **GPT-OSS-120B** | 70 | 58 | 12 | **12** | **100%** of real names |
| **Gemma-4-31B** | 7 | 0 | 7 | **7** | **100%** |
| **Qwen3-235B-MLX** | 3 | 0 | 3 | **3** | **100%** |
| **GPT-OSS-20B** | 1 | 0 | 1 | **1** | **100%** |

## Key Insight

**GPT-OSS-120B's "70 dataFiles" statistic is misleading**:
- 58 (82.9%) are empty strings `['']` - placeholders
- 12 are actual file names - ALL hallucinated

## Case Study: Protocol 121645 (Bioinformatics)

### Original Protocol Excerpt
```
Title: A Bioconductor R pipeline for analysis of RNA-seq data

Description:
We describe a powerful and easy-to-use RNA-seq analysis pipeline...
It starts with raw read output of an sequencing instrument and reports
lists of genes that are found to be differentially expressed...
```

**Note**: No specific file names mentioned!

### Hallucinated File Names by Each Model

#### GPT-OSS-120B (12 hallucinated files)
| Protocol | Hallucinated Files |
|----------|-------------------|
| Raw read acquisition | `Sample_1_R1.fastq.gz`, `Sample_1_R2.fastq.gz`, `Sample_2_R1.fastq.gz`, `Sample_2_R2.fastq.gz` |
| Read alignment | `Sample_1_aligned.bam`, `Sample_2_aligned.bam` |
| Read summarization | `gene_counts.txt` |
| Normalization | `voom_normalized.rds` |
| Differential expression | `DE_results.csv` |
| Result reporting | `DE_summary.pdf`, `volcano_plot.png`, `heatmap.png` |

#### Gemma-4-31B (4 hallucinated files)
| Protocol | Hallucinated Files |
|----------|-------------------|
| Sample Prep | `alignment_files.bam` |
| Analysis | `counts.txt`, `normalized_data.csv`, `deg_list.csv` |

#### Qwen3-235B-MLX (3 hallucinated files in other protocols)
Files like `.fastq`, `.bam`, `.csv` that weren't in originals.

#### GPT-OSS-20B (1 hallucinated file)
Similar pattern - invents plausible names.

## Why This Happens

1. **Domain Knowledge Injection**: Models know bioinformatics pipelines typically produce files like `.fastq`, `.bam`, `.csv`, `.pdf`
2. **Pattern Completion**: When asked for "dataFiles", models complete the pattern with typical outputs
3. **No Verification**: Models don't verify if these files are actually mentioned

## Impact on Quality

| Model | Approach | Quality Impact |
|-------|----------|----------------|
| **GPT-OSS-120B** | Invents 12 specific file names | ❌ LOW - False specificity |
| **GPT-OSS-20B** | Mostly empty, 1 invented | ⚠️ BETTER - Less hallucination |
| **Qwen3-235B-MLX** | Empty arrays `[]` mostly | ✅ BEST - Honest extraction |
| **Gemma-4-31B** | Invents 7 files | ❌ LOW |

## Recommendation

**Prefer models that return empty `[]` or `['']`** rather than hallucinated specific names.

Qwen3-235B-MLX is most honest - returns empty dataFiles array when no files mentioned.

## Correction to Previous Analysis

The "70 dataFiles" for GPT-OSS-120B is NOT a strength - it's a weakness:
- 82.9% are empty placeholders (not useful)
- 17.1% are hallucinated (misleading)

**Corrected ranking for dataFiles extraction**:
| Model | Rating | Reason |
|-------|--------|--------|
| Qwen3-235B-MLX | ✅ BEST | Returns `[]` - honest |
| GPT-OSS-20B | ✅ Good | Minimal hallucination |
| Gemma-4-31B | ⚠️ Poor | Hallucinates file names |
| GPT-OSS-120B | ❌ Worst | Most hallucinated files |