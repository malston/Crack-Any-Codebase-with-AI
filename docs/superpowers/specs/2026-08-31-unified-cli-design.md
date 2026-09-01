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
writes `index.md` plus a self-contained `index.html`. Diffing consecutive
chapters shows the render helpers, CSS, card/section builders, and run
loop are 70-80% identical (242 of 294 lines of the ch10 renderer appear
verbatim in the ch08 renderer). The true per-chapter deltas are:

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
  match. Parity means byte-identical except for a short, explicit list of
  deliberate unifications recorded in the test itself (for example a
  unified `<title>` suffix). These tests need no LLM calls and catch
  drift the moment an analysis is ported.
- `crack all` failure isolation gets its own test: mock one analysis's
  flow to raise, assert the other five still run and the exit code is
  non-zero.
- `test_smoke.py` runs one cheap real analysis end to end against a
  fixture repo built in a tmpdir with `git init` and two commits, so the
  git-history analysis is smoke-testable too. It skips unless an API key
  is present.
- TDD applies during implementation: each extraction step lands with its
  test first.

## Port order and the ch05 escape hatch

Analyses are ported hardest-last: backend, architecture, interfaces,
schema, git-history, product-intent. The shared engine is proven on the
converged chapters (ch08-ch10 are nearly identical) before it meets the
custom ones.

ch05 is the known design risk: its renderer is 547 lines against ch10's
294, and it generates an image via `call_image`. If ch05 cannot be
expressed as a section spec plus at most two hooks, it keeps a custom
`render.py` inside its own analysis package that imports the shared
helpers. Growing the hook system until the engine becomes a framework is
the failure mode this threshold exists to prevent.

## Size estimate

Roughly 2,500 lines of package code (mostly moved from chapters and
`utils/`, deduplicated) plus roughly 400 lines of tests.

## Open items

None. Approach B was chosen over copy-and-dispatch and over a
config-driven plugin registry (YAGNI).
