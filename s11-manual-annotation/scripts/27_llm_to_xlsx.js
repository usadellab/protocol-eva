// Turn one LLM extraction (elab2arc's llmData JSON) into isa.assay.xlsx with elab2arc's CURRENT local ISA
// generation (js/arctrl.bundle.js + js/modules/isa-generation-20260422-1145.js under jsdom), staged as
// processExperiment() stages it. Used to put every conversion on equal footing before scoring, so the
// score reflects the extraction, not the ISA-generation version that happened to push it.
//
//   node 27_llm_to_xlsx.js <llm.json> <protocol.md> <out.xlsx> [assayId]
// <llm.json> is either llmData itself ({samples, protocols}) or a 26_llm_extraction.js result ({llmData}).
const fs = require('fs');
const path = require('path');
const { JSDOM } = require(path.join(__dirname, 'node_modules', 'jsdom'));

const APP_JS = path.resolve(__dirname, '..', '..', 'elab2arc', 'js');
const [jsonFile, mdFile, outFile, assayId = 'assay'] = process.argv.slice(2);
if (!jsonFile || !mdFile || !outFile) {
  console.error('usage: node 27_llm_to_xlsx.js <llm.json> <protocol.md> <out.xlsx> [assayId]');
  process.exit(2);
}

(async () => {
  const w = new JSDOM('<!doctype html><html><body></body></html>', { runScripts: 'outside-only' }).window;
  w.console = { log() {}, info() {}, warn() {}, error: console.error, debug() {} };
  w.TextEncoder = TextEncoder; w.TextDecoder = TextDecoder;
  Object.defineProperty(w.document, 'currentScript', { value: { src: 'http://localhost/js/arctrl.bundle.js', tagName: 'SCRIPT' }, configurable: true });
  w.eval(fs.readFileSync(path.join(APP_JS, 'arctrl.bundle.js'), 'utf8'));
  w.memfsPathJoin = (...parts) => parts.join('/').replace(/\/+/g, '/');
  w.eval(fs.readFileSync(path.join(APP_JS, 'modules', 'isa-generation-20260422-1145.js'), 'utf8'));
  const mfs = w.FS.fs;

  const raw = JSON.parse(fs.readFileSync(jsonFile, 'utf8'));
  const llmData = raw.llmData || raw;
  if (!llmData || !Array.isArray(llmData.protocols)) throw new Error(`${jsonFile}: no llmData.protocols`);
  const base = path.basename(mdFile, '.md');
  const basePath = `arc/assays/${assayId}`;
  mfs.mkdirSync(`${basePath}/protocols`, { recursive: true });
  mfs.mkdirSync(`${basePath}/dataset`, { recursive: true });
  mfs.writeFileSync(`${basePath}/protocols/${base}.md`, new w.Uint8Array(fs.readFileSync(mdFile)));
  mfs.writeFileSync(`${basePath}/protocols/${base}.json`, JSON.stringify(llmData));
  mfs.writeFileSync(`${basePath}/dataset/README.elab2arc.md`, '# Dataset\n');
  const protocolInfo = w.Elab2ArcISA.extractProtocolInfo(`${basePath}/protocols`);
  const datasetInfo = w.Elab2ArcISA.extractDatasetInfo(`${basePath}/dataset`);
  const isaMetadata = {
    measurementType: 'eLabFTW experiment', technologyType: 'experiment', platform: 'eLabFTW',
    lastName: 'experimenter', firstName: '', familyName: '', email: '', affiliation: '',
  };
  const out = await w.Elab2ArcISA.generateIsaAssayElab2arcWithDatamap(basePath, assayId, isaMetadata, protocolInfo, datasetInfo,
    JSON.parse(JSON.stringify(llmData)));
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  fs.writeFileSync(outFile, Buffer.from(mfs.readFileSync(out)));
  const wb = await w.Xlsx.fromXlsxFile(out);
  const assay = w.arctrl.XlsxController.Assay.fromFsWorkbook(wb);
  console.log(`${outFile}: ${assay.Tables.length} tables, ${assay.Tables.reduce((n, t) => n + t.RowCount, 0)} rows`);
})().catch(e => { console.error('FAILED:', e.message || e); process.exit(1); });
