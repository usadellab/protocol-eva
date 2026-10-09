// Resolve the evidence quotes of an elab2arc LLM extraction (prompt v7) against the protocol text:
// every value cell gets a verifiable source location or an explicit reason why it has none.
//
//   node 32_resolve_evidence.js <llm.json> <protocol.md> [evidence.json]
// <llm.json> is llmData itself or a 26_llm_extraction.js result ({llmData}); default output: evidence.json
// next to <llm.json>. Pure function resolveEvidence(llmData, text) has no dependencies, so the same file can be
// loaded in the browser (window.Elab2ArcEvidence) and write the evidence file into the ARC.
//
// Matching (deterministic, no LLM):
//   normalise quote and text alike - HTML tags and markdown markup (* _ ` | \ #) dropped, whitespace and line
//   breaks collapsed, case folded - keeping a map back to the original characters;
//   exact  = the normalised quote occurs in the normalised text (several occurrences: the first one, and the count
//            is recorded - a quote should be long enough to be unique);
//   fuzzy  = otherwise, the text window with the most quote tokens in order (token LCS), accepted at >= 0.75 of
//            the quote's tokens;
//   value check: every token of the value (numbers compared canonically: 0,653 == 0.653; a number glued to a unit,
//            "48h", counts as that number) must occur in the located passage.
// Status per cell: exact | fuzzy (located, value inside) | value_not_in_quote (located, value missing)
//                  | unresolved (quote not found) | missing (no quote given = the model marks it as not in the text)
(function (root) {
  const TAG = /<[^<>]{0,300}>/g;
  const MARKUP = /[*_`|\\#]/;

  // normalised string + map from each normalised character to its original index
  function normalise(text) {
    const masked = text.replace(TAG, m => ' '.repeat(m.length));
    let out = '', map = [], space = true;
    for (let i = 0; i < masked.length; i++) {
      let ch = masked[i];
      if (MARKUP.test(ch)) ch = ' ';
      if (/\s/.test(ch)) {
        if (!space) { out += ' '; map.push(i); space = true; }
        continue;
      }
      out += ch.toLowerCase(); map.push(i); space = false;
    }
    const toks = [], index = new Map();
    for (const m of masked.toLowerCase().matchAll(/[a-z0-9äöüßµμ°%]+(?:[.,]\d+)?/g)) {
      const glued = m[0].match(/^(\d+(?:[.,]\d+)?)([a-zµμ°%]+)$/);
      const parts = glued ? [[canon(glued[1]), m.index, m.index + glued[1].length], [glued[2], m.index + glued[1].length, m.index + m[0].length]]
                          : [[canon(m[0]), m.index, m.index + m[0].length]];
      for (const [t, a, b] of parts) {
        if (!index.has(t)) index.set(t, []);
        index.get(t).push(toks.length);
        toks.push({ t, a, b });
      }
    }
    return { norm: out.trimEnd(), map, tokens: toks, index };
  }

  const canon = t => /^\d+(?:[.,]\d+)?$/.test(t) ? String(parseFloat(t.replace(',', '.'))) : t;
  function tokens(s) {
    const out = [];
    for (const m of s.toLowerCase().matchAll(/[a-z0-9äöüßµμ°%]+(?:[.,]\d+)?/g)) {
      const t = m[0], glued = t.match(/^(\d+(?:[.,]\d+)?)([a-zµμ°%]+)$/);
      if (glued) out.push(canon(glued[1]), glued[2]); else out.push(canon(t));
    }
    return out;
  }

  function locate(quote, src) {
    const q = normalise(quote).norm.trim();
    if (!q) return null;
    const first = src.norm.indexOf(q);
    if (first >= 0) {
      let count = 0, k = -1;
      while ((k = src.norm.indexOf(q, k + 1)) >= 0) count++;
      return { status: 'exact', start: src.map[first], end: src.map[first + q.length - 1] + 1, occurrences: count };
    }
    // fuzzy: LCS over number/unit-aware tokens ("48 h" == "48h", "0,653" == "0.653"), in a window around each
    // occurrence of the quote's rarest token
    const qt = tokens(quote);
    if (!qt.length) return null;
    const st = src.tokens;
    const freq = t => (src.index.get(t) || []).length;
    const anchor = qt.reduce((a, t) => (freq(t) && (!freq(a) || freq(t) < freq(a)) ? t : a), qt[0]);
    let best = null;
    for (const pos of src.index.get(anchor) || []) {
      const lo = Math.max(0, pos - qt.length - 2), win = st.slice(lo, pos + qt.length + 3);
      const dp = Array(qt.length + 1).fill(0).map(() => Array(win.length + 1).fill(0));
      for (let x = 1; x <= qt.length; x++)
        for (let y = 1; y <= win.length; y++)
          dp[x][y] = qt[x - 1] === win[y - 1].t ? dp[x - 1][y - 1] + 1 : Math.max(dp[x - 1][y], dp[x][y - 1]);
      const score = dp[qt.length][win.length] / qt.length;
      if (best && score <= best.score) continue;
      let x = qt.length, y = win.length, first = null, last = null;   // backtrack: first and last matched token
      while (x > 0 && y > 0) {
        if (qt[x - 1] === win[y - 1].t && dp[x][y] === dp[x - 1][y - 1] + 1) { last = last ?? y - 1; first = y - 1; x--; y--; }
        else if (dp[x - 1][y] >= dp[x][y - 1]) x--; else y--;
      }
      if (first !== null) best = { score, start: win[first].a, end: win[last].b };
    }
    if (best && best.score >= 0.75)
      return { status: 'fuzzy', start: best.start, end: best.end, score: +best.score.toFixed(3), occurrences: 1 };
    return null;
  }

  function valueInPassage(value, passage) {
    const vt = tokens(String(value)), pt = new Set(tokens(passage));
    return vt.length > 0 && vt.every(t => pt.has(t));
  }

  function lineOf(text, pos) {
    let n = 1;
    for (let i = 0; i < pos; i++) if (text.charCodeAt(i) === 10) n++;
    return n;
  }

  function cells(llmData) {
    const out = [];
    (llmData.samples || []).forEach((s, i) => (s.characteristics || []).forEach((c, j) =>
      out.push({ field_path: `samples[${i}].characteristics[${j}].value`, name: c.category, value: c.value, evidence: c.evidence })));
    (llmData.protocols || []).forEach((p, i) => (p.parameters || []).forEach((prm, j) => {
      const base = `protocols[${i}].parameters[${j}].value`;
      if (Array.isArray(prm.value)) {
        prm.value.forEach((v, k) => {
          const ev = Array.isArray(prm.evidence) ? prm.evidence[k] : prm.evidence;   // one passage may cover all rows
          out.push({ field_path: `${base}[${k}]`, name: prm.name, value: v, evidence: ev,
                     misaligned: Array.isArray(prm.evidence) && prm.evidence.length !== prm.value.length });
        });
      } else {
        out.push({ field_path: base, name: prm.name, value: prm.value,
                   evidence: Array.isArray(prm.evidence) ? prm.evidence[0] : prm.evidence });
      }
    }));
    return out.filter(c => String(c.value ?? '').trim() !== '');
  }

  function resolveEvidence(llmData, text) {
    const src = normalise(text);
    const entries = cells(llmData).map(c => {
      const quote = typeof c.evidence === 'string' ? c.evidence : '';
      const e = { field_path: c.field_path, name: c.name, value: String(c.value), quote };
      if (c.misaligned) e.misaligned = true;
      if (!quote.trim()) return { ...e, status: 'missing' };
      const loc = locate(quote, src);
      if (!loc) return { ...e, status: 'unresolved' };
      const passage = text.slice(loc.start, loc.end);
      Object.assign(e, { char_span: [loc.start, loc.end], line: lineOf(text, loc.start), passage,
                         occurrences: loc.occurrences, ...(loc.score ? { fuzzy_score: loc.score } : {}) });
      e.status = valueInPassage(c.value, passage) ? loc.status : 'value_not_in_quote';
      return e;
    });
    const count = s => entries.filter(e => e.status === s).length;
    const summary = { cells: entries.length, exact: count('exact'), fuzzy: count('fuzzy'),
                      value_not_in_quote: count('value_not_in_quote'), unresolved: count('unresolved'), missing: count('missing') };
    summary.traceable = summary.exact + summary.fuzzy;
    summary.traceable_share = entries.length ? +(summary.traceable / entries.length).toFixed(4) : 0;
    return { entries, summary };
  }

  const api = { resolveEvidence, normalise, locate, valueInPassage };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Elab2ArcEvidence = api;

  if (typeof require !== 'undefined' && typeof module !== 'undefined' && require.main === module) {
    const fs = require('fs'), path = require('path'), crypto = require('crypto');
    const [llmFile, mdFile, outArg] = process.argv.slice(2);
    if (!llmFile || !mdFile) { console.error('usage: node 32_resolve_evidence.js <llm.json> <protocol.md> [evidence.json]'); process.exit(2); }
    const raw = JSON.parse(fs.readFileSync(llmFile, 'utf8'));
    const llmData = raw.llmData || raw;
    if (!llmData || !llmData.protocols) { console.error(`${llmFile}: no llmData`); process.exit(1); }
    const text = fs.readFileSync(mdFile, 'utf8');
    const { entries, summary } = resolveEvidence(llmData, text);
    const out = outArg || path.join(path.dirname(llmFile), 'evidence.json');
    fs.writeFileSync(out, JSON.stringify({ source: path.basename(mdFile),
      source_sha256: crypto.createHash('sha256').update(text).digest('hex'), summary, entries }, null, 1));
    console.log(`${out}: ${summary.cells} cells, traceable ${summary.traceable} (${(100 * summary.traceable_share).toFixed(1)}%) - `
      + `exact ${summary.exact}, fuzzy ${summary.fuzzy}, value not in quote ${summary.value_not_in_quote}, `
      + `unresolved ${summary.unresolved}, missing ${summary.missing}`);
  }
})(typeof window !== 'undefined' ? window : globalThis);
