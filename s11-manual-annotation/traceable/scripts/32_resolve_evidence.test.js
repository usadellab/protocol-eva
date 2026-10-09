// Control for 32_resolve_evidence.js: one case per status. node scripts/32_resolve_evidence.test.js (exit 1 on failure)
const E = require('./32_resolve_evidence.js');
const text = '## Run 2\nWT: OD <mark>0,653</mark> after washing\n\nMutant: OD 0,36 after **washing**\ngrow for 48h at 37 °C\n5 uL were spotted';
const llm = { samples: [], protocols: [{ name: 'Wash', parameters: [
  { name: 'OD', value: ['0.653', '0.36'], evidence: ['WT: OD 0,653 after washing', 'Mutant: OD 0,36 after washing'] }, // markup, comma
  { name: 'time', value: '48', evidence: 'grow for 48h' },                  // number glued to its unit
  { name: 'temp', value: '37', evidence: 'grow for 48 h at 37 C' },        // reworded quote -> fuzzy
  { name: 'vol', value: '10', evidence: '5 uL were spotted' },              // passage found, value not in it
  { name: 'speed', value: '200', evidence: 'shaken at 200 rpm' },          // quote not in the text
  { name: 'derived', value: '26.5', evidence: '' }] }] };                   // declared as not written in the text
const want = ['exact', 'exact', 'exact', 'fuzzy', 'value_not_in_quote', 'unresolved', 'missing'];
const got = E.resolveEvidence(llm, text).entries.map(e => e.status);
if (JSON.stringify(got) !== JSON.stringify(want)) { console.error('FAILED', got); process.exit(1); }
console.log('32 control OK: exact (markup, decimal comma, glued unit), fuzzy, value_not_in_quote, unresolved, missing');
