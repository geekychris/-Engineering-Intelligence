# Engineering Intelligence

**A Quantitative Framework for Measuring, Understanding, and Optimizing Modern Software Engineering**

_Engineering Intelligence_ is a publication-length AsciiDoc book about measuring software engineering as a socio-technical and economic system. It connects engineering economics, human attention, architecture, queueing, causal inference, AI-assisted development, governance, portfolio decisions, and organizational learning.

The master publication file is [`book.adoc`](book.adoc). Authoring, evidence, metric, instrumentation, diagram, and review conventions are defined in [`CONTRIBUTING.adoc`](CONTRIBUTING.adoc).

## Book structure

- `frontmatter/` — executive summary and reader’s guide
- `chapters/` — Chapters 1–18 and their research-foundation sidecars
- `appendices/` — reference models, standards, templates, architecture, bibliography, and maturity guidance
- `figures/mermaid/` — Mermaid diagram sources
- `scripts/build.sh` — validation and publication pipeline
- `build/` — generated HTML, PDF, diagrams, and manifest

Each chapter-level source-note file distinguishes established research from original _Engineering Intelligence_ synthesis. Bibliography anchors are maintained in `appendices/i-evidence-base-and-bibliography.adoc`.

## Prerequisites

A local build requires:

- Ruby 3.x
- Bundler
- Node.js 20 or later
- npm/npx
- Python 3
- Chromium or another browser usable by Mermaid CLI

On macOS, Chromium may be installed through Homebrew:

```bash
brew install --cask chromium
```

Set `PUPPETEER_EXECUTABLE_PATH` when Mermaid CLI cannot locate the browser automatically.

## Install dependencies

```bash
bundle install
npm install
```

The Mermaid CLI dependency is pinned in `package.json`. Ruby publication dependencies are declared in `Gemfile`.

## Build the book

Build both HTML and PDF editions:

```bash
make all
```

Build and run the complete validation path:

```bash
make validate
```

Build one edition:

```bash
make html
make pdf
```

Render only Mermaid diagrams:

```bash
make diagrams
```

Remove generated output:

```bash
make clean
```

## Generated artifacts

A successful full build produces:

- `build/engineering-intelligence.html`
- `build/engineering-intelligence.pdf`
- `build/manifest.json`
- `build/figures/mermaid/*.svg`

The manifest records artifact sizes, SHA-256 digests, source commit, generation time, and diagram count.

## Validation performed

The publication pipeline checks:

- recursive AsciiDoc includes;
- complete and correctly ordered chapter/source-note pairs;
- referenced local images;
- Mermaid source references;
- unresolved bibliography-style citation anchors;
- duplicate explicit anchors;
- Asciidoctor warnings during HTML and PDF generation.

A validation failure stops publication.

## Docker build

Build the publication image:

```bash
docker build -t engineering-intelligence-book .
```

Generate the editions into a local `build` directory. On Linux, run the container with the host user and group so the unprivileged publication process can write to the bind mount:

```bash
mkdir -p build
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -v "$(pwd)/build:/book/build" \
  engineering-intelligence-book
```

Docker Desktop for macOS generally maps bind-mount permissions automatically; the explicit `--user` option remains safe when `id` is available.

The image itself defaults to a dedicated unprivileged `publisher` user when no user override is supplied.

## Continuous integration

`.github/workflows/publish-book.yml` builds and validates the book for:

- pushes to `main`;
- pull requests;
- manually dispatched runs;
- version tags matching `v*`.

Normal builds have read-only repository access. Tagged builds publish the generated HTML, PDF, and manifest to a GitHub release using a separate least-privilege release job.

## Creating a release

After the `main` build is successful, create and push a version tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

The workflow validates the source, uploads a workflow artifact, and attaches the publication editions to the tagged GitHub release.

## Editing conventions

- Keep each top-level chapter or appendix in its own `.adoc` file.
- Add chapter research foundations in a matching `*-source-notes.adoc` sidecar.
- Use stable explicit bibliography anchors such as `[[forsgren2018]]`.
- Reference bibliography entries with AsciiDoc cross-references such as `<<forsgren2018>>`.
- Mark emerging evidence, standards, practitioner synthesis, and original constructs honestly.
- Preserve null, negative, and contradictory evidence where relevant.
- Add diagrams as Mermaid source under `figures/mermaid/` and reference the `.mmd` file from AsciiDoc; the build converts it to SVG.

See [`CONTRIBUTING.adoc`](CONTRIBUTING.adoc) for the complete publication workflow and review checklist.

## Publication status

The manuscript contains eighteen chapters, eleven appendices, a curated evidence base, chapter-level research notes, diagrams, and automated HTML/PDF publication tooling.
