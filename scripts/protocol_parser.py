#!/usr/bin/env python3
"""
Protocol Parser - Extracts complete protocol text from protocols.io format.

Handles Draft.js JSON format in 'step' field and combines with protocol_text.

Usage:
    python3 protocol_parser.py --input input/ --output example_protocol/
    python3 protocol_parser.py --single input/PROTO-MB-008.json
"""

import json
import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def extract_text_from_draftjs(step_json_str: str) -> str:
    """
    Extract plain text from Draft.js JSON format.

    Draft.js format:
    {
        "blocks": [
            {"key": "xxx", "text": "Some text", "type": "unstyled", ...},
            ...
        ],
        "entityMap": {...}
    }

    Returns concatenated text from all blocks.
    """
    try:
        step_data = json.loads(step_json_str)
        blocks = step_data.get("blocks", [])

        # Extract text from each block, preserving paragraph breaks
        texts = []
        for block in blocks:
            text = block.get("text", "")
            if text.strip():  # Skip empty blocks
                texts.append(text)

        return "\n".join(texts)
    except json.JSONDecodeError:
        # If not valid JSON, return raw string
        return step_json_str


def extract_entities_from_draftjs(step_json_str: str) -> Dict:
    """
    Extract entities (links, reagents, tables) from Draft.js format.

    Returns entityMap with useful metadata.
    """
    try:
        step_data = json.loads(step_json_str)
        entity_map = step_data.get("entityMap", {})
        return entity_map
    except json.JSONDecodeError:
        return {}


def extract_table_data(entity_map: Dict) -> List[Dict]:
    """
    Extract table data from entityMap if present.

    Tables are stored as 'tables' type entities with 'data' containing cells.
    """
    tables = []
    for entity_key, entity in entity_map.items():
        if entity.get("type") == "tables":
            table_data = entity.get("data", {})
            data_rows = table_data.get("data", [])
            if data_rows:
                tables.append({
                    "headers": data_rows[0] if data_rows else [],
                    "rows": data_rows[1:] if len(data_rows) > 1 else [],
                    "col_widths": table_data.get("colWidths", []),
                    "raw_data": table_data.get("printData", data_rows)
                })
    return tables


def extract_reagents(entity_map: Dict) -> List[Dict]:
    """
    Extract reagent information from entityMap if present.

    Reagents are stored as 'reagents' type entities.
    """
    reagents = []
    for entity_key, entity in entity_map.items():
        if entity.get("type") == "reagents":
            reagent_data = entity.get("data", {})
            reagents.append({
                "name": reagent_data.get("name", ""),
                "sku": reagent_data.get("sku", ""),
                "vendor": reagent_data.get("vendor", {}).get("name", ""),
                "url": reagent_data.get("url", ""),
                "mol_weight": reagent_data.get("mol_weight", 0),
                "cas_number": reagent_data.get("cas_number", ""),
            })
    return reagents


def parse_section_html(section_html: Optional[str]) -> str:
    """
    Extract section name from HTML format.

    Input: "<p>Pellet Cells</p>" or None
    Output: "Pellet Cells" or ""
    """
    if section_html is None:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', section_html)
    return clean.strip()


