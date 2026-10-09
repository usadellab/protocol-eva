// Run elab2arc's own LLM extraction (Elab2ArcLLM.callTogetherAI from an llm-service module file) headless
// under jsdom, on a given protocol markdown, with the same metadata processExperiment() passes.
// Provider "dataplan" (h.dataplan.top, DeepSeek-V4-Flash, no API key), as in the deployed app.
//
//   node 26_llm_extraction.js <llm-service.js> <protocol.md> <out.json> [assayId]
//   DRY=1 ...  capture the exact request (prompt + parameters) into <out.json> without calling the LLM
//   MODEL=<id> ...  send the identical prompt to another model on the same endpoint. The app builds the request
//                   for its hard-wired DeepSeek model (temperature 1.0, top_p 0.95, repetition_penalty 1.1,
//                   enable_thinking false, max_tokens 28000); for another model those keys are removed and the
//                   model's own settings from PARAMS_FILE (default work/eval/model_params.json, taken from the
//                   model cards) are applied instead. A model without an entry is refused.
//   ENDPOINT=<url> ...  send the request to another OpenAI-compatible endpoint (e.g. a local oMLX server,
//                   http://127.0.0.1:8082/v1/chat/completions) and ask it for token usage in the stream
//                   (stream_options.include_usage); the usage is recorded in <out.json>.
//
// Browser-only details handled here: the forbidden "Host" header (a browser drops it) and the jsdom
// AbortSignal (not accepted by Node's fetch) are removed before the request is sent.
const fs = require('fs');
const path = require('path');
const { JSDOM } = require(path.join(__dirname, 'node_modules', 'jsdom'));

const [moduleFile, mdFile, outFile, assayId = 'assay'] = process.argv.slice(2);
if (!moduleFile || !mdFile || !outFile) {
  console.error('usage: node 26_llm_extraction.js <llm-service.js> <protocol.md> <out.json> [assayId]');
  process.exit(2);
}
const protocolFilename = path.basename(mdFile);
const PARAMS_FILE = process.env.PARAMS_FILE || path.join(__dirname, '..', 'work', 'eval', 'model_params.json');
const MODEL_PARAMS = fs.existsSync(PARAMS_FILE) ? JSON.parse(fs.readFileSync(PARAMS_FILE, 'utf8')) : {};
const metadata = { protocolFilename, protocolPath: `assays/${assayId}/protocols/${protocolFilename}`, assayId };

// usage object of a streamed response (last "usage" chunk), or null when the server sent none
function streamUsage(raw) {
  const lines = raw.split('\n').filter(l => l.startsWith('data: {') && l.includes('"usage"'));
  return lines.length ? JSON.parse(lines[lines.length - 1].slice(6)).usage : null;
}

