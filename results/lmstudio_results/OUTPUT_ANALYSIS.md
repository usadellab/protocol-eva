# Detailed Output Analysis - Parameter & Characteristics Extraction

## Aggregate Statistics

| Model | Success | Avg Samples | Chars/Sample | Avg Protocols | Total Params | Params/Proto | I/O Avg | DataFiles |
|-------|---------|-------------|--------------|---------------|--------------|--------------|---------|-----------|
| **GPT-OSS-20B** | 7/7 ✅ | 2.4 | 0.8 | 5.3 | 71 | 1.9 | 1.3/1.2 | 1 |
| **Qwen3-235B-MLX** | 7/7 ✅ | 1.4 | **1.5** | 6.0 | **91** | **2.2** | 0.9/0.9 | 3 |
| **GPT-OSS-120B** | 6/7 | 2.2 | **1.7** | **11.2** | **123** | 1.8 | 1.3/1.0 | **70** |
| **Gemma-4-31B** | 5/7 | **2.4** | 1.0 | 4.8 | 43 | 1.8 | 1.3/1.0 | 7 |
| **Qwen3.5-0.8B** | 7/7* | 0 | 0 | 0 | 0 | 0 | - | - |

*Qwen3.5-0.8B returns wrong structure (single protocol, not ISA format)

## Per-Protocol Breakdown

### GPT-OSS-20B (100% Success)
| Protocol | Samples | Chars | Protocols | Params | Inputs | Outputs | Files |
|----------|---------|-------|-----------|--------|--------|---------|-------|
| 102038 | 2 | 0 | 5 | 11 | 6 | 5 | 1 |
| 103062 | 6 | 0 | 8 | 19 | 8 | 8 | 0 |
| 105043 | 3 | 6 | 5 | 16 | 5 | 5 | 0 |
| 11015 | 2 | 4 | 7 | 0 | 14 | 14 | 0 |
| 121645 | 2 | 0 | 3 | 6 | 6 | 5 | 0 |
| 121743 | 1 | 3 | 6 | 13 | 5 | 6 | 0 |
| 12716 | 1 | 1 | 3 | 6 | 3 | 3 | 0 |

### Qwen3-235B-MLX (100% Success)
| Protocol | Samples | Chars | Protocols | Params | Inputs | Outputs | Files |
|----------|---------|-------|-----------|--------|--------|---------|-------|
| 102038 | 2 | 4 | 5 | 15 | 6 | 5 | 0 |
| 103062 | 1 | 3 | 5 | 15 | 5 | 5 | 1 |
| 105043 | 1 | 3 | 3 | 9 | 3 | 3 | 0 |
| 11015 | 2 | 2 | 7 | 21 | 8 | 8 | 0 |
| 121645 | 2 | 0 | 12 | 3 | 8 | 9 | 0 |
| 121743 | 1 | 3 | 7 | 19 | 6 | 6 | 2 |
| 12716 | 1 | 0 | 3 | 9 | 3 | 3 | 0 |

### GPT-OSS-120B (85.7% Success)
| Protocol | Samples | Chars | Protocols | Params | Inputs | Outputs | Files |
|----------|---------|-------|-----------|--------|--------|---------|-------|
| 102038 | 2 | 4 | 9 | 10 | 10 | 9 | 9 |
| 103062 | 3 | 3 | 8 | 16 | 8 | 8 | 8 |
| 105043 | 3 | 6 | 3 | 12 | 3 | 3 | 0 |
| 11015 | 2 | 4 | **23** | **50** | 24 | 23 | **23** |
| 121645 | 2 | 4 | 6 | 17 | 9 | 8 | 12 |
| 121743 | - | - | - | ❌ FAILED | - | - | - |
| 12716 | 1 | 1 | 18 | 18 | 36 | 18 | 18 |

### Gemma-4-31B (71.4% Success)
| Protocol | Samples | Chars | Protocols | Params | Inputs | Outputs | Files |
|----------|---------|-------|-----------|--------|--------|---------|-------|
| 102038 | 2 | 2 | 5 | 8 | 6 | 5 | 1 |
| 103062 | 1 | 1 | 8 | 12 | 8 | 8 | 1 |
| 105043 | - | - | - | ❌ FAILED | - | - | - |
| 11015 | - | - | - | ❌ FAILED | - | - | - |
| 121645 | 2 | 2 | 4 | 7 | 5 | 4 | 4 |
| 121743 | 3 | 3 | 4 | 10 | 6 | 4 | 1 |
| 12716 | 4 | 4 | 3 | 6 | 6 | 3 | 0 |

## Key Findings

### 1. Protocol Extraction
- **GPT-OSS-120B**: Most granular (11.2 protocols avg) - breaks down into more steps
- **Qwen3-235B**: Good balance (6.0 protocols avg)
- **GPT-OSS-20B**: Moderate (5.3 protocols avg)
- **Gemma-4-31B**: Fewest (4.8 protocols avg) - more consolidated

### 2. Parameter Extraction
- **Qwen3-235B**: Best density (2.2 params/protocol)
- **GPT-OSS-20B**: Good (1.9 params/protocol)
- **GPT-OSS-120B**: Similar (1.8 params/protocol) but higher total due to more protocols
- **Gemma-4-31B**: Lowest (1.8 params/protocol)

### 3. Sample Characteristics
- **GPT-OSS-120B**: Most detailed (1.7 chars/sample)
- **Qwen3-235B**: Good (1.5 chars/sample)
- **Gemma-4-31B**: Moderate (1.0 chars/sample)
- **GPT-OSS-20B**: Fewest (0.8 chars/sample)

### 4. DataFile Extraction
- **GPT-OSS-120B**: Extensive (70 total files) - may be over-extracting
- **Gemma-4-31B**: Moderate (7 files)
- **Qwen3-235B**: Minimal (3 files)
- **GPT-OSS-20B**: Minimal (1 file)

### 5. ISA Format Compliance
| Model | Follows ISA | Notes |
|-------|-------------|-------|
| GPT-OSS-20B | ✅ Yes | Clean structure |
| Qwen3-235B | ✅ Yes | Clean structure |
| GPT-OSS-120B | ✅ Yes | Clean structure |
| Gemma-4-31B | ✅ Yes | Clean structure |
| Qwen3.5-0.8B | ❌ No | Returns single protocol object |

## Model Recommendations

**For detailed extraction**:
- GPT-OSS-120B (most protocols, most files)

**For quality extraction**:
- Qwen3-235B (highest params/protocol, 100% success)

**For balanced production**:
- GPT-OSS-20B (fastest, reliable, good extraction)

**Not recommended**:
- Qwen3.5-0.8B (wrong output format)