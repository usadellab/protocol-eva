// A3: LLM input markdown for entries delivered as eLabFTW .eln exports (ro-crate; the entry's HTML body is the
// "text" property). Same conversion as the app's processExperiment() (see 07_pipeline_markdown.js): the body's
// download links are stripped to their long_name, then the app's own js/turndown.js with keep(['table'])
// (the conversion itself lives in 40_html_to_app_md.js).
// Differences from the app, recorded as a caveat: an .eln has no numeric upload id, so uploads are renamed with the
// first 8 characters of their file UUID instead of the upload id (only image links in the markdown are affected).
//
//   node 33_eln_to_input_md.js <export.eln> <title-substring> <outDir>
//   -> <outDir>/eLabFTW_protocol_<id>_<title30>.elab2arc.md   (id = the experiment id in the entry's url)
//
// HTML mode (A3b): the entry body as HTML saved from the rendered eLabFTW page (wrapper <div id="doc"><div id="body_view">):
//   node 33_eln_to_input_md.js --html <file.html> --id <elabid> --title <title> --out <outDir>
//        [--links-from-pdf <entry.pdf>]       fill empty <a href=""> from the PDF's link annotations (matched by link text, in order)
//        [--image <alt>=<file>]...            fill an empty <img src=""> whose alt is <alt>; the file is copied to
//                                             <dataset-dir>/<id>-<title20>/<name>_<sha256[:8]>.elab2arc.<ext> and linked as ../dataset/...
//        [--dataset-dir <dir>]                where the copies go (default <outDir>/../dataset)
//        [--pairs <json>]                     [{alt, rel}] renames exactly as the .eln mode does (used by the control)
//   The rendered page drops the URLs of internal links and the src of attachments; they are recovered, never invented.
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const { execFileSync } = require('child_process');
const { htmlToAppMd } = require('./40_html_to_app_md.js');
const sanitize = (t, n) => t.replace(/[^a-zA-Z0-9\s\-_]/g, '').replace(/\s+/g, '_').replace(/_{2,}/g, '_').replace(/^_|_$/g, '').substring(0, n);
const safeName = n => n.replace(/[^a-zA-Z0-9_,.\-+%$|(){}\[\]*=#?&$!^°<>;]/g, '_');
const datasetFileName = (name, uid) => { const real = safeName(name), dot = real.lastIndexOf('.');
  return dot > 0 ? `${real.slice(0, dot)}_${uid}.elab2arc${real.slice(dot)}` : `${real}_${uid}.elab2arc`; };

// shared tail of both modes: app turndown, rename of the attachments, write the file
function finish({ body, id, name, pairs, outDir }) {
  let markdown = htmlToAppMd(body);
  for (const { alt, rel } of pairs) markdown = markdown.split(alt).join(rel).split(encodeURIComponent(alt)).join(rel);
  markdown = markdown.replace(/&storage=./g, '');
  fs.mkdirSync(outDir, { recursive: true });
  const out = path.join(outDir, `eLabFTW_protocol_${id}_${sanitize(name, 30)}.elab2arc.md`);
  fs.writeFileSync(out, markdown);
  console.log(out, markdown.length, 'chars; experiment', id, JSON.stringify(name));
}

function elnMode(eln, titlePart, outDir) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'eln-'));
  execFileSync('unzip', ['-oq', eln, '-d', tmp]);
  const crateFile = (function find(d) {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const p = path.join(d, e.name);
      if (e.isDirectory()) { const r = find(p); if (r) return r; } else if (e.name === 'ro-crate-metadata.json') return p;
    }
  })(tmp);
  const graph = JSON.parse(fs.readFileSync(crateFile, 'utf8'))['@graph'];
  const entry = graph.find(e => e.genre === 'experiment' && e.name.includes(titlePart));
  if (!entry) { console.error('no experiment with title containing', titlePart, 'in', graph.filter(e => e.genre === 'experiment').map(e => e.name)); process.exit(1); }
  const files = new Map(graph.filter(e => e['@type'] === 'File').map(e => [e['@id'], e]));
  const id = new URL(entry.url).searchParams.get('id');
  const folder = `${id}-${sanitize(entry.name, 20)}`;
  const pairs = [];
  for (const part of entry.hasPart || []) {
    const f = files.get(part['@id']);
    if (!f) continue;
    pairs.push({ alt: f.alternateName, rel: `../dataset/${folder}/${datasetFileName(f.name, path.basename(f['@id']).slice(0, 8))}` });
  }
  finish({ body: entry.text || '', id, name: entry.name, pairs, outDir });
}