def parse_protocol(protocol_data: Dict) -> Dict:
    """
    Parse a complete protocol from protocols.io JSON format.

    Returns:
        {
            "id": "...",
            "name": "...",
            "complete_text": "...",  # Full protocol text for LLM input
            "text_sections": [...],  # Structured sections
            "raw_steps": [...],      # Original step JSON preserved
            "tables": [...],         # Extracted table data
            "reagents": [...],       # Extracted reagent info
            "metadata": {...}        # Protocol metadata
        }
    """
    # Basic metadata
    metadata = {
        "id": protocol_data.get("id", ""),
        "original_id": protocol_data.get("original_id", ""),
        "name": protocol_data.get("name", ""),
        "domain": protocol_data.get("domain", ""),
        "complexity": protocol_data.get("complexity", ""),
        "source": protocol_data.get("source", ""),
        "step_count": protocol_data.get("step_count", 0),
        "keywords": protocol_data.get("keywords", ""),
        "url": protocol_data.get("url", ""),
    }

    # Start with protocol_text (intro/summary)
    protocol_text = protocol_data.get("protocol_text", "")

    # Parse original_steps
    original_steps = protocol_data.get("original_steps", [])
    text_sections = []
    raw_steps = []
    all_tables = []
    all_reagents = []

    if original_steps:
        for step in original_steps:
            # Extract step metadata
            step_number = step.get("number", "")
            section_name = parse_section_html(step.get("section", ""))
            section_color = step.get("section_color", "")
            duration = step.get("duration", 0)
            is_substep = step.get("is_substep", False)

            # Extract text from Draft.js format
            step_json_str = step.get("step", "")
            step_text = extract_text_from_draftjs(step_json_str)

            # Extract entities (tables, reagents)
            entity_map = extract_entities_from_draftjs(step_json_str)
            tables = extract_table_data(entity_map)
            reagents = extract_reagents(entity_map)

            # Store structured section
            text_sections.append({
                "step_number": step_number,
                "section_name": section_name,
                "section_color": section_color,
                "duration": duration,
                "is_substep": is_substep,
                "text": step_text,
                "tables_count": len(tables),
                "reagents_count": len(reagents),
            })

            # Store raw step data (preserving original JSON)
            raw_steps.append({
                "id": step.get("id"),
                "guid": step.get("guid"),
                "number": step_number,
                "section": section_name,
                "duration": duration,
                "step_json": step_json_str,  # Original Draft.js JSON string
                "parsed_text": step_text,    # Extracted text
                "tables": tables,            # Extracted table data
                "reagents": reagents,        # Extracted reagent data
            })

            all_tables.extend(tables)
            all_reagents.extend(reagents)

    # Build complete text for LLM input
    complete_text_parts = [protocol_text]

    if text_sections:
        complete_text_parts.append("\n\n=== PROTOCOL STEPS ===\n")

        for section in text_sections:
            section_header = f"\n## Step {section['step_number']}: {section['section_name']}"
            if section['duration'] > 0:
                section_header += f" (Duration: {section['duration']} min)"
            complete_text_parts.append(section_header)
            complete_text_parts.append(section['text'])

            # Include table data as text
            for raw_step in raw_steps:
                if raw_step['number'] == section['step_number'] and raw_step['tables']:
                    for t in raw_step['tables']:
                        complete_text_parts.append("\n[TABLE]")
                        if t['headers']:
                            complete_text_parts.append(" | ".join(str(h) for h in t['headers']))
                        for row in t['rows']:
                            complete_text_parts.append(" | ".join(str(c) for c in row))

    # Include reagents summary
    if all_reagents:
        complete_text_parts.append("\n\n=== REAGENTS/MATERIALS ===\n")
        for r in all_reagents:
            reagent_line = f"- {r['name']}"
            if r['vendor']:
                reagent_line += f" ({r['vendor']})"
            if r['sku']:
                reagent_line += f" [SKU: {r['sku']}]"
            complete_text_parts.append(reagent_line)

    complete_text = "\n".join(complete_text_parts)

    return {
        "metadata": metadata,
        "complete_text": complete_text,
        "text_sections": text_sections,
        "raw_steps": raw_steps,
        "tables": all_tables,
        "reagents": all_reagents,
        "original_protocol_text": protocol_text,
        "original_steps_json": original_steps,
    }


def format_table_as_text(table: Dict) -> str:
    """Format table data as readable text."""
    lines = []
    lines.append("TABLE:")

    # Headers
    if table.get('headers'):
        header_line = " | ".join(str(h) for h in table['headers'])
        lines.append(header_line)
        lines.append("-" * len(header_line))

    # Rows
    for row in table.get('rows', []):
        row_line = " | ".join(str(c) for c in row)
        lines.append(row_line)

    return "\n".join(lines)


def format_reagent_as_text(reagent: Dict) -> str:
    """Format reagent data as readable text."""
    parts = [f"- {reagent['name']}"]
    if reagent['vendor']:
        parts.append(f"Vendor: {reagent['vendor']}")
    if reagent['sku']:
        parts.append(f"SKU: {reagent['sku']}")
    if reagent['url']:
        parts.append(f"URL: {reagent['url']}")
    return " | ".join(parts)


