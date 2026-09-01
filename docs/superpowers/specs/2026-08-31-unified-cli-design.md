# Unified CLI: one `crack` command for the six chapter analyses

**Date:** 2026-08-31
**Status:** Approved design, pending implementation plan
**Branch:** `feat/unified-cli`

## Goal

Collapse the six chapter workflows (ch05-ch10) into a single installable
package under `src/` with one executable CLI named `crack`. The chapter
folders stay untouched; they remain the book's teaching material. `src/`
is the living, deduplicated version of the same behavior.

## Non-goals

- No changes to any `ch*` folder.
- No wrapping of the ch02/ch04 scripts or the ch03 base workflow.
- No plugin system or config-file-driven analyses. Six fixed analyses.
- No backward compatibility shims for the per-chapter entry points.

## What the chapters share (measured)

Each chapter workflow is the same PocketFlow skeleton: a crawl step builds
a text bundle, LLM nodes fill prompts against that bundle, and a renderer
writes `index.md` plus a self-contained `index.html`. That skeleton, the
node plumbing, and the `utils/` helpers are shared by all six.

The renderers split into two families (see "Two renderer families"
below). Within the card family the overlap is large: 242 of the 294 lines
of the ch10 renderer appear verbatim in the ch08 renderer, and the
`_card`, `_section`, and `_intro` helpers are byte-identical across all
four. The true per-chapter deltas are:

1. the crawl/bundle helper,
2. the node classes and their prompt files,
3. the section layout of the report,
4. a few analysis-specific CLI flags.

## Package layout

```text
pyproject.toml              # package "crack-codebase", console script "crack"
src/crack/
  __init__.py
  cli.py                    # argparse: six analysis subcommands + "all"
  core/
    call_llm.py             # copied from utils/ (see "Relationship to utils/")
    llm.py                  # read_prompt, fill, extract_mermaid, yaml/json calls
    crawl.py                # crawl, list_files, safe_read, defaults
    overview.py             # page-overview writer
    nodes.py                # OverviewNode
    render.py               # shared renderer: md/html helpers, CSS, cards,
                            # sections, page shell, welcome/intro blocks
    runner.py               # run one analysis: flow.run(shared) -> write
                            # index.md + index.html into the output dir
  analyses/
    __init__.py             # registry: name -> analysis module
    product_intent/
    git_history/
    schema/
    interfaces/
    architecture/
    backend/
      # each package contains:
      #   nodes.py          node classes + overview_spec + build_flow()
      #   <crawl helper>.py gitlog.py / schema_find.py / routes_find.py /
      #                     arch_crawl.py / backend_crawl.py / (ch05: crawl args)
      #   sections.py       section spec consumed by core/render.py
      #   prompts/*.md      copied verbatim from the chapter's prompts/
tests/
  test_render.py            # card splitting, section building, html shell
  test_crawl.py             # include/exclude, size caps, skip dirs
  test_cli.py               # dispatch, output paths, flag wiring
  test_sections.py          # each analysis's section spec renders
  test_smoke.py             # one real end-to-end run; skipped without API key
```

## Analysis module interface

Every analysis package exposes the same surface:

```python
NAME: str            # subcommand name, e.g. "backend"
TITLE: str           # report title fragment
def build_flow() -> pocketflow.Flow
def overview_spec(shared: dict) -> dict      # consumed by OverviewNode
SECTIONS: list[Section]                       # consumed by core/render.py
def add_arguments(parser) -> None             # analysis-specific flags, optional
def init_shared(args, out_dir: str) -> dict   # build the flow's shared dict
ENV_DEFAULTS: dict[str, str]                  # e.g. LLM_MAX_OUTPUT_TOKENS
```

`init_shared` exists because some analyses need more in `shared` than the
repo path. ch05 needs `pain_image_path_target` set to `<out_dir>/pain.png`
before the flow runs, since one node writes a generated image there; ch06
needs its `--max-graves` and `--grave-min-files` values; ch07 needs
`--schema`. The default implementation returns `{"repo_path": args.repo_path}`.
Analyses may write extra files into `out_dir` beyond `index.md` and
`index.html`; the `crack all` index page links the report, not the extras.

