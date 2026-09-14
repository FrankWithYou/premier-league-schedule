#!/usr/bin/env node
// Render a generated schedule.html to a print-exact PDF with Chromium (Playwright).
// Chinese needs a CJK font; we inject it by file:// so no system fontconfig is required.
//
//   node render_pdf.cjs schedule.html schedule.pdf
//
// Environment overrides (defaults suit a Playwright install):
//   PW_CORE   path to a playwright-core module
//   CHROME    path to the chromium 'chrome' binary
//   CJK_REG / CJK_BOLD   .otf/.ttf files for the Chinese font (Regular/Bold)
// Set LD_LIBRARY_PATH if Chromium needs bundled libs, and TMPDIR to a SHORT
// path (Chromium's singleton socket path must stay under ~108 chars).

const PW_CORE = process.env.PW_CORE ||
  '/home/jammyang/.npm/_npx/e41f203b7505f1fb/node_modules/playwright-core';
const CHROME = process.env.CHROME ||
  '/home/jammyang/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome';
const REG = 'file://' + (process.env.CJK_REG || '/home/jammyang/.fonts/NotoSansCJKsc-Regular.otf');
const BOLD = 'file://' + (process.env.CJK_BOLD || '/home/jammyang/.fonts/NotoSansCJKsc-Bold.otf');

const pw = require(PW_CORE);
const FONTCSS = `
@font-face{font-family:'Noto Sans CJK SC';font-weight:400;src:url('${REG}');}
@font-face{font-family:'Noto Sans CJK SC';font-weight:700;src:url('${BOLD}');}
@font-face{font-family:'Noto Sans CJK SC';font-weight:800;src:url('${BOLD}');}`;

(async () => {
  const [src, out] = [process.argv[2], process.argv[3]];
  if (!src || !out) { console.error('usage: node render_pdf.cjs <in.html> <out.pdf>'); process.exit(2); }
  const path = require('path').resolve(src);
  const b = await pw.chromium.launch({ executablePath: CHROME, args: ['--no-sandbox'] });
  const p = await b.newPage();
  await p.goto('file://' + path, { waitUntil: 'networkidle' });
  await p.addStyleTag({ content: FONTCSS });
  await p.evaluate(() => document.fonts.ready);
  await p.emulateMedia({ media: 'print' });
  const over = await p.evaluate(() =>
    [...document.querySelectorAll('.week-page')].filter(s => s.getBoundingClientRect().height > 1056).length);
  await p.pdf({ path: out, preferCSSPageSize: true, printBackground: true });
  await b.close();
  console.log(`Wrote ${out}` + (over ? `  (WARNING: ${over} page(s) exceed one sheet)` : '  (every matchweek fits one sheet)'));
})().catch(e => { console.error(String(e).slice(0, 500)); process.exit(1); });