function htmlMode(args) {
  const opt = k => { const i = args.indexOf(k); return i < 0 ? undefined : args[i + 1]; };
  const all = k => args.flatMap((a, i) => a === k ? [args[i + 1]] : []);
  const file = opt('--html'), id = opt('--id'), title = opt('--title'), outDir = opt('--out');
  if (!file || !id || !title || !outDir) { console.error('usage: node 33_eln_to_input_md.js --html <file> --id <elabid> --title <title> --out <outDir> [...]'); process.exit(2); }
  const { JSDOM } = require(path.join(__dirname, 'node_modules', 'jsdom'));
  const doc = new JSDOM(fs.readFileSync(file, 'utf8')).window.document;
  const view = doc.getElementById('body_view');
  if (!view) { console.error('no #body_view in', file); process.exit(1); }
  const folder = `${id}-${sanitize(title, 20)}`;
  const datasetDir = opt('--dataset-dir') || path.join(outDir, '..', 'dataset');
  // internal links: the rendered page keeps the text but drops the URL; the PDF annotations still have it
  const empty = [...view.querySelectorAll('a')].filter(a => !a.getAttribute('href'));
  if (empty.length) {
    const pdf = opt('--links-from-pdf');
    if (!pdf) { console.error(empty.length, 'links without href and no --links-from-pdf'); process.exit(1); }
    const pool = JSON.parse(execFileSync('/opt/homebrew/bin/python3.13', [path.join(__dirname, '44_pdf_links.py'), pdf], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }));
    const norm = s => s.replace(/[^\p{L}\p{N}]+/gu, ' ').trim();
    for (const a of empty) {
      const k = pool.findIndex(l => norm(l.text).includes(norm(a.textContent)));
      if (k < 0) { console.error('no PDF link annotation for link text', JSON.stringify(a.textContent)); process.exit(1); }
      console.log('link', JSON.stringify(a.textContent), '->', pool[k].uri, `(PDF page ${pool[k].page})`);
      a.setAttribute('href', pool.splice(k, 1)[0].uri);
    }
  }
  // attachments: the rendered page keeps the alt (storage name) and drops the src
  const pairs = opt('--pairs') ? JSON.parse(fs.readFileSync(opt('--pairs'), 'utf8')) : [];
  for (const spec of all('--image')) {
    const [alt, src] = [spec.slice(0, spec.indexOf('=')), spec.slice(spec.indexOf('=') + 1)];
    const img = [...view.querySelectorAll('img')].find(i => i.getAttribute('alt') === alt && !i.getAttribute('src'));
    if (!img) { console.error('no <img src=""> with alt', alt); process.exit(1); }
    const uid = crypto.createHash('sha256').update(fs.readFileSync(src)).digest('hex').slice(0, 8);
    const fileName = datasetFileName(path.basename(src), uid);
    fs.mkdirSync(path.join(datasetDir, folder), { recursive: true });
    fs.copyFileSync(src, path.join(datasetDir, folder, fileName));
    const placeholder = `${alt.slice(0, 2)}/${alt}`;       // like the .eln's download name `xx/<name>`: `pairs` turns it into the dataset path, the alt stays
    img.setAttribute('src', placeholder);
    pairs.push({ alt: placeholder, rel: `../dataset/${folder}/${fileName}` });
    console.log('image', alt.slice(0, 16) + '...', '->', `../dataset/${folder}/${fileName}`);
  }
  finish({ body: view.innerHTML, id, name: title, pairs, outDir });
}

const args = process.argv.slice(2);
if (args.includes('--html')) htmlMode(args);
else {
  const [eln, titlePart, outDir] = args;
  if (!eln || !titlePart || !outDir) { console.error('usage: node 33_eln_to_input_md.js <export.eln> <title-substring> <outDir>'); process.exit(2); }
  elnMode(eln, titlePart, outDir);
}