`Section` is a small dataclass in `core/render.py`: number, label, note,
rail class, the shared-state key holding the markdown, and an optional
card-splitting or chart hook. The per-chapter `render_html` /
`render_markdown` functions collapse into this declaration plus the
shared engine. Where a chapter has a genuinely custom render step (the
ch08 group chart, the ch05 pain illustration), the section spec carries a
hook function; the engine calls it.

## CLI behavior

```text
crack product-intent <repo> [--out DIR] [--include GLOB]... [--exclude GLOB]...
crack git-history    <repo> [--out DIR] [--max-graves N] [--grave-min-files N]
crack schema         <repo> [--out DIR] [--schema PATH]
crack interfaces     <repo> [--out DIR]
crack architecture   <repo> [--out DIR]
crack backend        <repo> [--out DIR]
crack all            <repo> [--out DIR]
```

- Per-analysis flags come verbatim from each chapter's `main.py`
  (measured above); `add_arguments` wires them.
- Default output root: `./crack-output/<repo-name>/`. Each analysis
  writes `<root>/<analysis>/index.md` and `index.html`.
- `crack all` runs the six analyses sequentially, then writes
  `<root>/index.html`: a small page that links the six reports and shows
  each one's overview line. A failed analysis does not abort the run;
  `all` reports it at the end and exits non-zero.
