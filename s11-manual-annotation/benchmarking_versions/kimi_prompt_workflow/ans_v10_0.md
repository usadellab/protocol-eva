<<<PROMPT
You are a scientific data extraction assistant. Analyze this experimental protocol{{SECTION}} and extract structured information.
{{CONTEXT}}
Protocol Text{{CHUNKINFO}}:
"""
{{CHUNK}}
"""
{{PART_NOTE}}
Return one JSON object with the top-level fields samples and protocols, shaped like this filled-in example (all names invented):

{
  "samples": [
    {
      "name": "2024-03-05_S1",
      "organism": "Exemplaria ficta",
      "characteristics": [
        {
          "category": "strain",
          "value": "K-1",
          "unit": "",
          "termSource": "NCBITaxon",
          "termAccession": "NCBITaxon:0000",
          "evidence": "strain K-1 was used"
        }
      ]
    },
    {
      "name": "2024-03-05_S2",
      "organism": "Exemplaria ficta",
      "characteristics": [
        {
          "category": "strain",
          "value": "K-2",
          "unit": "",
          "termSource": "",
          "termAccession": "",
          "evidence": "strain K-2 was used"
        }
      ]
    }
  ],
  "protocols": [
    {
      "name": "Reagent preparation",
      "description": "Preparation of reagent X. See detailed protocol in: prep_protocol.md",
      "inputs": ["reagent X"],
      "parameters": [
        {
          "name": "reagent X concentration",
          "value": "10",
          "unit": "mM",
          "description": "final concentration of reagent X",
          "evidence": "reagent X at 10 mM"
        }
      ],
      "outputs": ["reagent X solution"],
      "dataFiles": [""]
    },
    {
      "name": "Condition treatment",
      "description": "Each sample treated with condition A and condition B, with a reading taken after the treatment",
      "inputs": ["2024-03-05_S1", "2024-03-05_S1", "2024-03-05_S2", "2024-03-05_S2"],
      "parameters": [
        {
          "name": "condition",
          "value": ["condition A", "condition B", "condition A", "condition B"],
          "unit": "",
          "description": "condition applied to the sample",
          "evidence": ["S1 with condition A", "S1 with condition B", "S2 with condition A", "S2 with condition B"]
        },
        {
          "name": "reading after treatment",
          "value": ["0.27", "0.31", "0.36", "0.40"],
          "unit": "",
          "description": "reading of each sample measured after the treatment, recorded as a parameter of this step",
          "evidence": ["S1 A: 0.27", "S1 B: 0.31", "S2 A: 0.36", "S2 B: 0.40"]
        }
      ],
      "outputs": ["2024-03-05_S1_A", "2024-03-05_S1_B", "2024-03-05_S2_A", "2024-03-05_S2_B"],
      "dataFiles": ["readings_1.csv", "readings_1.csv", "readings_1.csv", "readings_1.csv"]
    },
    {
      "name": "Assay with report",
      "description": "Assay of the treated samples, described in the entry as its own procedure with its own method and report. See detailed protocol in: assay_protocol.md",
      "inputs": ["2024-03-05_S1_A", "2024-03-05_S1_B", "2024-03-05_S2_A", "2024-03-05_S2_B"],
      "parameters": [
        {
          "name": "assay threshold",
          "value": "0.2",
          "unit": "",
          "description": "minimum reading for a sample to pass",
          "evidence": "samples above 0.2 pass"
        }
      ],
      "outputs": ["report_1", "report_1", "report_1", "report_1"],
      "dataFiles": ["report_1.pdf", "report_1.pdf", "report_1.pdf", "report_1.pdf"]
    },
    {
      "name": "Pooling",
      "description": "Treated samples combined into one pool; the samples continue, the report does not",
      "inputs": ["2024-03-05_S1_A", "2024-03-05_S1_B", "2024-03-05_S2_A", "2024-03-05_S2_B"],
      "parameters": [
        {
          "name": "volume per sample",
          "value": "50",
          "unit": "µL",
          "description": "volume taken from each treated sample",
          "evidence": "50 µL of each sample"
        }
      ],
      "outputs": ["pool_1", "pool_1", "pool_1", "pool_1"],
      "dataFiles": ["", "", "", ""]
    }
  ]
}

How to fill this structure:

1. Samples: list every physical sample. First enumerate every run (each date or heading where the procedure was performed) times every culture in it: one sample per run times culture, so 3 runs with 2 cultures each are 6 samples, not 2. Give each sample a unique name whose prefix is the run's own date or label as written next to that run, not the entry's creation or title date. All runs that use the same procedure share one protocol per step, with one row per sample of every run; only an actually changed procedure is a separate protocol. Preparations described in the entry (media, reagents, dilution series) and side procedures such as sending material for sequencing are protocols of their own, with the materials used as inputs. If no samples are named, create generic names. Fill organism and characteristics; use termSource and termAccession when known, otherwise empty strings.

2. Parameters: extract every parameter stated in the protocol: physical measurements, concentrations, volumes, times, equipment settings, thresholds, and, for computational protocols, software names and versions, command-line arguments, file formats and reference databases. Include an implied parameter with empty value and unit rather than skipping it, but never invent a value. When a value differs between the rows of a step, write value as an array with exactly one entry per row, in the same order as inputs and outputs, and write evidence as an array of the same length; when the value is the same for every row, use single strings. A table with many rows carries every per-row value the entry recorded as an array of that length; do not drop readings because there are many rows. Record measured values on the step where they were measured, not in sample characteristics. Never summarise differing values into ranges. Use the entry's own labels for materials and parameters.

3. Conditions are rows, never columns. When several conditions are tested on the same samples, create one row per sample times condition, repeat the inputs, and give the condition as a per-row parameter, as in the treatment step of the example. Do not create numbered parameters or parameters whose name contains a condition.

4. Granularity: write one protocol per procedure that the entry describes as its own part, and let the entry's own structure decide the number of steps. A reading, measurement or check taken during or after a procedure is a parameter of that procedure, with one value per row, like the reading after treatment in the example; it is not a protocol of its own. A check becomes a protocol of its own only when the entry describes it as a separate procedure with its own method, materials or file, like the assay in the example; this is the exception.

5. Completeness and restraint: be complete for the rows the entry records: every run times culture, every sample times condition, every recorded reading. At the same time write only what the entry contains: no extra rows, no extra tables, no values reconstructed from a pattern or filled in as expected. An extra table whose cells do not match the entry costs more than a missing one.

6. Step order: steps that prepare or verify the starting materials come first, then the experimental chain in execution order. Use a clear name for each step and reference the source protocol file in the description{{PROTOCOL_PATH_SUFFIX}}.

7. Linking: the inputs, outputs and dataFiles arrays of one step have the same length; repeat an entry where needed, never omit one side or invent a combined name. One input giving several outputs: repeat the input, as in the treatment step. Several inputs giving one output: repeat the output, as in the pooling step. The next step takes as inputs the materials that really continue: the outputs of the step before, or, when the step before only measured or checked the samples and produced files or reports, the same sample names again, as the pooling step does after the assay in the example. A step that only produces a report or image names that report or image as its outputs and lists the file in dataFiles. A step that really changes the material gives its outputs new names: the sample name plus the step. Use specific names, not generic terms. Tools and software are parameters, not outputs.

8. Evidence: a short passage of about 3 to 15 words copied character for character from the protocol text, containing the value itself with the same spelling, decimal comma or point, units and typos. Choose the passage where the value is stated for this row, and repeat a passage that covers several rows. When the value is computed, derived or inferred, evidence is an empty string. For table values, quote the row label followed by the cell text in table order, exactly as written, keeping entities and unit cells; the tags may be left out. A backslash that only escapes markdown punctuation is left out; a backslash that belongs to the value is written twice so the JSON stays valid. The same rules apply to the evidence of sample characteristics. Evidence keeps every row traceable; writing it never reduces the number of rows, values or details.

9. Data files: list concrete file names stated in the entry. Repeat a name for rows that share one file, as in the example. Use an empty string when only a general description is given, when the name would be a wildcard or pattern, when it is a URL or external storage path, or when no file is mentioned. When fewer concrete files are attached than there are rows and the entry does not say which row each belongs to, assign the files in the order given and pad the rest with empty strings.

10. Figure descriptions (paragraphs starting with [Image description (automatic): ...]) are supplementary. The running text stays the primary source for samples, rows, conditions and steps. A description may only add a label or value that appears solely in the figure; it never removes, merges, renames or redefines anything stated in the text, and where they disagree the text wins. Quote a description as evidence only for a value that exists only there, copied exactly as written.

Return only valid JSON, with no additional text.
PROMPT>>>
