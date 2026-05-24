import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { basename, join } from 'node:path';

const docsDir = new URL('../docs/hermes/', import.meta.url);
const outFile = new URL('../docs/hermes/index.html', import.meta.url);

const files = readdirSync(docsDir)
  .filter((file) => file.endsWith('.md') && file !== 'README.md')
  .sort();

function escapeHtml(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

function slugify(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function inlineMarkdown(value) {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
}

function renderMarkdown(markdown, fileId) {
  const lines = markdown.split(/\r?\n/);
  const html = [];
  let paragraph = [];
  let list = [];
  let inCode = false;
  let codeLines = [];

  const flushParagraph = () => {
    if (!paragraph.length) return;
    html.push(`<p>${inlineMarkdown(paragraph.join(' '))}</p>`);
    paragraph = [];
  };

  const flushList = () => {
    if (!list.length) return;
    html.push('<ul>');
    for (const item of list) {
      html.push(`<li>${inlineMarkdown(item)}</li>`);
    }
    html.push('</ul>');
    list = [];
  };

  for (const line of lines) {
    if (line.startsWith('```')) {
      if (inCode) {
        html.push(`<pre><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`);
        codeLines = [];
        inCode = false;
      } else {
        flushParagraph();
        flushList();
        inCode = true;
      }
      continue;
    }

    if (inCode) {
      codeLines.push(line);
      continue;
    }

    const heading = line.match(/^(#{1,4})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      flushList();
      const level = heading[1].length;
      const text = heading[2].trim();
      const id = `${fileId}-${slugify(text)}`;
      html.push(`<h${level} id="${id}">${inlineMarkdown(text)}</h${level}>`);
      continue;
    }

    const bullet = line.match(/^\s*[-*]\s+(.+)$/);
    if (bullet) {
      flushParagraph();
      list.push(bullet[1].trim());
      continue;
    }

    if (!line.trim()) {
      flushParagraph();
      flushList();
      continue;
    }

    paragraph.push(line.trim());
  }

  flushParagraph();
  flushList();

  return html.join('\n');
}

function titleFromMarkdown(markdown, file) {
  const firstHeading = markdown.match(/^#\s+(.+)$/m);
  return firstHeading ? firstHeading[1].trim() : basename(file, '.md');
}

const documents = files.map((file) => {
  const markdown = readFileSync(join(docsDir.pathname, file), 'utf8');
  const fileId = basename(file, '.md');
  return {
    file,
    id: fileId,
    title: titleFromMarkdown(markdown, file),
    html: renderMarkdown(markdown, fileId),
  };
});

const generatedAt = new Date().toISOString();

const content = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Hermes Core Documentation</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f5ef;
      --panel: #ffffff;
      --ink: #181a1f;
      --muted: #626975;
      --line: #d8d3c8;
      --accent: #1d6f78;
      --accent-ink: #0e3e45;
      --code-bg: #101419;
      --code-ink: #edf2f7;
      --warn: #a45214;
    }

    * {
      box-sizing: border-box;
    }

    html {
      scroll-behavior: smooth;
    }

    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.6;
    }

    .shell {
      display: grid;
      grid-template-columns: 300px minmax(0, 1fr);
      min-height: 100vh;
    }

    aside {
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
      border-right: 1px solid var(--line);
      background: #efebe1;
      padding: 24px 18px;
    }

    .brand {
      padding: 0 8px 18px;
      border-bottom: 1px solid var(--line);
      margin-bottom: 18px;
    }

    .brand h1 {
      margin: 0;
      font-size: 22px;
      line-height: 1.1;
      letter-spacing: 0;
    }

    .brand p {
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 13px;
    }

    nav a {
      display: block;
      color: var(--accent-ink);
      text-decoration: none;
      padding: 8px;
      border-radius: 6px;
      font-size: 14px;
    }

    nav a:hover,
    nav a:focus {
      background: rgba(29, 111, 120, 0.1);
      outline: none;
    }

    main {
      padding: 40px min(6vw, 72px) 80px;
    }

    .hero {
      max-width: 980px;
      margin: 0 0 36px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 28px;
    }

    .hero .eyebrow {
      margin: 0 0 10px;
      color: var(--accent);
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
    }

    .hero h2 {
      margin: 0;
      font-size: clamp(34px, 5vw, 68px);
      line-height: 0.95;
      letter-spacing: 0;
      max-width: 900px;
    }

    .hero p {
      max-width: 760px;
      color: var(--muted);
      font-size: 17px;
      margin: 18px 0 0;
    }

    .doc {
      max-width: 980px;
      padding: 28px 0 36px;
      border-bottom: 1px solid var(--line);
    }

    .doc:first-of-type {
      padding-top: 0;
    }

    h1,
    h2,
    h3,
    h4 {
      line-height: 1.15;
      letter-spacing: 0;
    }

    .doc h1 {
      font-size: 34px;
      margin: 0 0 18px;
    }

    .doc h2 {
      font-size: 24px;
      margin: 30px 0 12px;
    }

    .doc h3 {
      font-size: 19px;
      margin: 24px 0 10px;
    }

    .doc h4 {
      font-size: 16px;
      margin: 20px 0 8px;
    }

    p,
    li {
      font-size: 15.5px;
    }

    p {
      margin: 12px 0;
    }

    ul {
      margin: 10px 0 16px;
      padding-left: 22px;
    }

    code {
      font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
      font-size: 0.92em;
    }

    p code,
    li code {
      background: rgba(24, 26, 31, 0.08);
      border: 1px solid rgba(24, 26, 31, 0.08);
      border-radius: 4px;
      padding: 1px 5px;
    }

    pre {
      margin: 14px 0 20px;
      background: var(--code-bg);
      color: var(--code-ink);
      padding: 16px;
      border-radius: 8px;
      overflow: auto;
      border: 1px solid #222b35;
    }

    pre code {
      font-size: 13px;
      line-height: 1.55;
      white-space: pre;
    }

    .meta {
      margin-top: 20px;
      color: var(--muted);
      font-size: 12px;
    }

    @media (max-width: 860px) {
      .shell {
        display: block;
      }

      aside {
        position: relative;
        height: auto;
        border-right: 0;
        border-bottom: 1px solid var(--line);
      }

      nav {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 4px;
      }

      main {
        padding: 28px 18px 64px;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div class="brand">
        <h1>Hermes Core</h1>
        <p>Rendered documentation from Markdown sources.</p>
      </div>
      <nav aria-label="Documentation sections">
        ${documents.map((doc) => `<a href="#${doc.id}">${escapeHtml(doc.title)}</a>`).join('\n        ')}
      </nav>
      <p class="meta">Generated ${escapeHtml(generatedAt)} from docs/hermes/*.md.</p>
    </aside>
    <main>
      <section class="hero" aria-labelledby="page-title">
        <p class="eyebrow">Project Hermes</p>
        <h2 id="page-title">No-touch maintenance architecture</h2>
        <p>A browsable HTML edition of the Hermes core design docs, generated from the Markdown files in this folder.</p>
      </section>
      ${documents
        .map((doc) => `<article class="doc" id="${doc.id}" data-source="${escapeHtml(doc.file)}">\n${doc.html}\n</article>`)
        .join('\n      ')}
    </main>
  </div>
</body>
</html>
`;

writeFileSync(outFile, content);
console.log(`Rendered ${documents.length} Markdown files to ${outFile.pathname}`);
