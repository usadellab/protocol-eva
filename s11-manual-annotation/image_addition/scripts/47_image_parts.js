// Images in the prompt, convention a1/a2 of PLAN_images_in_prompt.md §0: the text of the prompt is unchanged, the request is cut at each
// `![alt](path)` and an image part follows it.   Pure functions, no I/O, loadable in the browser (window.Elab2ArcImageParts).
//
//   buildContent(prompt, resolve, mode)  ->  { content, report }
//     prompt   the full user prompt string (what the app sends today as `content`)
//     resolve  (alt, path) -> data URL string ("data:image/png;base64,...") or null/undefined when the image is not available
//     mode     'interleaved' (a1, default): [text up to and including the ![]() match, image, text up to the next match, image, ..., rest]
//              'appended'    (a2): [whole prompt, image 1, image 2, ...] in order of appearance
//   content  OpenAI-compatible parts array [{type:'text',text}, {type:'image_url',image_url:{url}}, ...]; no empty text parts;
//            when no image resolves, a plain string (the unchanged text-only request) is returned
//   report   { images: [{index, alt, path, line, resolved}], unresolved: [...], textOnly }
// Invariant (checked in 47_image_parts.test.js): the text parts, concatenated, equal the prompt byte for byte.
(function (root) {
  const IMG = /!\[([^\]]*)\]\(([^)]*)\)/g;

  function buildContent(prompt, resolve, mode) {
    mode = mode || 'interleaved';
    if (mode !== 'interleaved' && mode !== 'appended') throw new Error('unknown mode ' + mode);
    const images = [];
    const parts = [];
    let last = 0;
    for (const m of prompt.matchAll(IMG)) {
      const url = resolve(m[1], m[2]);
      const line = prompt.slice(0, m.index).split('\n').length;
      images.push({ index: images.length, alt: m[1], path: m[2], line, resolved: !!url });
      if (!url) continue;
      const end = m.index + m[0].length;
      if (mode === 'interleaved') {
        if (end > last) parts.push({ type: 'text', text: prompt.slice(last, end) });
        last = end;
      }
      parts.push({ type: 'image_url', image_url: { url } });
    }
    const report = { images, unresolved: images.filter(i => !i.resolved), textOnly: !images.some(i => i.resolved) };
    if (report.textOnly) return { content: prompt, report };
    if (mode === 'interleaved') {
      if (last < prompt.length) parts.push({ type: 'text', text: prompt.slice(last) });
      return { content: parts, report };
    }
    return { content: [{ type: 'text', text: prompt }, ...parts], report };
  }

  const api = { buildContent, IMG_PATTERN: IMG.source };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.Elab2ArcImageParts = api;
})(typeof window !== 'undefined' ? window : globalThis);
