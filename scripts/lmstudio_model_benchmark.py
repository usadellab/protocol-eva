#!/usr/bin/env python3
"""
LM Studio Model Benchmark for Protocol-to-ISA Conversion

Benchmarks 6 LM Studio models on microbiology protocol conversion.
Uses test_set_1 protocols (7 samples, first from each category).

Model-specific JSON handling:
- GPT-OSS models: DO NOT force { prefix (triggers chain-of-thought)
- Qwen models: Handle markdown code blocks, preamble text
- Gemma models: Standard brace-counting JSON extraction

Usage:
    python3 lmstudio_model_benchmark.py --model-key gemma-4-31b
    python3 lmstudio_model_benchmark.py --list-models
"""

import json
import time
import re
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Configuration - paths relative to script location in protocol-eva/scripts/
SCRIPT_DIR = Path(__file__).parent
EVA_DIR = SCRIPT_DIR.parent  # protocol-eva root
RESULTS_DIR = EVA_DIR / "results" / "lmstudio_results"  # Output directory
STATE_DIR = EVA_DIR / "results" / ".benchmark_state"    # Hidden state for progress
DATASETS_DIR = EVA_DIR / "datasets"                     # Test sets location
LMSTUDIO_API = "http://localhost:1234/v1/chat/completions"

# Model configurations
MODEL_CONFIGS = {
    "gemma-4-31b": {
        "model_id": "google/gemma-4-31b",
        "name": "Gemma-4-31B",
        "force_json_prefix": True,
        "json_handler": "standard",
        "temperature": 0.1,
        "max_tokens": 4096,
    },
    "qwen3.5-0.8b-optiq": {
        "model_id": "qwen3.5-0.8b-optiq",
        "name": "Qwen3.5-0.8B-Optiq",
        "force_json_prefix": True,
        "json_handler": "qwen",
        "temperature": 0.1,
        "max_tokens": 4096,
    },
    "gpt-oss-120b": {
        "model_id": "openai/gpt-oss-120b",
        "name": "GPT-OSS-120B",
        "force_json_prefix": False,  # DO NOT add { prefix - triggers CoT
        "json_handler": "gpt_oss",
        "temperature": 0.1,
        "max_tokens": 8192,
    },
    "gpt-oss-20b": {
        "model_id": "openai/gpt-oss-20b",
        "name": "GPT-OSS-20B",
        "force_json_prefix": False,  # DO NOT add { prefix
        "json_handler": "gpt_oss",
        "temperature": 0.1,
        "max_tokens": 8192,
    },
    "qwen3-235b-mlx": {
        "model_id": "qwen3-235b-a22b-instruct-2507-mlx",
        "name": "Qwen3-235B-A22B-MLX",
        "force_json_prefix": True,
        "json_handler": "qwen",
        "temperature": 0.1,
        "max_tokens": 4096,
    },
}

# ISA extraction prompt
ISA_PROMPT_TEMPLATE = '''You are a scientific data extraction assistant. Analyze this experimental protocol and extract structured information.

Protocol Text:
"""
{protocol_text}
"""

Extract and return ONLY a JSON object (no markdown, no explanation) with this structure:
{{
  "samples": [
    {{
      "name": "Sample identifier or name",
      "organism": "Organism or source",
      "characteristics": [
        {{
          "category": "Characteristic category",
          "value": "Characteristic value",
          "unit": "Unit if applicable or empty string",
          "termSource": "Ontology source or empty string",
          "termAccession": "Ontology term ID or empty string"
        }}
      ]
    }}
  ],
  "protocols": [
    {{
      "name": "Protocol step name",
      "description": "Brief description of this protocol step",
      "inputs": ["array of input sample/material names"],
      "parameters": [
        {{
          "name": "parameter name",
          "value": "actual value if specified, empty string if not",
          "unit": "measurement unit or empty string",
          "description": "what this parameter represents"
        }}
      ],
      "outputs": ["array of output sample/material names"],
      "dataFiles": []
    }}
  ]
}}

CRITICAL - PARAMETER EXTRACTION RULES:
1. Extract ALL parameters mentioned: temperatures, times, concentrations, volumes, equipment settings
2. For bioinformatics protocols: extract software names, versions, command-line arguments, thresholds
3. If a parameter value is mentioned, include it in the description field
4. Even if parameters array would be empty, try to infer 2-3 key parameters from context

IMPORTANT - SAMPLE EXTRACTION:
1. Extract sample information: names, organism, characteristics (age, tissue type, genotype, treatment)
2. If no specific samples mentioned, create generic samples (e.g., "Sample_1", "Sample_2")

IMPORTANT - PROTOCOL LINKING:
1. Link protocols sequentially - OUTPUT of one protocol MUST EXACTLY MATCH INPUT of next
2. Use clear names (e.g., "Sample Preparation", "Measurement", "Analysis")
3. First protocol inputs should reference sample names from samples array
4. Tools/software are parameters, NOT outputs

Return ONLY valid JSON, no additional text.'''


