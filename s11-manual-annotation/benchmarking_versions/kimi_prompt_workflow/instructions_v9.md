You rewrite the extraction prompt of a tool that reads an electronic-lab-notebook entry (a wet-lab protocol with tables, run data and sometimes figure descriptions) and returns ONE JSON object
(samples, protocol steps with per-row parameters, verbatim evidence passages, data files). The prompt below is the current version. The model that runs it reads it once per entry.

The user of the tool asked for these changes. Apply all of them:

1. FIX A WRONG RULE. The current prompt says the output of one protocol must exactly match the input of the next protocol. That is wrong. A step such as a quality control or a measurement can produce only a report or an image file
   while the very same samples are used again in the next step. Rewrite the linking guidance so that it is correct: the next step takes the materials that really continue (which can be the outputs of the step before, or the same samples again when the
   step before only measured or checked them and produced files/reports). Keep the rule that inputs, outputs and dataFiles arrays of one step have the same length (repeat an entry where needed); a step that only produces a report or image names that
   report or image as its output, lists the file in dataFiles, and the next step uses the original sample names as inputs again. Keep the rule that a step that really changes the material gives its output a new name (the sample name plus the step).
2. NO SHOUTING. Never write words in all capital letters for emphasis (no CRITICAL, MUST, NEVER, ONLY, ALL, FIRST, ...), and no bold markers. Explain everything in plain natural language as short numbered steps, simple sentences. Acronyms such as JSON or OD are fine.
   The final line may be: Return only valid JSON, with no additional text.
3. ONE EXAMPLE. Merge all the examples into the FIRST example JSON, condensed. Replace the separate description of the JSON structure at the top and the whole EXAMPLES section and all inline examples by one filled-in example JSON placed right after the
   protocol text. This single example (invented names only, for example S1, S2, condition A, condition B, reagent X, file names like report_1.pdf) has to show, in as few rows as possible: a samples entry with characteristics and ontology fields; a per-row parameter given as an array with
   one value per row and an array of evidence passages; a single-valued parameter; evidence as a verbatim passage; evidence left empty for a computed value; sample names that carry the run date; a preparation step listed first; conditions expanded into rows (one row per sample and condition,
   inputs repeated, the condition as a per-row parameter); a pooling or splitting step with repeated entries; a quality-control step that produces a report or image (outputs are the report names, dataFiles list the files) while the samples continue unchanged into the next step;
   data files repeated for rows that share a file and left empty where no concrete file is named. After the example write the explanation as a few short numbered steps in plain sentences. The example must be valid JSON.
4. KEEP THE CONTENT. Everything else the prompt teaches stays, but shorter and in plain language: which parameters to extract (also for computational protocols), per-row values, the evidence rules (a short verbatim passage containing the value, the passage of this row, empty when the value is
   computed or inferred, table rows quoted as written, the exception for markdown backslashes), sample extraction (every run times every culture is its own sample, runs with the same procedure share one protocol, the run's own date as prefix, preparations and side procedures are their own protocols,
   never summarise differing values, keep every measurement, use the entry's own labels), conditions are rows and never columns, order of steps, data file rules (concrete file names only, no wildcards, no external paths), and the figure-description rules (the descriptions are supplementary: the running text
   stays the primary source; a description may only add a label or value that appears only in the figure; it never removes, merges or renames samples, rows or conditions stated in the text; where they disagree the text wins; quote a description only for a value that exists only there).
5. The result must be clearly shorter than the current prompt.

Constraints (checked by program; a violation is sent back to you): keep the six placeholders {{SECTION}}, {{CONTEXT}}, {{CHUNKINFO}}, {{CHUNK}}, {{PROTOCOL_PATH_SUFFIX}}, {{PART_NOTE}} exactly as written and exactly once each, in the places where they are now
({{CHUNK}} stays inside the triple quotes of the protocol text, as now); do not use backticks or the characters dollar-brace; the JSON field names stay exactly as they are (samples, name, organism, characteristics, category, value, unit, termSource, termAccession, evidence, protocols, description, inputs,
parameters, outputs, dataFiles); no words in all capital letters except acronyms; generic only: invented example names, and do not use words from any specific experiment (a check compares your words with a list of words from curated annotation tables; ordinary words that happen to be on that list are flagged too,
so prefer simple neutral wording and rephrase when a word is reported); do not ask the model to repair, tolerate or post-process anything (strict valid JSON only).

ANSWER FORMAT: the complete new prompt text between the markers <<<PROMPT and PROMPT>>> on lines of their own, and nothing else (no explanation before or after).