def save_parsed_protocol(parsed: Dict, output_dir: Path, format_type: str = "all"):
    """
    Save parsed protocol in multiple formats.

    Formats:
        - complete_text.txt: Full protocol text for LLM input
        - structured.json: Structured data with sections, tables, reagents
        - raw_steps.json: Original step JSON preserved
        - tables.json: Extracted table data
        - reagents.json: Extracted reagent data
    """
    protocol_id = parsed['metadata']['id']

    if format_type == "all" or format_type == "text":
        text_file = output_dir / f"{protocol_id}_complete.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(parsed['complete_text'])
        print(f"  Saved: {text_file}")

    if format_type == "all" or format_type == "structured":
        structured_file = output_dir / f"{protocol_id}_structured.json"
        with open(structured_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": parsed['metadata'],
                "text_sections": parsed['text_sections'],
                "tables": parsed['tables'],
                "reagents": parsed['reagents'],
            }, f, indent=2, ensure_ascii=False)
        print(f"  Saved: {structured_file}")

    if format_type == "all" or format_type == "raw":
        raw_file = output_dir / f"{protocol_id}_raw_steps.json"
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": parsed['metadata'],
                "original_protocol_text": parsed['original_protocol_text'],
                "raw_steps": parsed['raw_steps'],
                "original_steps_json": parsed['original_steps_json'],
            }, f, indent=2, ensure_ascii=False)
        print(f"  Saved: {raw_file}")

    if format_type == "all" or format_type == "tables":
        if parsed['tables']:
            tables_file = output_dir / f"{protocol_id}_tables.json"
            with open(tables_file, 'w', encoding='utf-8') as f:
                json.dump(parsed['tables'], f, indent=2, ensure_ascii=False)
            print(f"  Saved: {tables_file}")

    if format_type == "all" or format_type == "reagents":
        if parsed['reagents']:
            reagents_file = output_dir / f"{protocol_id}_reagents.json"
            with open(reagents_file, 'w', encoding='utf-8') as f:
                json.dump(parsed['reagents'], f, indent=2, ensure_ascii=False)
            print(f"  Saved: {reagents_file}")


def main():
    parser = argparse.ArgumentParser(description="Protocol Parser - Extract complete protocol text")
    parser.add_argument("--input", "-i", type=str,
                        help="Input directory or single JSON file")
    parser.add_argument("--output", "-o", type=str, default="example_protocol",
                        help="Output directory")
    parser.add_argument("--single", "-s", type=str,
                        help="Process single protocol file")
    parser.add_argument("--format", "-f", type=str, default="all",
                        choices=["all", "text", "structured", "raw", "tables", "reagents"],
                        help="Output format type")
    parser.add_argument("--limit", "-n", type=int,
                        help="Limit number of protocols to process")

    args = parser.parse_args()

    # Require either --input or --single
    if not args.input and not args.single:
        parser.error("Either --input or --single is required")

    # Use --single as input if provided
    if args.single:
        args.input = args.single

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.single or (input_path.is_file() and input_path.suffix == '.json'):
        # Process single file
        single_path = input_path
        if not single_path.exists():
            print(f"Error: File not found: {single_path}")
            return

        print(f"\nParsing: {single_path}")
        with open(single_path) as f:
            protocol_data = json.load(f)

        parsed = parse_protocol(protocol_data)
        save_parsed_protocol(parsed, output_dir, args.format)

        print(f"\nProtocol ID: {parsed['metadata']['id']}")
        print(f"Protocol Name: {parsed['metadata']['name']}")
        print(f"Steps: {len(parsed['text_sections'])}")
        print(f"Tables: {len(parsed['tables'])}")
        print(f"Reagents: {len(parsed['reagents'])}")
        print(f"Complete text length: {len(parsed['complete_text'])} chars")

    elif input_path.is_dir():
        # Process all JSON files in directory
        json_files = sorted(input_path.glob("*.json"))
        if args.limit:
            json_files = json_files[:args.limit]

        print(f"\nFound {len(json_files)} protocol files")
        print(f"Output directory: {output_dir}")
        print(f"Format: {args.format}")
        print("-" * 50)

        for i, json_file in enumerate(json_files, 1):
            print(f"\n[{i}/{len(json_files)}] {json_file.name}")

            try:
                with open(json_file) as f:
                    protocol_data = json.load(f)

                parsed = parse_protocol(protocol_data)
                save_parsed_protocol(parsed, output_dir, args.format)

                steps = len(parsed['text_sections'])
                tables = len(parsed['tables'])
                reagents = len(parsed['reagents'])
                text_len = len(parsed['complete_text'])

                print(f"  Steps: {steps}, Tables: {tables}, Reagents: {reagents}, Text: {text_len} chars")

            except Exception as e:
                print(f"  ERROR: {e}")

        print("\n" + "=" * 50)
        print("PARSING COMPLETE")
        print(f"Output saved to: {output_dir}")

    else:
        print(f"Error: Input path not found: {input_path}")


if __name__ == "__main__":
    main()