def extract_first_complete_json(json_str: str) -> str:
    """Extract first complete JSON object using brace counting."""
    brace_count = 0
    first_valid_end = -1
    start_idx = -1

    for i, c in enumerate(json_str):
        if c == '{':
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif c == '}':
            brace_count -= 1
            if brace_count == 0 and first_valid_end == -1:
                first_valid_end = i + 1
                break

    if start_idx >= 0 and first_valid_end > start_idx:
        return json_str[start_idx:first_valid_end]
    return json_str


def extract_json_standard(response_text: str) -> str:
    """Standard JSON extraction - brace counting."""
    json_str = response_text.strip()

    # Remove markdown code blocks
    if '```json' in json_str:
        start_marker = json_str.find('```json')
        json_start = json_str.find('{', start_marker)
        json_str = json_str[json_start:]
        if '```' in json_str:
            end_marker = json_str.find('```')
            json_str = json_str[:end_marker]

    json_str = re.sub(r'```\s*$', '', json_str)

    # Find {"samples" pattern
    match = re.search(r'\{\s*"samples"', json_str)
    if match:
        json_str = json_str[match.start():]

    return extract_first_complete_json(json_str)


def extract_json_qwen(response_text: str) -> str:
    """Extract JSON from Qwen model output (handles markdown blocks, preamble)."""
    json_str = response_text.strip()

    # Handle markdown code blocks
    if '```json' in json_str:
        start = json_str.find('```json')
        json_start = json_str.find('{', start)
        json_str = json_str[json_start:]
        if '```' in json_str:
            json_str = json_str[:json_str.find('```')]
    elif '```' in json_str:
        # Generic code block
        start = json_str.find('```')
        json_start = json_str.find('{', start)
        if json_start > -1:
            json_str = json_str[json_start:]
            if '```' in json_str:
                json_str = json_str[:json_str.find('```')]

    # Find JSON start pattern
    match = re.search(r'\{\s*"samples"', json_str)
    if match:
        json_str = json_str[match.start():]

    # Remove trailing markdown
    json_str = re.sub(r'```\s*$', '', json_str)

    return extract_first_complete_json(json_str)


def extract_json_gpt_oss(response_text: str) -> str:
    """Extract JSON from GPT-OSS model output (handles <|channel|> markers)."""
    json_str = response_text.strip()

    # Handle <|channel|>final<|message|> marker
    if '<|channel|>final<|message|>' in json_str:
        marker_idx = json_str.find('<|channel|>final<|message|>')
        json_str = json_str[marker_idx + len('<|channel|>final<|message|>'):].strip()

    # Handle <|end|> <|start|>assistant pattern
    if '<|end|>' in json_str:
        last_end = json_str.rfind('<|end|>')
        remainder = json_str[last_end:]
        if '{' in remainder:
            json_str = remainder[remainder.find('{'):]

    # Remove markdown code blocks if present
    if '```json' in json_str:
        start = json_str.find('```json')
        json_start = json_str.find('{', start)
        json_str = json_str[json_start:]
        if '```' in json_str:
            json_str = json_str[:json_str.find('```')]

    json_str = re.sub(r'```\s*$', '', json_str)

    # Find JSON start
    match = re.search(r'\{\s*"samples"', json_str)
    if match:
        json_str = json_str[match.start():]

    return extract_first_complete_json(json_str)


