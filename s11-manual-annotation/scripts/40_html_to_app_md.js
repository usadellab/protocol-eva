// HTML body -> markdown exactly as the elab2arc app does it (js/elab2arc-core20260504.js: `new TurndownService()` +
// `keep(['table'])`, js/turndown.js loaded from the app) plus the app's body clean-up of eLabFTW links.
// Reused by 33_eln_to_input_md.js (.eln entries) and 38_pdf_to_html.py (PDF-only entries).
//
//   node 40_html_to_app_md.js <in.html> <out.md>      (CLI; the html file is the entry body)
//   const { htmlToAppMd } = require('./40_html_to_app_md.js')
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { JSDOM } = require(path.join(__dirname, 'node_modules', 'jsdom'));

const APP_JS = path.resolve(__dirname, '..', '..', 'elab2arc', 'js');
const dom = new JSDOM('<!doctype html><html><body></body></html>');
const sandbox = { window: dom.window, document: dom.window.document, DOMParser: dom.window.DOMParser, console };
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(path.join(APP_JS, 'turndown.js'), 'utf8') + '\nthis.TurndownService = TurndownService;', sandbox);

// The app's own stripDownloadPhp() (js/elab2arc-core20260504.js), cut out of the shipped file so that this script cannot drift from the app.
// (Until 2026-10-06 the app used the greedy /app\/download\.php(.*)f=/g, which lost the first of two images on one line.)
const coreSrc = fs.readFileSync(path.join(APP_JS, 'elab2arc-core20260504.js'), 'utf8');
const stripMatch = coreSrc.match(/function stripDownloadPhp\(html\) \{[\s\S]*?\n    \}/);
if (!stripMatch) throw new Error('stripDownloadPhp not found in the app core file');
vm.runInContext(stripMatch[0] + '\nthis.stripDownloadPhp = stripDownloadPhp;', sandbox);

function htmlToAppMd(body) {
  body = sandbox.stripDownloadPhp(body);
  body = body.replace('<a href="experiments.php?', '<a target="_blank" href="https://elabftw.example.org/experiments.php?');
  body = body.replace('<a href="database.php?', '<a  target="_blank" href="https://elabftw.example.org/experiments.php?');
  const td = new sandbox.TurndownService();
  td.keep(['table']);
  return td.turndown(body);
}
module.exports = { htmlToAppMd };

if (require.main === module) {
  const [inp, out] = process.argv.slice(2);
  if (!inp || !out) { console.error('usage: node 40_html_to_app_md.js <in.html> <out.md>'); process.exit(2); }
  const md = htmlToAppMd(fs.readFileSync(inp, 'utf8'));
  fs.writeFileSync(out, md);
  console.log(out, md.length, 'chars');
}