- API keys come from the environment exactly as today
  (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GEMINI_API_KEY`).
- The `LLM_MAX_OUTPUT_TOKENS` default of `32768` set by ch08, ch09, and
  ch10 moves into those three analyses' `ENV_DEFAULTS` (empty for the
  other three, which use the `16384` fallback in `call_llm.py`). The
  runner sets each default before the analysis runs and restores the
  prior environment after, so one analysis's default never leaks into
  the next under `crack all`. A value already set by the user always
  wins.

## Relationship to `utils/`

Root `utils/` stays as-is because the chapter folders import it. `src/
crack/core/` receives a copy of its five modules so the package is
self-contained and installable. This duplication is deliberate: the
chapters are frozen teaching snapshots; `src/` is the maintained code.

`utils/` is already a package with relative imports and no `sys.path`
manipulation, so the copy is close to verbatim. The `sys.path.insert`
lines live in the chapter files, not in `utils/`; the ported analysis
modules drop them and import from `crack.core` instead.

## Packaging

- `pyproject.toml` with setuptools, `src` layout,
  `[project.scripts] crack = "crack.cli:main"`.
- Dependencies: `pocketflow`, `pyyaml`, `markdown-it-py`, `pathspec`
  (used by `crawl.py`), plus optional extras for the provider SDKs
  (`anthropic`, `openai`, `google-genai`) matching what
  `utils/call_llm.py` imports.
- Python version: `requires-python = ">=3.10"`.
- Dev install: `pip install -e ".[dev]"` (dev extra adds pytest).

## Error handling

- Keep the chapters' assertion style inside nodes (retries handled by
  `Node(max_retries=3, wait=2)`).
- `cli.py` validates the repo path before any LLM call and prints the
  failing analysis's name on error.
- `crack all` isolates failures per analysis as described above.

## Testing

- Unit tests need no network: renderer, crawl, CLI dispatch, section
  specs, the `all` index page.
- **Parity tests are the core check that this refactor preserves
  behavior.**
  The chapter renderers are pure functions of a `shared` dict. For each
  ported analysis, a fixture `shared` dict feeds both the chapter's
  `render_html`/`render_markdown` and the new engine; the outputs must
  match. Parity means byte-identical after applying the "Deliberate
  unifications" list below, which each parity test names explicitly so no
  difference passes unnoticed. These tests need no LLM calls and catch
  drift the moment an analysis is ported. For ch05 and ch06, whose
  renderers are ported nearly verbatim, parity is byte-identical with no
  exceptions.
- `crack all` failure isolation gets its own test: mock one analysis's
  flow to raise, assert the other five still run and the exit code is
  non-zero.
- `test_smoke.py` runs one cheap real analysis end to end against a
  fixture repo built in a tmpdir with `git init` and two commits, so the
  git-history analysis is smoke-testable too. It skips unless an API key
  is present.
- TDD applies during implementation: each extraction step lands with its
  test first.

## Two renderer families (measured)

A file-by-file survey of the six renderers found two families, not one.

**The card family — ch07, ch08, ch09, ch10.** These four share the
`split_cards` → `_card` → `_section` engine. Their `_card`, `_section`,
and `_intro` helpers are byte-identical. Their `<body>` markup is
byte-identical apart from the hero eyebrow and the footer line. These
four are what the shared engine serves.

**The bespoke family — ch05, ch06.** These two hand-build their whole
page from structured dicts rather than markdown blobs. ch05 has no
`.rail`, `.card`, `.card-top`, `.sec-head`, or `.intro` at all; it has
`.pain-card`, `.two-col`, `table.matrix`, and `.card-rail`, plus the only
filesystem touch in any renderer (embedding `pain.png`). ch06 hardcodes
its three sections in the template, builds three different card types
(`_era_card`, `_profile_card`, `_grave_card`), and renders a coloured
flex timeline instead of a Mermaid diagram. Neither reads
`shared["overview"]` the way the card family does; ch05 has no
welcome/intros concept at all.

The escape hatch defined earlier for ch05 therefore fires for ch06 as
well. Both keep a custom `render.py` inside their own analysis package,
importing the shared `md`, `md_rich`, `esc`, and CSS base. Forcing them
through a section spec would mean growing hooks until the engine became a
framework, which is the outcome the threshold exists to prevent.

## What the shared engine parameterizes

For the card family, the per-analysis differences reduce to two
declarations.

`SECTIONS` — an ordered list of sections, each with a number, label,
note, rail class, rail width in pixels, and the `shared` key holding its
markdown. Two behaviors seen in the survey must be supported: a section
that is omitted entirely when its key is empty (ch08's tour), and a
section that renders a "skipped" head with no rail (ch07's migration
history). ch08 also needs the one existing `prefix_html` hook, which
hoists a Mermaid diagram above the rail and renders a single hand-built
card.

`THEME` — the palette and copy that differ per analysis: accent and
accent-soft colours, hero gradient, eyebrow colour and text, hero
subtitle colour, `<title>` suffix, footer template, and the hero prefix
block (an ERD for ch07, a computed bar chart for ch08, a Mermaid diagram
for ch09 and ch10).

## Deliberate unifications

The survey found small CSS differences among ch07-ch10 that read as drift
rather than intent. The engine unifies these; each parity test names the
list explicitly so no difference passes unnoticed.

- `.card` max-height: `72vh` (ch07/08/09) and `74vh` (ch10) unify to `72vh`.
- `pre code` font-size: `.74rem` and `.73rem` (ch10) unify to `.74rem`.
- `.card-top` font-size: `.98rem`, `.96rem`, `.95rem` unify to `.96rem`.
- `.card-body li`: `margin .3em/.28em` and `line-height 1.55/1.5` unify to `.28em` and `1.55`.
- The `.erd` wrapper class (ch07) becomes `.diagram`, matching ch08-ch10.
- Table CSS (present in ch07/ch08, absent in ch09/ch10) is included for all four.
- The Mermaid `flowchart: { htmlLabels: true }` option (ch10 only) applies to all four.

Dead code found by the survey is dropped rather than ported:
`_welcome_html` (defined in all four, called by none), `extract_mermaid`
in ch09 and ch10 (defined, never called), and ch09's `.verdict` CSS
(no element ever carries that class).

## Port order

Analyses are ported easiest-first so the engine is proven before it meets
the bespoke pages: backend, architecture, interfaces, schema (the card
family), then git-history and product-intent (custom renderers).

## Size estimate

Roughly 3,000 lines of package code (mostly moved from chapters and
`utils/`, deduplicated) plus roughly 600 lines of tests. The estimate is
higher than a pure card-family collapse would need, because ch05 and ch06
keep their own renderers.

## Open items

None. Approach B was chosen over copy-and-dispatch and over a
config-driven plugin registry (YAGNI).