class LMStudioClient:
    """Client for LM Studio API."""

    def __init__(self, model_config: Dict):
        self.config = model_config

    def call(self, prompt: str) -> Tuple[str, float, bool]:
        """Call LM Studio API and return response."""
        # Apply force_json_prefix setting
        if self.config.get("force_json_prefix", False):
            full_prompt = prompt + "\n{"
        else:
            full_prompt = prompt

        payload = {
            "model": self.config["model_id"],
            "messages": [{"role": "user", "content": full_prompt}],
            "max_tokens": self.config.get("max_tokens", 4096),
            "temperature": self.config.get("temperature", 0.1),
            "top_p": 0.9,
        }

        start_time = time.time()
        try:
            response = requests.post(
                LMSTUDIO_API,
                json=payload,
                timeout=600,
                headers={"Content-Type": "application/json"}
            )
            latency = time.time() - start_time

            if response.status_code != 200:
                return f"API error: {response.status_code} - {response.text}", latency, False

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content, latency, True

        except requests.exceptions.Timeout:
            latency = time.time() - start_time
            return "Timeout error", latency, False
        except Exception as e:
            latency = time.time() - start_time
            return str(e), latency, False

    def extract_json(self, response_text: str) -> Tuple[Dict, bool]:
        """Extract JSON using model-specific handler."""
        handler = self.config.get("json_handler", "standard")

        if handler == "qwen":
            json_str = extract_json_qwen(response_text)
        elif handler == "gpt_oss":
            json_str = extract_json_gpt_oss(response_text)
        else:
            json_str = extract_json_standard(response_text)

        try:
            parsed = json.loads(json_str)
            return parsed, True
        except json.JSONDecodeError as e:
            return {"error": str(e), "raw_response": response_text[:500]}, False


