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
ENV_DEFAULTS: dict[str, str]                  # e.g. LLM_MAX_OUTPUT_TOKENS
```

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
- Each chapter's `LLM_MAX_OUTPUT_TOKENS` default moves into that
  analysis's `ENV_DEFAULTS` and applies only while it runs.

## Relationship to `utils/`

Root `utils/` stays as-is because the chapter folders import it. `src/
crack/core/` receives a copy of its five modules so the package is
self-contained and installable. This duplication is deliberate: the
chapters are frozen teaching snapshots; `src/` is the maintained code.
The copies drop the `sys.path` manipulation and use package-relative
imports.

## Packaging

- `pyproject.toml` with setuptools, `src` layout,
  `[project.scripts] crack = "crack.cli:main"`.
- Dependencies: `pocketflow`, `pyyaml`, `markdown-it-py`, plus optional
  extras for the provider SDKs (`anthropic`, `openai`,
  `google-generativeai`) matching what `utils/call_llm.py` supports.
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
- `test_smoke.py` runs one cheap real analysis end to end against a tiny
  fixture repo; it skips unless an API key is present.
- TDD applies during implementation: each extraction step lands with its
  test first.

## Size estimate

Roughly 2,500 lines of package code (mostly moved from chapters and
`utils/`, deduplicated) plus roughly 400 lines of tests.

## Open items

None. Approach B was chosen over copy-and-dispatch and over a
config-driven plugin registry (YAGNI).
