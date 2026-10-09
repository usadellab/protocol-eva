// Controls for 47_image_parts.js (phase 1 of PLAN_images_in_prompt.md). node scripts/47_image_parts.test.js (exit 1 on failure).
// Every property is checked on real inputs (the five benchmark markdowns) and each check is shown to FAIL on a deliberately broken builder.
const fs = require('fs');
const path = require('path');
const P = require('./47_image_parts.js');
const ROOT = path.resolve(__dirname, '..', '..');                        // root of the section s11-manual-annotation
let failed = 0;
const check = (name, ok, detail) => { console.log((ok ? 'ok   ' : 'FAIL ') + name + (ok ? '' : '  ' + (detail || ''))); if (!ok) failed++; };
const fake = (alt, p) => 'data:image/png;base64,' + Buffer.from(p).toString('base64');   // the data URL encodes the path: order and identity are checkable
const textOf = c => c.filter(p => p.type === 'text').map(p => p.text).join('');
const imgsOf = c => c.filter(p => p.type === 'image_url').map(p => Buffer.from(p.image_url.url.split(',')[1], 'base64').toString());

// properties, parameterised by the builder so a broken builder can be run through the same checks
function properties(build, label) {
  const results = [];
  const cases = { phage: 1, sdy1: 2, biolector034: 2, ux511: 7, pux782: 1 };
  for (const [c, n] of Object.entries(cases)) {
    const md = fs.readFileSync(path.join(ROOT, 'datasets/protocol_inputs', c + '.md'), 'utf8');
    const prompt = 'PROMPT HEAD\n' + md + '\nPROMPT TAIL';
    const expected = [...prompt.matchAll(/!\[([^\]]*)\]\(([^)]*)\)/g)].map(m => m[2]);
    for (const mode of ['interleaved', 'appended']) {
      const { content, report } = build(prompt, fake, mode);
      const ok = Array.isArray(content);
      results.push([`${label} ${c} ${mode}: ${n} images -> parts array`, ok && report.images.length === n && imgsOf(content).length === n]);
      results.push([`${label} ${c} ${mode}: text parts concatenate to the prompt byte for byte`, ok && textOf(content) === prompt]);
      results.push([`${label} ${c} ${mode}: images in order of appearance`, ok && JSON.stringify(imgsOf(content)) === JSON.stringify(expected)]);
      results.push([`${label} ${c} ${mode}: no empty text part`, ok && content.every(p => p.type !== 'text' || p.text.length > 0)]);
      if (mode === 'interleaved') {
        // each image part directly follows the text that ends with its own ![]() line
        const okPos = ok && content.every((p, i) => p.type !== 'image_url' || (content[i - 1] && content[i - 1].type === 'text' ? /\)$/.test(content[i - 1].text) : content[i - 1] && content[i - 1].type === 'image_url'));
        results.push([`${label} ${c} interleaved: every image sits right after its ![]() match`, okPos]);
      } else {
        results.push([`${label} ${c} appended: first part is the unchanged prompt`, ok && content[0].text === prompt]);
      }
    }
  }
  return results;
}

// 1. the real builder passes everything
for (const [name, ok] of properties(P.buildContent, 'builder')) check(name, ok);

// 2. every ![]() line is resolved or reported
{
  const prompt = 'a\n![x.png](p/x.png)\nb ![y.png](p/y.png)![z.png](p/z.png) c\n';
  const r = P.buildContent(prompt, (alt, p) => (p === 'p/y.png' ? null : fake(alt, p)), 'interleaved');
  check('unresolved image is reported with alt, path, line', r.report.unresolved.length === 1 && r.report.unresolved[0].path === 'p/y.png' && r.report.unresolved[0].line === 3);
  check('unresolved image gets no image part, text still complete', textOf(r.content) === prompt && imgsOf(r.content).join() === 'p/x.png,p/z.png');
  check('two images on one line (the UX511 case) both survive', imgsOf(P.buildContent('![a.png](p/a.png)![b.png](p/b.png)', fake).content).join() === 'p/a.png,p/b.png');
  const none = P.buildContent(prompt, () => null);
  check('no image resolves -> unchanged string (text-only request)', none.content === prompt && none.report.textOnly === true);
  check('no ![]() at all -> unchanged string', P.buildContent('plain text', fake).content === 'plain text');
  let threw = false; try { P.buildContent(prompt, fake, 'sideways'); } catch (e) { threw = true; }
  check('unknown mode throws', threw);
}

// 3. each check fails on a deliberately broken builder
const broken = {
  'drops the last text': (p, r, m) => { const x = P.buildContent(p, r, m); if (Array.isArray(x.content)) x.content = x.content.slice(0, -1); return x; },
  'reverses the images': (p, r, m) => { const x = P.buildContent(p, (a, q) => r(a, q), m); if (Array.isArray(x.content)) { const im = x.content.filter(t => t.type === 'image_url').reverse(); let i = 0; x.content = x.content.map(t => t.type === 'image_url' ? im[i++] : t); } return x; },
  'inserts a caption': (p, r, m) => P.buildContent(p.replace(/(!\[[^\]]*\]\([^)]*\))/, '$1\nFigure 1'), r, m),
  'puts all images first': (p, r, m) => { const x = P.buildContent(p, r, m); if (Array.isArray(x.content)) x.content = [...x.content.filter(t => t.type === 'image_url'), ...x.content.filter(t => t.type === 'text')]; return x; },
};
for (const [what, build] of Object.entries(broken)) {
  const bad = properties(build, 'broken').filter(([, ok]) => !ok).length;
  check(`controls detect a builder that ${what} (${bad} checks fail)`, bad > 0);
}
if (failed) { console.error(failed + ' check(s) FAILED'); process.exit(1); }
console.log('47 controls OK');