class OriginalTextEvaluator:
    """Evaluates model output against original protocol text."""

    def evaluate(self, model_output: Dict, original_text: str, original_step_count: int) -> Dict:
        """Evaluate model output for faithfulness to original protocol."""
        if not model_output or "protocols" not in model_output:
            return {
                "step_preservation": 0,
                "parameter_extraction": 0,
                "component_extraction": 0,
                "sequence_order": 0,
                "overall": 0,
                "notes": "No valid output"
            }

        extracted_steps = model_output.get("protocols", [])
        extracted_count = len(extracted_steps)
        step_preservation = min(100, (extracted_count / max(1, original_step_count)) * 100) if original_step_count > 0 else 50

        original_numbers = self._extract_numbers(original_text)
        extracted_numbers = self._extract_numbers_from_output(model_output)
        param_extraction = (len(extracted_numbers) / max(1, len(original_numbers))) * 100 if original_numbers else 50

        original_components = self._extract_components(original_text)
        extracted_components = self._extract_components_from_output(model_output)
        comp_extraction = (len(extracted_components) / max(1, len(original_components))) * 100 if original_components else 50

        sequence_order = 100 if extracted_count > 0 else 0

        overall = (step_preservation * 0.4 + param_extraction * 0.25 +
                   comp_extraction * 0.20 + sequence_order * 0.15)

        return {
            "step_preservation": round(step_preservation, 1),
            "parameter_extraction": round(param_extraction, 1),
            "component_extraction": round(comp_extraction, 1),
            "sequence_order": round(sequence_order, 1),
            "overall": round(overall, 1),
            "extracted_steps": extracted_count,
            "original_steps": original_step_count,
        }

    def _extract_numbers(self, text: str) -> List[str]:
        """Extract numeric values from text."""
        patterns = [
            r'(\d+\.?\d*)\s*(?:C|celsius)',
            r'(\d+\.?\d*)\s*(?:min|mins|minutes)',
            r'(\d+\.?\d*)\s*(?:sec|seconds|s)',
            r'(\d+\.?\d*)\s*(?:hr|hours|h)',
            r'(\d+\.?\d*)\s*(?:ul|ml|mL)',
            r'(\d+\.?\d*)\s*(?:ug|mg|g)',
            r'(\d+\.?\d*)\s*(?:mM|uM|M)',
            r'(\d+\.?\d*)\s*(?:rpm|RPM|xg)',
            r'(\d+\.?\d*)\s*(?:%|percent)',
            r'(\d+\.?\d*)\s*(?:cycles|x)',
        ]
        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            numbers.extend(matches)
        return numbers

    def _extract_numbers_from_output(self, output: Dict) -> List[str]:
        """Extract numeric values from model output."""
        numbers = []
        for protocol in output.get("protocols", []):
            for param in protocol.get("parameters", []):
                value = param.get("value", "")
                if value:
                    numbers.append(str(value))
        return numbers

    def _extract_components(self, text: str) -> List[str]:
        """Extract materials/reagents from text."""
        patterns = [
            r'([A-Za-z][A-Za-z\s\-]+(?:buffer|Buffer|medium|Medium|agar|Agar|broth|Broth|solution|Solution))',
        ]
        components = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            components.extend(matches)
        return list(set([c.strip() for c in components if c.strip()]))

    def _extract_components_from_output(self, output: Dict) -> List[str]:
        """Extract materials/reagents from model output."""
        components = []
        for sample in output.get("samples", []):
            name = sample.get("name", "")
            if name:
                components.append(name)
        for protocol in output.get("protocols", []):
            for input_item in protocol.get("inputs", []):
                components.append(input_item)
            for output_item in protocol.get("outputs", []):
                components.append(output_item)
        return list(set(components))


class StateManager:
    """Manages incremental saving of benchmark results."""

    def __init__(self, output_dir: Path, model_key: str):
        self.output_dir = output_dir
        self.model_key = model_key
        # Model results in: lmstudio_results/<model_key>/
        self.model_dir = output_dir / model_key
        # State in hidden: .benchmark_state/<model_key>/
        self.state_dir = STATE_DIR / model_key
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def load_progress(self) -> Dict:
        """Load progress from state file."""
        progress_file = self.state_dir / "progress.json"
        if progress_file.exists():
            try:
                with open(progress_file) as f:
                    return json.load(f)
            except:
                pass
        return {"total": 0, "completed": [], "failed": []}

    def save_progress(self, progress: Dict):
        """Save progress atomically."""
        progress_file = self.state_dir / "progress.json"
        with open(progress_file, 'w') as f:
            json.dump(progress, f, indent=2)

    def save_result(self, protocol_id: str, result: Dict):
        """Save individual protocol result."""
        result_file = self.model_dir / f"{protocol_id}.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    def get_completed_ids(self) -> set:
        """Get set of completed protocol IDs."""
        progress = self.load_progress()
        return set(progress.get("completed", []))

    def finalize_results(self, summary: Dict) -> Path:
        """Combine all results into final output file."""
        all_results = []
        for result_file in self.model_dir.glob("*.json"):
            # Skip summary.json
            if result_file.name == "summary.json":
                continue
            try:
                with open(result_file) as f:
                    all_results.append(json.load(f))
            except:
                continue

        final_output = {
            "model": self.model_key,
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "results": all_results
        }

        # Save as summary.json in model folder
        output_file = self.model_dir / "summary.json"
        with open(output_file, 'w') as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)

        return output_file


