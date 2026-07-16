#!/usr/bin/env node
// Preprocess AsciiDoc source in a work dir: render every stem:[...] inline
// expression and [stem] ... ++++ block into an SVG under figures/math/ and
// rewrite the source to reference the SVG. Runs after prepare_sources so it
// only touches the build copies.

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const {mathjax} = require('mathjax-full/js/mathjax.js');
const {TeX} = require('mathjax-full/js/input/tex.js');
const {SVG} = require('mathjax-full/js/output/svg.js');
const {liteAdaptor} = require('mathjax-full/js/adaptors/liteAdaptor.js');
const {RegisterHTMLHandler} = require('mathjax-full/js/handlers/html.js');
const {AllPackages} = require('mathjax-full/js/input/tex/AllPackages.js');

const adaptor = liteAdaptor();
RegisterHTMLHandler(adaptor);
const tex = new TeX({packages: AllPackages, inlineMath: [], displayMath: []});
const svgOut = new SVG({fontCache: 'none'});
const doc = mathjax.document('', {InputJax: tex, OutputJax: svgOut});

const workDir = process.argv[2];
if (!workDir) {
  console.error('usage: render-math.js <work-dir>');
  process.exit(1);
}

const mathDir = path.join(workDir, 'figures', 'math');
fs.mkdirSync(mathDir, {recursive: true});

const cache = new Map();

// MathJax outputs dimensions in ex units. prawn-svg's default ex resolution
// is larger than the surrounding body text, so equations render 2-3x too big.
// Match asciidoctor-pdf's default 10.5pt body font: 1em = 10.5pt, 1ex ~ 0.5em.
const PT_PER_EX = 10.5 * 0.5;

function convertExAttribute(svg, attr) {
  const re = new RegExp(`(\\s${attr}=")([0-9.]+)ex(")`);
  return svg.replace(re, (_, pre, num, post) =>
    `${pre}${(parseFloat(num) * PT_PER_EX).toFixed(3)}pt${post}`
  );
}

function render(source, display) {
  const key = display + '|' + source;
  if (cache.has(key)) return cache.get(key);

  const node = doc.convert(source, {display});
  let svg = adaptor.innerHTML(node);
  const match = svg.match(/<svg[\s\S]*<\/svg>/);
  if (!match) {
    throw new Error('MathJax did not return an SVG for: ' + source);
  }
  svg = match[0];
  if (!/\sxmlns=/.test(svg.slice(0, svg.indexOf('>')))) {
    svg = svg.replace(/^<svg\b/, '<svg xmlns="http://www.w3.org/2000/svg"');
  }
  svg = convertExAttribute(svg, 'width');
  svg = convertExAttribute(svg, 'height');

  const hash = crypto.createHash('sha1').update(key).digest('hex').slice(0, 12);
  const name = (display ? 'block-' : 'inline-') + hash + '.svg';
  const outPath = path.join(mathDir, name);
  fs.writeFileSync(outPath, svg, 'utf8');
  const rel = path.posix.join('figures', 'math', name);
  cache.set(key, rel);
  return rel;
}

const inlineRe = /stem:\[((?:\\.|[^\\\]])*)\]/g;
const blockRe = /^\[stem\]\r?\n\+\+\+\+\r?\n([\s\S]*?)\r?\n\+\+\+\+\s*$/gm;

function walk(dir) {
  for (const entry of fs.readdirSync(dir, {withFileTypes: true})) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else if (entry.isFile() && entry.name.endsWith('.adoc')) processFile(full);
  }
}

function processFile(file) {
  let text = fs.readFileSync(file, 'utf8');
  let dirty = false;

  text = text.replace(blockRe, (_, body) => {
    const rel = render(body.trim(), true);
    dirty = true;
    return `image::${rel}[role="math-block"]`;
  });

  text = text.replace(inlineRe, (_, body) => {
    const rel = render(body.trim(), false);
    dirty = true;
    return `image:${rel}[role="math-inline"]`;
  });

  if (dirty) fs.writeFileSync(file, text, 'utf8');
}

walk(workDir);
console.log(`Rendered ${cache.size} math expressions to ${mathDir}`);