(async () => {
  const w = new JSDOM('<!doctype html><html><body></body></html>', { runScripts: 'outside-only', url: 'http://127.0.0.1:8000/elab2arc/' }).window;
  w.console = { log() {}, info() {}, debug() {}, warn: (...a) => console.warn('[llm warn]', ...a), error: (...a) => console.error('[llm error]', ...a) };
  w.TextEncoder = TextEncoder; w.TextDecoder = TextDecoder;
  w.localStorage.setItem('llmApiProvider', 'dataplan');
  const requests = [];
  let imageReport = null;
  w.fetch = async (url, opts = {}) => {
    const headers = { ...(opts.headers || {}) };
    for (const h of Object.keys(headers)) if (h.toLowerCase() === 'host') delete headers[h];
    const body = opts.body ? JSON.parse(opts.body) : null;
    if (body && process.env.MODEL) {
      body.model = process.env.MODEL;
      if (!process.env.MODEL.toLowerCase().includes('deepseek')) {
        const params = MODEL_PARAMS[process.env.MODEL];
        if (!params) throw new Error(`no settings for ${process.env.MODEL} in ${PARAMS_FILE}`);
        for (const k of ['temperature', 'top_p', 'repetition_penalty', 'enable_thinking', 'reasoning_effort', 'max_tokens']) delete body[k];
        Object.assign(body, params);
      }
    }
    if (body && process.env.ENDPOINT) {
      url = process.env.ENDPOINT;
      body.stream_options = { include_usage: true };
    }
    if (body && process.env.IMAGES) {      // images in the prompt (PLAN_images_in_prompt.md): IMAGES=interleaved|appended, IMAGE_DIR = dir with manifest.json (default <entry dir>/images)
      const { buildContent } = require('./47_image_parts.js');
      const dir = process.env.IMAGE_DIR || path.join(path.dirname(path.dirname(path.resolve(mdFile))), 'images');
      const manifest = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json'), 'utf8'));
      const byPath = Object.fromEntries(manifest.map(m => [m.path, path.join(path.dirname(dir), m.file.startsWith('images/') ? path.basename(dir) + '/' + path.basename(m.file) : m.file)]));
      const resolve = (alt, p) => byPath[p] && fs.existsSync(byPath[p]) ? 'data:image/png;base64,' + fs.readFileSync(byPath[p]).toString('base64') : null;
      const msg = body.messages.find(m => typeof m.content === 'string' && /!\[[^\]]*\]\([^)]*\)/.test(m.content));
      if (!msg) throw new Error('IMAGES set but no message contains an image line');
      const built = buildContent(msg.content, resolve, process.env.IMAGES);
      if (built.report.unresolved.length) throw new Error('IMAGES: unresolved images ' + JSON.stringify(built.report.unresolved.map(i => i.path)));
      msg.content = built.content;
      imageReport = built.report;
    }
    if (process.env.OPENROUTER_KEY) headers.Authorization = 'Bearer ' + process.env.OPENROUTER_KEY;   // free OpenRouter models; the key comes from the environment only, never stored in a result
    if (!process.env.DRY && /dataplan\.top|together\.(ai|xyz)/i.test(String(url)) && process.env.ALLOW_TOGETHER !== '1')
      throw new Error('BLOCKED: ' + url + ' is billed to together.ai. Never used without the user\'s explicit instruction (set ALLOW_TOGETHER=1 only then).');
    requests.push({ url, body });
    if (process.env.DRY) throw new Error('DRY run: request captured, not sent');
    const response = await fetch(url, { method: opts.method, headers, body: JSON.stringify(body) });
    // keep the raw (streamed) response of every request, to diagnose output the app cannot parse
    response.clone().text().then(t => raws.push(t)).catch(e => raws.push(`<unreadable: ${e.message}>`));
    return response;
  };
  const raws = [];
  w.eval(fs.readFileSync(moduleFile, 'utf8'));
  const markdown = fs.readFileSync(mdFile, 'utf8');
  const t0 = Date.now();
  let llmData = null, error = null;
  try {
    llmData = await w.Elab2ArcLLM.callTogetherAI(markdown, false, metadata);
  } catch (e) {
    error = e.message;
  }
  const last = requests[requests.length - 1];
  const result = {
    module: moduleFile, input: mdFile, metadata, seconds: Math.round((Date.now() - t0) / 1000),
    request: last ? { url: last.url, model: last.body.model, temperature: last.body.temperature, top_p: last.body.top_p,
      max_tokens: last.body.max_tokens,
      settings: Object.fromEntries(Object.entries(last.body).filter(([k]) => !['messages', 'stream'].includes(k))),
      prompt: last.body.messages.map(m => typeof m.content === 'string' ? m.content : m.content.map(c => c.type === 'text' ? c.text : '<image>').join('')).join('\n---\n') } : null,
    images: imageReport ? { mode: process.env.IMAGES, count: imageReport.images.length } : null,
    requests: requests.length, usage: raws.map(streamUsage), error, llmData,
  };
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  raws.forEach((t, i) => fs.writeFileSync(outFile.replace(/\.json$/, `.raw${i + 1}.txt`), t));
  fs.writeFileSync(outFile, JSON.stringify(result, null, 2));
  const p = llmData && llmData.protocols ? llmData.protocols.length : 0;
  console.log(`${process.env.DRY ? 'DRY ' : ''}${outFile}: ${requests.length} request(s), model ${result.request && result.request.model}, `
    + `temperature ${result.request && result.request.temperature}, ${p} protocols, ${result.seconds}s${error ? ', error: ' + error : ''}`);
})();