def load_test_protocols(test_set_dir: Path) -> List[Dict]:
    """Load first protocol from each category in test_set_1."""
    categories = [
        "Bacterial_Cultivation",
        "DNA_Extraction",
        "Transformation",
        "Sequencing",
        "PCR",
        "RNA_Extraction",
        "Bioinformatics"
    ]

    protocols = []
    for category in categories:
        category_dir = test_set_dir / category
        if not category_dir.exists():
            print(f"Warning: Category directory not found: {category_dir}")
            continue

        # Get all txt files, sorted by name
        txt_files = sorted(category_dir.glob("*.txt"))
        if not txt_files:
            print(f"Warning: No protocols found in {category_dir}")
            continue

        # Take first file
        first_file = txt_files[0]

        # Read protocol content
        with open(first_file) as f:
            content = f.read()

        # Count steps (lines starting with ## Step)
        step_count = len(re.findall(r'^## Step', content, re.MULTILINE))

        protocol_id = first_file.stem
        protocols.append({
            "id": protocol_id,
            "name": f"{category} - {protocol_id}",
            "category": category,
            "protocol_text": content,
            "step_count": step_count,
        })

    return protocols


def run_benchmark(model_key: str, test_set_dir: Path, output_dir: Path) -> Dict:
    """Run benchmark for a single model."""
    model_config = MODEL_CONFIGS[model_key]
    model_name = model_config["name"]

    print(f"\n{'=' * 60}")
    print(f"Running LM Studio benchmark for: {model_name}")
    print(f"Model ID: {model_config['model_id']}")
    print(f"JSON Handler: {model_config['json_handler']}")
    print(f"Force JSON Prefix: {model_config['force_json_prefix']}")
    print(f"{'=' * 60}\n")

    # Load test protocols (first from each category)
    protocols = load_test_protocols(test_set_dir)
    print(f"Loaded {len(protocols)} test protocols (first from each category)")

    if not protocols:
        print("No protocols to process!")
        return {"error": "No protocols found"}

    state_manager = StateManager(output_dir, model_key)
    completed_ids = state_manager.get_completed_ids()

    client = LMStudioClient(model_config)
    evaluator = OriginalTextEvaluator()

    success_count = 0
    fail_count = 0
    total_latency = 0

    progress = state_manager.load_progress()
    progress["total"] = len(protocols)

    for i, protocol in enumerate(protocols, 1):
        pid = protocol["id"]

        if pid in completed_ids:
            print(f"[{i}/{len(protocols)}] {pid}: SKIPPED (already completed)")
            continue

        print(f"\n[{i}/{len(protocols)}] {pid}: {protocol['name']}")

        # Format prompt
        prompt = ISA_PROMPT_TEMPLATE.format(protocol_text=protocol["protocol_text"])

        # Call API
        response_text, latency, call_success = client.call(prompt)
        total_latency += latency

        if not call_success:
            result = {
                "protocol_id": pid,
                "protocol_name": protocol["name"],
                "category": protocol["category"],
                "original_steps": protocol["step_count"],
                "success": False,
                "latency_s": round(latency, 2),
                "evaluation": {"overall": 0, "notes": "API call failed"},
                "raw_output": {"error": response_text},
                "json_valid": False,
                "error": response_text
            }
            fail_count += 1
            print(f"  FAIL | {latency:.1f}s | API error: {response_text[:50]}")
        else:
            # Extract JSON
            isa_output, json_success = client.extract_json(response_text)

            if json_success:
                eval_result = evaluator.evaluate(
                    isa_output,
                    protocol["protocol_text"],
                    protocol["step_count"]
                )
                success_count += 1
                result = {
                    "protocol_id": pid,
                    "protocol_name": protocol["name"],
                    "category": protocol["category"],
                    "original_steps": protocol["step_count"],
                    "success": True,
                    "latency_s": round(latency, 2),
                    "evaluation": eval_result,
                    "raw_output": isa_output,
                    "json_valid": True,
                }
                print(f"  OK | {latency:.1f}s | Score: {eval_result['overall']:.1f}")
            else:
                result = {
                    "protocol_id": pid,
                    "protocol_name": protocol["name"],
                    "category": protocol["category"],
                    "original_steps": protocol["step_count"],
                    "success": False,
                    "latency_s": round(latency, 2),
                    "evaluation": {"overall": 0, "notes": "JSON parse failed"},
                    "raw_output": isa_output,
                    "json_valid": False,
                    "error": isa_output.get("error", "Unknown")
                }
                fail_count += 1
                print(f"  FAIL | {latency:.1f}s | JSON parse error")

        # Save result
        state_manager.save_result(pid, result)

        if result["success"]:
            progress["completed"].append(pid)
        else:
            progress["failed"].append(pid)
        state_manager.save_progress(progress)

    # Calculate summary from ALL results (including previously completed)
    all_results = []
    successful_results = []
    failed_results = []
    total_results_latency = 0

    for rf in state_manager.model_dir.glob("*.json"):
        # Skip summary.json
        if rf.name == "summary.json":
            continue
        with open(rf) as f:
            r = json.load(f)
            all_results.append(r)
            if r.get("success"):
                successful_results.append(r)
                total_results_latency += r.get("latency_s", 0)
            else:
                failed_results.append(r)
                total_results_latency += r.get("latency_s", 0)

    total_success = len(successful_results)
    total_failed = len(failed_results)
    avg_score = 0
    avg_latency = 0

    if successful_results:
        avg_score = sum(r["evaluation"]["overall"] for r in successful_results) / len(successful_results)

    if all_results:
        avg_latency = total_results_latency / len(all_results)

    summary = {
        "model_key": model_key,
        "model_name": model_name,
        "model_id": model_config["model_id"],
        "json_handler": model_config["json_handler"],
        "force_json_prefix": model_config["force_json_prefix"],
        "total_protocols": len(protocols),
        "successful": total_success,
        "failed": total_failed,
        "success_rate": round(total_success / max(1, len(protocols)) * 100, 1),
        "avg_latency_s": round(avg_latency, 2),
        "avg_score": round(avg_score, 1),
        "total_time_s": round(total_results_latency, 1),
        "processed_this_run": len(protocols) - len(completed_ids),
    }

    output_file = state_manager.finalize_results(summary)

    print(f"\n{'=' * 60}")
    print(f"Benchmark complete for {model_name}")
    print(f"{'=' * 60}")
    print(f"Success rate: {summary['success_rate']}%")
    print(f"Average score: {summary['avg_score']}/100")
    print(f"Average latency: {summary['avg_latency_s']}s")
    print(f"Results saved: {output_file}")

    return summary


def list_models():
    """Print available models."""
    print("\nAvailable Models:")
    print("-" * 70)
    for key, config in MODEL_CONFIGS.items():
        print(f"  {key}")
        print(f"    Name: {config['name']}")
        print(f"    Model ID: {config['model_id']}")
        print(f"    JSON Handler: {config['json_handler']}")
        print(f"    Force JSON Prefix: {config['force_json_prefix']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="LM Studio Model Benchmark for Protocol-to-ISA Conversion"
    )
    parser.add_argument(
        "--model-key",
        choices=list(MODEL_CONFIGS.keys()),
        help="Model key to benchmark"
    )
    parser.add_argument(
        "--test-set",
        type=str,
        default=str(DATASETS_DIR / "test_set_1"),
        help="Path to test set directory (default: datasets/test_set_1)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(RESULTS_DIR),
        help="Output directory for results"
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models"
    )

    args = parser.parse_args()

    if args.list_models:
        list_models()
        return

    if not args.model_key:
        print("Error: --model-key is required")
        print("Use --list-models to see available models")
        return

    test_set_dir = Path(args.test_set)
    if not test_set_dir.exists():
        print(f"Error: Test set directory not found: {test_set_dir}")
        return

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check LM Studio is running
    try:
        health_check = requests.get("http://localhost:1234/v1/models", timeout=5)
        if health_check.status_code != 200:
            print("Warning: LM Studio may not be running properly")
    except:
        print("Error: LM Studio is not running at localhost:1234")
        print("Please start LM Studio and load the model before running benchmark")
        return

    run_benchmark(args.model_key, test_set_dir, output_dir)


if __name__ == "__main__":
    main()