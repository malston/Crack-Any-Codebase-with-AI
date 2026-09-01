# Unified `crack` CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse the six chapter workflows (ch05-ch10) into one installable Python package under `src/` exposing a single `crack` command.

**Architecture:** A shared core (`crack.core`) holds the LLM wrapper, the crawler, one render engine, and a runner. Each analysis is a thin module declaring only what differs: its crawl helper, its node classes and prompts, and a `SECTIONS` list the render engine consumes. The chapter folders are never modified; they stay as the book's teaching snapshots.

**Tech Stack:** Python 3.10+, PocketFlow, markdown-it-py, pathspec, pyyaml, pytest. Provider SDKs (`anthropic`, `openai`, `google-genai`) are optional extras.

**Spec:** `docs/superpowers/specs/2026-08-31-unified-cli-design.md`

## Global Constraints

- No file under any `ch*/` directory may be created, modified, or deleted. Verify with `git status` before every commit.
- Root `utils/` is not modified. `src/crack/core/` gets its own copy.
- `requires-python = ">=3.10"`.
- Runtime dependencies: `pocketflow>=0.0.1`, `pyyaml>=6.0`, `markdown-it-py>=3.0`, `pathspec>=0.12`. Provider SDKs are optional extras only: `anthropic>=0.40.0`, `openai>=1.0.0`, `google-genai>=0.3.0`.
- Package name `crack-codebase`; import name `crack`; console script `crack = "crack.cli:main"`.
- Default output root is `./crack-output/<repo-name>/<analysis>/`, holding `index.md` and `index.html`.
- Every task ends with a passing `pytest` run and a commit. No task leaves the tree red.
- Parity with the chapter renderers is the acceptance bar for every ported analysis. Deliberate differences must be listed explicitly in the parity test, never waved through.

---

### Task 1: Package scaffold and core extraction

Create the installable package and copy the five `utils/` modules into `crack.core`. `utils/` is already a package using relative imports with no `sys.path` manipulation, so this copy is near-verbatim.

**Files:**

- Create: `pyproject.toml`
- Create: `src/crack/__init__.py`
- Create: `src/crack/core/__init__.py`
- Create: `src/crack/core/call_llm.py` (copy of `utils/call_llm.py`)
- Create: `src/crack/core/llm.py` (copy of `utils/llm.py`)
- Create: `src/crack/core/crawl.py` (copy of `utils/crawl.py`)
- Create: `src/crack/core/overview.py` (copy of `utils/overview.py`)
- Create: `src/crack/core/nodes.py` (copy of `utils/nodes.py`)
- Test: `tests/test_core_imports.py`

**Interfaces:**

- Consumes: nothing.
- Produces: `crack.core.call_llm(prompt: str) -> str`, `crack.core.call_image(prompt: str, output_path: str) -> str`, `crack.core.write_overview(name, what, sections, facts="") -> dict`, `crack.core.OverviewNode(spec, max_retries=2, wait=2)`, `crack.core.read_prompt(prompts_dir, name) -> str`, `crack.core.fill(template, **kwargs) -> str`, `crack.core.extract_mermaid(md, kind=None) -> str`, `crack.core.parse_json`, `crack.core.parse_yaml`, `crack.core.json_call`, `crack.core.yaml_call`, `crack.core.crawl(root, **kwargs)`, `crack.core.list_files(root, *, keep_ext, skip_dirs, ...)`, `crack.core.safe_read(path) -> str`, and the constants `DEFAULT_KEEP_EXT`, `DEFAULT_SKIP_DIR`, `DEFAULT_KEEP_NAMES`, `DEFAULT_MAX_FILE_BYTES`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_core_imports.py`:

```python
"""crack.core must re-export the same surface utils/ does."""
import inspect

def test_core_reexports_public_surface():
    import crack.core as core

    expected = {
        "call_llm", "call_image", "write_overview", "OverviewNode",
        "read_prompt", "fill", "extract_mermaid", "parse_json", "parse_yaml",
        "json_call", "yaml_call", "crawl", "list_files", "safe_read",
        "DEFAULT_KEEP_EXT", "DEFAULT_SKIP_DIR", "DEFAULT_KEEP_NAMES",
        "DEFAULT_MAX_FILE_BYTES",
    }
    missing = expected - set(dir(core))
    assert not missing, f"crack.core is missing: {sorted(missing)}"

def test_core_does_not_touch_sys_path():
    """The chapters manipulate sys.path; the package must not."""
    import pathlib
    core_dir = pathlib.Path(inspect.getfile(__import__("crack.core", fromlist=["x"]))).parent
    for path in core_dir.glob("*.py"):
        assert "sys.path.insert" not in path.read_text(), f"{path.name} manipulates sys.path"

def test_call_llm_signature_matches_utils():
    from crack.core import call_llm
    assert list(inspect.signature(call_llm).parameters) == ["prompt"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_core_imports.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'crack'`

- [ ] **Step 3: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "crack-codebase"
version = "0.1.0"
description = "Read any codebase six ways: product intent, git history, schema, interfaces, architecture, backend."
requires-python = ">=3.10"
dependencies = [
    "pocketflow>=0.0.1",
    "pyyaml>=6.0",
    "markdown-it-py>=3.0",
    "pathspec>=0.12",
]

[project.optional-dependencies]
anthropic = ["anthropic>=0.40.0"]
openai = ["openai>=1.0.0"]
google = ["google-genai>=0.3.0"]
dev = ["pytest>=8.0"]

[project.scripts]
crack = "crack.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
"crack.analyses" = ["*/prompts/*.md"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 4: Copy the five core modules verbatim**

These are byte-for-byte copies. No edits to the file bodies are needed, because `utils/` uses relative imports already and contains no `sys.path` manipulation.

```bash
mkdir -p src/crack/core tests
cp utils/call_llm.py src/crack/core/call_llm.py
cp utils/llm.py      src/crack/core/llm.py
cp utils/crawl.py    src/crack/core/crawl.py
cp utils/overview.py src/crack/core/overview.py
cp utils/nodes.py    src/crack/core/nodes.py
```

Verify no copied file manipulates `sys.path`:

```bash
grep -rn "sys.path" src/crack/core/ && echo "FOUND — remove those lines" || echo "clean"
```

- [ ] **Step 5: Write `src/crack/__init__.py`**

```python
"""Read any codebase six ways from one command."""
__version__ = "0.1.0"
```

- [ ] **Step 6: Write `src/crack/core/__init__.py`**

This mirrors `utils/__init__.py` exactly, so ported analysis code can swap `from utils import X` for `from crack.core import X` with no other change.

```python
"""Shared helpers every analysis imports: the LLM wrapper, the crawler, the
LLM-node plumbing, the reusable OverviewNode, and the page-overview writer."""
# Re-exported for `from crack.core import <name>`; not used inside this module.
from .call_llm import call_llm, call_image  # noqa: F401
from .overview import write_overview  # noqa: F401
from .nodes import OverviewNode  # noqa: F401
from .llm import (  # noqa: F401
    read_prompt,
    fill,
    extract_mermaid,
    parse_json,
    parse_yaml,
    json_call,
    yaml_call,
)
from .crawl import (  # noqa: F401
    crawl,
    list_files,
    safe_read,
    DEFAULT_KEEP_EXT,
    DEFAULT_SKIP_DIR,
    DEFAULT_KEEP_NAMES,
    DEFAULT_MAX_FILE_BYTES,
)
```

- [ ] **Step 7: Install the package in editable mode**

Run: `pip install -e ".[dev]"`
Expected: installs `crack-codebase 0.1.0` with no errors.

- [ ] **Step 8: Run the tests to verify they pass**

Run: `pytest tests/test_core_imports.py -v`
Expected: 3 passed.

- [ ] **Step 9: Verify no chapter file changed**

Run: `git status --porcelain -- 'ch*'`
Expected: empty output. If anything is listed, revert it before committing.

- [ ] **Step 10: Commit**

```bash
git add pyproject.toml src/crack tests/test_core_imports.py
git commit -m "feat: package scaffold and crack.core extraction"
```

---

### Task 2: Analysis registry and environment defaults

The registry maps a subcommand name to its analysis module. It imports lazily so a broken analysis cannot stop the whole CLI from starting. The environment helper applies an analysis's `ENV_DEFAULTS` and restores the prior environment afterwards, so under `crack all` one analysis's default never leaks into the next.

**Files:**

- Create: `src/crack/analyses/__init__.py`
- Create: `src/crack/core/env.py`
- Test: `tests/test_registry.py`
- Test: `tests/test_env.py`

**Interfaces:**

- Consumes: nothing from earlier tasks.
- Produces: `crack.analyses.ANALYSIS_NAMES: tuple[str, ...]` (the six names in port order), `crack.analyses.load(name: str) -> ModuleType` (raises `KeyError` for an unknown name), and `crack.core.env.env_defaults(defaults: dict[str, str])` — a context manager that sets each key only when absent and restores the prior environment on exit.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_env.py`:

```python
import os
import pytest
from crack.core.env import env_defaults

VAR = "LLM_MAX_OUTPUT_TOKENS"

@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv(VAR, raising=False)

def test_sets_default_when_absent():
    with env_defaults({VAR: "32768"}):
        assert os.environ[VAR] == "32768"

def test_restores_absence_on_exit():
    with env_defaults({VAR: "32768"}):
        pass
    assert VAR not in os.environ

def test_user_value_always_wins(monkeypatch):
    monkeypatch.setenv(VAR, "4096")
    with env_defaults({VAR: "32768"}):
        assert os.environ[VAR] == "4096"
    assert os.environ[VAR] == "4096"

def test_restores_even_when_body_raises():
    with pytest.raises(RuntimeError):
        with env_defaults({VAR: "32768"}):
            raise RuntimeError("boom")
    assert VAR not in os.environ

def test_empty_defaults_is_a_noop():
    with env_defaults({}):
        assert VAR not in os.environ
```

Create `tests/test_registry.py`:

```python
import pytest
from crack import analyses

def test_six_analyses_in_port_order():
    assert analyses.ANALYSIS_NAMES == (
        "backend", "architecture", "interfaces",
        "schema", "git-history", "product-intent",
    )

def test_unknown_name_raises_keyerror():
    with pytest.raises(KeyError):
        analyses.load("nonsense")

def test_load_is_lazy():
    """Importing the registry must not import any analysis module."""
    import subprocess, sys
    code = (
        "import sys; import crack.analyses; "
        "print([m for m in sys.modules if m.startswith('crack.analyses.')])"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.stdout.strip() == "[]", out.stdout
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_env.py tests/test_registry.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'crack.core.env'` and `No module named 'crack.analyses'`

- [ ] **Step 3: Write `src/crack/core/env.py`**

```python
"""Apply an analysis's environment defaults for the length of one run."""
import contextlib
import os

@contextlib.contextmanager
def env_defaults(defaults):
    """Set each key only when it is absent, then restore the prior environment.

    A value the user already set always wins. Restoring on exit keeps one
    analysis's default from leaking into the next under `crack all`.
    """
    prior = {}
    try:
        for key, value in defaults.items():
            prior[key] = os.environ.get(key)
            if prior[key] is None:
                os.environ[key] = value
        yield
    finally:
        for key, value in prior.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
```

- [ ] **Step 4: Write `src/crack/analyses/__init__.py`**

```python
"""Registry of the six analyses, in port order (converged chapters first)."""
import importlib

ANALYSIS_NAMES = (
    "backend",
    "architecture",
    "interfaces",
    "schema",
    "git-history",
    "product-intent",
)

_MODULES = {name: name.replace("-", "_") for name in ANALYSIS_NAMES}

def load(name):
    """Import and return one analysis module. Raises KeyError if unknown."""
    if name not in _MODULES:
        raise KeyError(f"unknown analysis {name!r}; expected one of {', '.join(ANALYSIS_NAMES)}")
    return importlib.import_module(f"crack.analyses.{_MODULES[name]}")
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `pytest tests/test_env.py tests/test_registry.py -v`
Expected: 8 passed.

- [ ] **Step 6: Verify no chapter file changed**

Run: `git status --porcelain -- 'ch*'`
Expected: empty output.

- [ ] **Step 7: Commit**

```bash
git add src/crack/analyses/__init__.py src/crack/core/env.py tests/test_env.py tests/test_registry.py
git commit -m "feat: analysis registry and environment defaults"
```

---

### Task 3: The shared render engine

One engine serves the card family (backend, architecture, interfaces, schema). Each of those analyses declares a `THEME` (palette and copy) and a `SECTIONS` list; the engine does the rest. An analysis may instead define its own `render_html`/`render_markdown`, which the engine delegates to untouched. ch05 and ch06 use that path.

Apply the deliberate unifications from the spec while building the CSS. Do not port the dead code the survey found: `_welcome_html`, `extract_mermaid` in ch09/ch10, and ch09's `.verdict` rules.

**Files:**

- Create: `src/crack/core/render.py`
- Test: `tests/test_render.py`

**Interfaces:**

- Consumes: nothing from earlier tasks.
- Produces: `crack.core.render.md(text) -> str`, `md_rich(text) -> str`, `esc(s) -> str`, `split_cards(markdown) -> list[tuple[str, str]]`, `extract_mermaid(text) -> str`, `strip_mermaid(text) -> str`, `card(header_md, body_md) -> str`, `section(spec, cards_html, prefix_html="", intro="") -> str`, the dataclasses `Section` and `Theme`, and the dispatchers `render_html(analysis, name, shared) -> str` and `render_markdown(analysis, name, shared) -> str`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_render.py`:

````python
import types
import pytest
from crack.core import render
from crack.core.render import Section, Theme

def test_md_unwraps_a_single_paragraph():
    assert render.md("hello *there*") == "hello <em>there</em>"

def test_md_keeps_multiple_paragraphs_wrapped():
    out = render.md("one\n\ntwo")
    assert out.count("<p>") == 2

def test_md_handles_none():
    assert render.md(None) == ""

def test_esc_escapes_markup():
    assert render.esc("<script>") == "&lt;script&gt;"

def test_split_cards_drops_content_before_first_header():
    markdown = "preamble text\n\n### First\nbody one\n\n### Second\nbody two"
    assert render.split_cards(markdown) == [
        ("First", "body one"), ("Second", "body two")]

def test_split_cards_on_empty_input():
    assert render.split_cards("") == []
    assert render.split_cards(None) == []

def test_extract_and_strip_mermaid_are_complements():
    text = "before\n\n```mermaid\ngraph TD;\nA-->B;\n```\n\nafter"
    assert render.extract_mermaid(text) == "graph TD;\nA-->B;"
    stripped = render.strip_mermaid(text)
    assert "mermaid" not in stripped
    assert "before" in stripped and "after" in stripped

def test_md_rich_converts_mermaid_fence_to_pre():
    out = render.md_rich("```mermaid\ngraph TD;\n```")
    assert '<pre class="mermaid">' in out
    assert "language-mermaid" not in out

def _theme():
    return Theme(
        title_suffix="backend", eyebrow="Backend",
        accent="#4f46e5", accent_soft="#eef2ff",
        hero_from="#1e1b4b", hero_to="#0f0d2b",
        eyebrow_color="#a5b4fc", eyebrow_bar="#818cf8",
        sub_color="#d6d8f5", card_top_from="#fafaff",
        subtitle=lambda shared: "a subtitle",
        footer=lambda shared: "a footer",
        md_preamble=lambda shared: "",
    )

def _analysis(sections, theme=None):
    return types.SimpleNamespace(
        NAME="backend", THEME=theme or _theme(), SECTIONS=sections)

def test_section_omitted_when_key_empty_and_mode_is_omit():
    sections = [Section("01", "The tour", "note", "tour", 400, "tour_md",
                        when_empty="omit")]
    html = render.render_html(_analysis(sections), "zulip", {})
    assert "The tour" not in html

def test_section_survives_an_empty_key_by_default():
    """ch07 01-03, ch09 and ch10 keep the heading and grow an empty rail."""
    sections = [Section("01", "The trace", "note", "trace", 460, "trace_md")]
    html = render.render_html(_analysis(sections), "zulip", {})
    assert "The trace" in html
    assert 'class="rail trace"' in html

def test_section_renders_skip_note_when_mode_is_skip_note():
    sections = [Section("04", "Migration history", "note", "acts", 420,
                        "migration_md", when_empty="skip-note",
                        skip_note=lambda shared: "skipped &mdash; too few migrations")]
    html = render.render_html(_analysis(sections), "zulip", {})
    assert "Migration history" in html
    assert "too few migrations" in html
    assert 'class="rail acts"' not in html

def test_rail_width_comes_from_the_section():
    sections = [Section("01", "The pipeline", "n", "pipe", 400, "pipeline_md")]
    html = render.render_html(_analysis(sections), "zulip",
                              {"pipeline_md": "### A\nbody"})
    assert ".rail.pipe .card { flex: 0 0 400px; width: 400px; }" in html

def test_theme_drives_title_eyebrow_and_accent():
    sections = [Section("01", "S", "n", "pipe", 400, "k")]
    html = render.render_html(_analysis(sections), "zulip", {"k": "### A\nb"})
    assert "<title>zulip: backend</title>" in html
    assert '<span class="eyebrow">Backend</span>' in html
    assert "--accent: #4f46e5" in html

def test_page_name_hook_overrides_the_repo_name():
    """ch07 titles its page with shared["product_name"]."""
    import dataclasses
    theme = dataclasses.replace(
        _theme(), title_suffix="schema",
        page_name=lambda shared, name: shared.get("product_name") or name)
    sections = [Section("01", "S", "n", "tour", 400, "k")]
    html = render.render_html(_analysis(sections, theme), "repo-dir",
                              {"k": "### A\nb", "product_name": "Zulip"})
    assert "<title>Zulip: schema</title>" in html
    assert "<h1>Zulip</h1>" in html

def test_prefix_hook_renders_above_the_rail():
    sections = [Section("01", "S", "n", "seq", 560, "k",
                        prefix=lambda shared: '<div class="diagram">D</div>')]
    html = render.render_html(_analysis(sections), "zulip", {"k": "### A\nb"})
    assert html.index('class="diagram"') < html.index('class="rail seq"')

def test_unifications_are_applied():
    """Incidental drift among ch07-ch10 collapses to one value."""
    sections = [Section("01", "S", "n", "pipe", 400, "k")]
    html = render.render_html(_analysis(sections), "zulip", {"k": "### A\nb"})
    assert "max-height: 72vh" in html
    assert "font-size: .74rem" in html
    assert ".erd" not in html
    assert "class=\"verdict\"" not in html

def test_dead_helpers_are_not_ported():
    assert not hasattr(render, "_welcome_html")

def test_custom_renderer_takes_precedence():
    analysis = types.SimpleNamespace(
        NAME="product-intent",
        render_html=lambda name, shared: f"<html>{name} custom</html>",
        render_markdown=lambda name, shared: f"# {name} custom")
    assert render.render_html(analysis, "nats", {}) == "<html>nats custom</html>"
    assert render.render_markdown(analysis, "nats", {}) == "# nats custom"

def test_markdown_uses_theme_suffix_and_section_labels():
    sections = [Section("01", "The pipeline", "n", "pipe", 400, "pipeline_md")]
    out = render.render_markdown(_analysis(sections), "zulip",
                                 {"pipeline_md": "### A\nbody"})
    assert out.startswith("# zulip: backend")
    assert "## The pipeline" in out
    assert "### A" in out

def test_markdown_skip_note_when_section_empty():
    sections = [Section("04", "Migration history", "n", "acts", 420,
                        "migration_md", when_empty="skip-note",
                        skip_note=lambda shared: "skipped",
                        md_skip_note=lambda shared: "_Skipped: too few._")]
    out = render.render_markdown(_analysis(sections), "zulip", {})
    assert "## Migration history" in out
    assert "_Skipped: too few._" in out
````

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_render.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'crack.core.render'`

- [ ] **Step 3: Write the dataclasses and text helpers**

Create `src/crack/core/render.py` starting with:

````python
"""One render engine for the card family, plus the helpers custom renderers reuse.

An analysis either declares THEME + SECTIONS and lets this module build its
page, or defines its own render_html/render_markdown and this module steps
aside. ch05 and ch06 take the second path: their pages are hand-built from
structured data rather than markdown blobs.
"""
import html as _html
import re
from dataclasses import dataclass, field
from typing import Callable, Optional

from markdown_it import MarkdownIt

_MD = MarkdownIt("commonmark", {"html": False, "linkify": True, "breaks": False}).enable(["table"])

@dataclass(frozen=True)
class Section:
    """One numbered section of a card-family page.

    when_empty controls what happens when shared[key] is falsy:
      "always"    render the section anyway, with an empty rail (the default,
                  matching ch07 01-03, ch09, and ch10)
      "omit"      drop the section entirely (ch08's tour)
      "skip-note" render the head with skip_note() as its note, no rail (ch07 04)
    """
    number: str
    label: str
    note: str
    rail: str
    width: int
    key: str
    when_empty: str = "always"
    skip_note: Optional[Callable] = None
    md_skip_note: Optional[Callable] = None
    prefix: Optional[Callable] = None
    cards: Optional[Callable] = None

@dataclass(frozen=True)
class Theme:
    """The palette and copy that differ per analysis."""
    title_suffix: str
    eyebrow: str
    accent: str
    accent_soft: str
    hero_from: str
    hero_to: str
    eyebrow_color: str
    eyebrow_bar: str
    sub_color: str
    card_top_from: str
    subtitle: Callable
    footer: Callable
    md_preamble: Callable
    hero_prefix: Optional[Callable] = None
    # ch07 titles its page with shared["product_name"] rather than the repo
    # directory name. page_name covers both the HTML hero and the markdown H1.
    page_name: Optional[Callable] = None

def _mermaidize(rendered_html):
    return re.sub(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        lambda m: f'<pre class="mermaid">{_html.unescape(m.group(1))}</pre>',
        rendered_html, flags=re.DOTALL,
    )

def md(text):
    if text is None:
        return ""
    out = _MD.render(str(text).strip()).strip()
    if out.startswith("<p>") and out.endswith("</p>") and out.count("<p>") == 1:
        return out[3:-4]
    return out

def md_rich(text):
    return _mermaidize(_MD.render(str(text or "").strip()))

def esc(s):
    return _html.escape(str(s).strip())

def extract_mermaid(text):
    m = re.search(r"```mermaid\s*\n(.*?)```", text or "", re.DOTALL)
    return m.group(1).strip() if m else ""

def strip_mermaid(text):
    return re.sub(r"```mermaid\s*\n.*?```", "", text or "", flags=re.DOTALL).strip()

def split_cards(markdown):
    """Split a markdown blob into (header, body) pairs on each `### ` header.

    Content before the first `###` is dropped here; a caller that needs it
    renders it separately through a Section.prefix hook.
    """
    cards, title, body = [], None, []
    for line in (markdown or "").splitlines():
        m = re.match(r'^###\s+(.*)', line)
        if m:
            if title is not None:
                cards.append((title.strip(), "\n".join(body).strip()))
            title, body = m.group(1), []
        elif title is not None:
            body.append(line)
    if title is not None:
        cards.append((title.strip(), "\n".join(body).strip()))
    return cards

def card(header_md, body_md):
    return (
        '      <li class="card">\n'
        f'        <div class="card-top">{md(header_md)}</div>\n'
        f'        <div class="scroll"><div class="card-body">{md_rich(body_md)}</div></div>\n'
        '      </li>'
    )

def section(spec, cards_html, prefix_html="", intro=""):
    intro_html = f'    <div class="sec-intro">{intro}</div>\n' if intro else ""
    return (
        '    <div class="sec-head">\n'
        f'      <span class="sec-n">{spec.number}</span>\n'
        f'      <div class="sec-label">{spec.label}</div>\n'
        f'      <div class="sec-note">{spec.note}</div>\n'
        '      <div class="scroll-hint">swipe &rarr;</div>\n'
        '    </div>\n'
        f'{intro_html}{prefix_html}'
        f'    <ul class="rail {spec.rail}">\n{cards_html}\n    </ul>'
    )

def _skip_head(spec, shared):
    note = spec.skip_note(shared) if spec.skip_note else "skipped"
    return (f'    <div class="sec-head"><span class="sec-n">{spec.number}</span>'
            f'<div class="sec-label">{spec.label}</div>'
            f'<div class="sec-note">{note}</div></div>')

def _intro(shared, label):
    text = (shared.get("overview") or {}).get("intros", {}).get(label, "")
    return md_rich(text) if text else ""
````

- [ ] **Step 4: Add the page template**

Append the `PAGE` constant to `render.py`. Build it by copying the `HTML_TEMPLATE` string from `ch10-backend/workflow/render.py:65-199` and applying exactly these changes. Every other line stays byte-for-byte identical, including the doubled braces required by `str.format`.

1. `<title>{name}: backend</title>` becomes `<title>{name}: {title_suffix}</title>`.
2. Keep ch10's Mermaid init line verbatim (it is the one with `flowchart: {{ htmlLabels: true }}`); it now applies to all four analyses.
3. In `:root`, replace the accent pair with placeholders: `--accent: {accent}; --accent-soft: {accent_soft};`.
4. In `.hero`, replace the gradient stops with `{hero_from} 0%, {hero_to} 70%`.
5. In `.eyebrow`, replace the colour with `{eyebrow_color}`; in `.eyebrow::before`, replace the background with `{eyebrow_bar}`; in `.hero .sub`, replace the colour with `{sub_color}`.
6. In `.card`, change `max-height: 74vh` to `max-height: 72vh`.
7. In `.card-top`, replace the gradient start with `{card_top_from}` and change `font-size: .95rem` to `font-size: .96rem`.
8. In `.card-body li`, change `margin: .3em 0` to `margin: .28em 0`.
9. In `pre code`, change `font-size: .73rem` to `font-size: .74rem`.
10. Add the table rules from `ch07-schema/workflow/render.py:179-183` immediately after the `code` rule, including the `td code` line ch08 lacks.
11. Add a `{rail_widths}` placeholder on its own line immediately after the `.rail::-webkit-scrollbar-thumb` rule; the engine fills it with one `.rail.<name> .card` rule per section.
12. Replace `<span class="eyebrow">Backend</span>` with `<span class="eyebrow">{eyebrow}</span>`.
13. Replace the whole `<footer>` line with `    <footer>{footer}</footer>`.
14. Delete nothing else. Do not copy `_welcome_html`, the `.verdict` rules, or the `.erd` rules; `.diagram` already covers the diagram wrapper.

- [ ] **Step 5: Write the two dispatchers**

Append to `render.py`:

```python
def _rail_widths(sections):
    return "\n".join(
        f"  .rail.{s.rail} .card {{ flex: 0 0 {s.width}px; width: {s.width}px; }}"
        for s in sections)

def _section_html(spec, shared):
    body = shared.get(spec.key, "")
    if not body:
        if spec.when_empty == "omit":
            return None
        if spec.when_empty == "skip-note":
            return _skip_head(spec, shared)
    builder = spec.cards or (lambda sh, text: "\n".join(card(h, b) for h, b in split_cards(text)))
    prefix = spec.prefix(shared) if spec.prefix else ""
    return section(spec, builder(shared, body), prefix_html=prefix,
                   intro=_intro(shared, spec.label))

def _render_card_page(analysis, name, shared):
    theme = analysis.THEME
    blocks = [html for html in
              (_section_html(spec, shared) for spec in analysis.SECTIONS)
              if html is not None]
    page_name = theme.page_name(shared, name) if theme.page_name else name
    return PAGE.format(
        name=esc(page_name),
        title_suffix=theme.title_suffix,
        eyebrow=esc(theme.eyebrow),
        accent=theme.accent, accent_soft=theme.accent_soft,
        hero_from=theme.hero_from, hero_to=theme.hero_to,
        eyebrow_color=theme.eyebrow_color, eyebrow_bar=theme.eyebrow_bar,
        sub_color=theme.sub_color, card_top_from=theme.card_top_from,
        rail_widths=_rail_widths(analysis.SECTIONS),
        subtitle=theme.subtitle(shared),
        intro=theme.hero_prefix(shared) if theme.hero_prefix else "",
        sections="\n".join(blocks),
        footer=theme.footer(shared),
    )

def _render_card_markdown(analysis, name, shared):
    theme = analysis.THEME
    title = theme.page_name(shared, name) if theme.page_name else name
    parts = [f"# {title}: {theme.title_suffix}\n"]

    preamble = theme.md_preamble(shared)
    if preamble:
        parts.append(preamble)
    welcome = (shared.get("overview") or {}).get("welcome")
    if welcome:
        parts.append(welcome.strip() + "\n")

    for spec in analysis.SECTIONS:
        body = shared.get(spec.key, "")
        if not body and spec.when_empty == "omit":
            continue
        parts.append(f"## {spec.label}\n")
        if not body and spec.md_skip_note:
            parts.append(spec.md_skip_note(shared))
        else:
            # Matches the chapters, which append body.strip() + "\n"
            # unconditionally: an absent key still emits a blank line.
            parts.append(body.strip() + "\n")
    return "\n".join(parts)

def render_html(analysis, name, shared):
    """Render one analysis's page, deferring to a custom renderer when present."""
    custom = getattr(analysis, "render_html", None)
    return custom(name, shared) if custom else _render_card_page(analysis, name, shared)

def render_markdown(analysis, name, shared):
    custom = getattr(analysis, "render_markdown", None)
    return custom(name, shared) if custom else _render_card_markdown(analysis, name, shared)
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `pytest tests/test_render.py -v`
Expected: 21 passed.

- [ ] **Step 7: Verify no chapter file changed**

Run: `git status --porcelain -- 'ch*'`
Expected: empty output.

- [ ] **Step 8: Commit**

```bash
git add src/crack/core/render.py tests/test_render.py
git commit -m "feat: shared render engine for the card-family analyses"
```

---

### Task 4: The runner

The runner executes one analysis end to end: it applies that analysis's environment defaults, builds the shared dict, runs the flow, and writes `index.md` and `index.html` into the output directory. It is the single place that knows the output layout.

**Files:**

- Create: `src/crack/core/runner.py`
- Test: `tests/test_runner.py`

**Interfaces:**

- Consumes: `crack.core.env.env_defaults` (Task 2), `crack.core.render.render_html(analysis, name, shared) -> str` and `render_markdown(analysis, name, shared) -> str` (Task 3).
- Produces: `crack.core.runner.output_dir(root: str, repo_name: str, analysis_name: str) -> str`, `crack.core.runner.repo_name_of(repo_path: str) -> str`, and `crack.core.runner.run_analysis(analysis, repo_path: str, out_root: str, args) -> str` which returns the output directory it wrote.

- [ ] **Step 1: Write the failing test**

Create `tests/test_runner.py`:

```python
import os
import types
import pytest
from crack.core import runner

def _fake_analysis(**overrides):
    """A minimal analysis module standing in for a real one."""
    mod = types.SimpleNamespace()
    mod.NAME = "fake"
    mod.ENV_DEFAULTS = {}
    mod.SECTIONS = []
    mod.init_shared = lambda args, out_dir: {"repo_path": args.repo_path}
    mod.overview_spec = lambda shared: {"name": "x", "what": "y", "sections": []}
    ran = {"count": 0}

    def build_flow():
        flow = types.SimpleNamespace()
        def run(shared):
            ran["count"] += 1
            shared["ran"] = True
        flow.run = run
        return flow

    mod.build_flow = build_flow
    mod._ran = ran
    for key, value in overrides.items():
        setattr(mod, key, value)
    return mod

def test_repo_name_strips_trailing_slash():
    assert runner.repo_name_of("/tmp/zulip/") == "zulip"
    assert runner.repo_name_of("/tmp/zulip") == "zulip"

def test_output_dir_layout():
    assert runner.output_dir("/out", "zulip", "backend") == os.path.join(
        "/out", "zulip", "backend")

def test_run_analysis_writes_both_files(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "render_html", lambda a, n, s: "<html>ok</html>")
    monkeypatch.setattr(runner, "render_markdown", lambda a, n, s: "# ok")
    repo = tmp_path / "myrepo"
    repo.mkdir()
    analysis = _fake_analysis()
    args = types.SimpleNamespace(repo_path=str(repo))

    out = runner.run_analysis(analysis, str(repo), str(tmp_path / "out"), args)

    assert analysis._ran["count"] == 1
    assert open(os.path.join(out, "index.html")).read() == "<html>ok</html>"
    assert open(os.path.join(out, "index.md")).read() == "# ok"
    assert out.endswith(os.path.join("myrepo", "fake"))

def test_run_analysis_applies_env_defaults(tmp_path, monkeypatch):
    monkeypatch.delenv("LLM_MAX_OUTPUT_TOKENS", raising=False)
    monkeypatch.setattr(runner, "render_html", lambda a, n, s: "")
    monkeypatch.setattr(runner, "render_markdown", lambda a, n, s: "")
    seen = {}

    def build_flow():
        flow = types.SimpleNamespace()
        flow.run = lambda shared: seen.update(
            value=os.environ.get("LLM_MAX_OUTPUT_TOKENS"))
        return flow

    repo = tmp_path / "r"
    repo.mkdir()
    analysis = _fake_analysis(ENV_DEFAULTS={"LLM_MAX_OUTPUT_TOKENS": "32768"},
                              build_flow=build_flow)
    runner.run_analysis(analysis, str(repo), str(tmp_path / "out"),
                        types.SimpleNamespace(repo_path=str(repo)))

    assert seen["value"] == "32768"
    assert "LLM_MAX_OUTPUT_TOKENS" not in os.environ

def test_run_analysis_passes_out_dir_to_init_shared(tmp_path, monkeypatch):
    """ch05 needs out_dir in shared before the flow runs (pain.png)."""
    monkeypatch.setattr(runner, "render_html", lambda a, n, s: "")
    monkeypatch.setattr(runner, "render_markdown", lambda a, n, s: "")
    captured = {}
    repo = tmp_path / "r"
    repo.mkdir()
    analysis = _fake_analysis(
        init_shared=lambda args, out_dir: captured.setdefault("out_dir", out_dir) or
        {"repo_path": args.repo_path})
    out = runner.run_analysis(analysis, str(repo), str(tmp_path / "out"),
                              types.SimpleNamespace(repo_path=str(repo)))
    assert captured["out_dir"] == out
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_runner.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'crack.core.runner'`

- [ ] **Step 3: Write `src/crack/core/runner.py`**

```python
"""Run one analysis end to end and write its report."""
import os

from .env import env_defaults
from .render import render_html, render_markdown

def repo_name_of(repo_path):
    """The directory name of the repo, used as the output folder name."""
    return os.path.basename(os.path.abspath(repo_path).rstrip(os.sep))

def output_dir(root, repo_name, analysis_name):
    return os.path.join(root, repo_name, analysis_name)

def run_analysis(analysis, repo_path, out_root, args):
    """Run one analysis and write index.md + index.html. Returns the output dir.

    The output directory is created before the flow runs, because some
    analyses write extra files into it during the run (ch05 writes pain.png).
    """
    name = repo_name_of(repo_path)
    out_dir = output_dir(out_root, name, analysis.NAME)
    os.makedirs(out_dir, exist_ok=True)

    shared = analysis.init_shared(args, out_dir)
    with env_defaults(getattr(analysis, "ENV_DEFAULTS", {})):
        analysis.build_flow().run(shared)

    with open(os.path.join(out_dir, "index.md"), "w") as fh:
        fh.write(render_markdown(analysis, name, shared))
    with open(os.path.join(out_dir, "index.html"), "w") as fh:
        fh.write(render_html(analysis, name, shared))
    return out_dir
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_runner.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git status --porcelain -- 'ch*'   # must be empty
git add src/crack/core/runner.py tests/test_runner.py
git commit -m "feat: analysis runner writing index.md and index.html"
```

---

### Task 5: The `crack all` index page

`crack all` writes one page at the repo's output root linking the six reports. It shows each report's welcome line where the analysis produced one, and names any analysis that failed so a partial run is honest about what is missing.

**Files:**

- Create: `src/crack/core/index.py`
- Test: `tests/test_index.py`

**Interfaces:**

- Consumes: `crack.core.render.md` and `crack.core.render.esc` (Task 3).
- Produces: `crack.core.index.write_index(root: str, repo_name: str, written: dict[str, str], failed: list[tuple[str, Exception]]) -> str`, returning the path of the page it wrote.

- [ ] **Step 1: Write the failing test**

Create `tests/test_index.py`:

```python
import os
import pytest
from crack.core.index import write_index

def test_links_every_written_report(tmp_path):
    written = {"backend": str(tmp_path / "backend"),
               "schema": str(tmp_path / "schema")}
    path = write_index(str(tmp_path), "zulip", written, [])
    html = open(path).read()
    assert path == os.path.join(str(tmp_path), "index.html")
    assert 'href="backend/index.html"' in html
    assert 'href="schema/index.html"' in html
    assert "zulip" in html

def test_names_failed_analyses(tmp_path):
    path = write_index(str(tmp_path), "zulip", {"backend": str(tmp_path / "backend")},
                       [("schema", RuntimeError("no schema found"))])
    html = open(path).read()
    assert "schema" in html
    assert "no schema found" in html

def test_escapes_failure_text(tmp_path):
    path = write_index(str(tmp_path), "zulip", {},
                       [("schema", RuntimeError("<script>x</script>"))])
    html = open(path).read()
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html

def test_empty_run_still_writes_a_page(tmp_path):
    path = write_index(str(tmp_path), "zulip", {}, [])
    assert os.path.exists(path)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_index.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'crack.core.index'`

- [ ] **Step 3: Write `src/crack/core/index.py`**

```python
"""The landing page `crack all` writes above the six reports."""
import os

from .render import esc

TITLES = {
    "product-intent": "Product intent",
    "git-history": "Git history",
    "schema": "Schema",
    "interfaces": "Interfaces",
    "architecture": "Architecture",
    "backend": "Backend",
}

NOTES = {
    "product-intent": "the product story, reverse engineered from the source",
    "git-history": "the roadmap already written in the git log",
    "schema": "the data model and how it migrated",
    "interfaces": "the API surface and one action traced through it",
    "architecture": "the services and how a request crosses them",
    "backend": "the six layers every request flows through",
}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #f7f8fa; --surface: #fff; --text: #101828; --muted: #667085;
    --faint: #98a2b3; --rule: #e4e7ec; --accent: #4f46e5;
    --bad: #b42318; --bad-bg: #fef3f2;
    --shadow: 0 1px 2px rgba(16,24,40,.05); --radius: 12px;
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    font-size: 13.5px; line-height: 1.5; background: var(--bg); color: var(--text); margin: 0;
    -webkit-font-smoothing: antialiased; }}
  main {{ max-width: 900px; margin: 0 auto; padding: 0 24px 56px; }}
  .hero {{ background: radial-gradient(120% 140% at 50% 0%, #1e1b4b 0%, #0f0d2b 70%);
    color: #fff; padding: 46px 20px 42px; text-align: center; }}
  .eyebrow {{ display: inline-flex; align-items: center; gap: 7px; color: #a5b4fc;
    font-size: .68rem; font-weight: 700; letter-spacing: .18em; text-transform: uppercase; }}
  .eyebrow::before {{ content: ''; width: 16px; height: 2px; background: #818cf8; border-radius: 2px; }}
  .hero h1 {{ font-size: 1.9rem; font-weight: 800; letter-spacing: -.025em; margin: 12px 0 10px; }}
  .hero .sub {{ font-size: .94rem; color: #d6d8f5; margin: 0; }}
  ul.reports {{ list-style: none; padding: 0; margin: 32px 0 0; display: grid; gap: 14px; }}
  a.report {{ display: block; background: var(--surface); border: 1px solid var(--rule);
    border-left: 4px solid var(--accent); border-radius: var(--radius); box-shadow: var(--shadow);
    padding: 18px 22px; text-decoration: none; color: inherit; }}
  a.report:hover {{ border-color: var(--accent); }}
  .report h2 {{ margin: 0 0 5px; font-size: 1rem; font-weight: 700; }}
  .report p {{ margin: 0; font-size: .86rem; color: var(--muted); }}
  .failed {{ background: var(--bad-bg); border: 1px solid #fecdca; border-radius: var(--radius);
    padding: 16px 20px; margin-top: 26px; }}
  .failed h2 {{ margin: 0 0 8px; font-size: .78rem; font-weight: 700; letter-spacing: .1em;
    text-transform: uppercase; color: var(--bad); }}
  .failed li {{ font-size: .84rem; color: #7a271a; margin: .3em 0; }}
  .failed code {{ font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: .82em; }}
  footer {{ color: var(--faint); font-size: .74rem; text-align: center; margin-top: 44px;
    padding-top: 18px; border-top: 1px solid var(--rule); }}
</style>
</head>
<body>
  <header class="hero">
    <span class="eyebrow">Codebase</span>
    <h1>{name}</h1>
    <p class="sub">{sub}</p>
  </header>
  <main>
    <ul class="reports">
{cards}
    </ul>
{failures}
    <footer>Written by crack.</footer>
  </main>
</body>
</html>
"""

def _card(name, rel):
    return (f'      <li><a class="report" href="{esc(rel)}">\n'
            f'        <h2>{esc(TITLES.get(name, name))}</h2>\n'
            f'        <p>{esc(NOTES.get(name, ""))}</p>\n'
            f'      </a></li>')

def _failures(failed):
    if not failed:
        return ""
    items = "\n".join(
        f"        <li><code>{esc(name)}</code> — {esc(exc)}</li>" for name, exc in failed)
    return ('    <section class="failed">\n'
            '      <h2>Did not run</h2>\n'
            f'      <ul>\n{items}\n      </ul>\n'
            '    </section>\n')

def write_index(root, repo_name, written, failed):
    """Write the landing page linking each report. Returns its path."""
    os.makedirs(root, exist_ok=True)
    cards = "\n".join(
        _card(name, os.path.join(os.path.basename(path), "index.html"))
        for name, path in written.items())
    n = len(written)
    sub = f"{n} of 6 reads complete." if failed else "Six reads of one codebase."
    page = PAGE.format(name=esc(repo_name), sub=esc(sub), cards=cards,
                       failures=_failures(failed))
    path = os.path.join(root, "index.html")
    with open(path, "w") as fh:
        fh.write(page)
    return path
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_index.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git status --porcelain -- 'ch*'   # must be empty
git add src/crack/core/index.py tests/test_index.py
git commit -m "feat: crack all landing page linking the six reports"
```

---

### Task 6: The CLI

`cli.py` builds one subparser per analysis plus an `all` subcommand, validates the repo path before any LLM call, and dispatches to the runner. Under `all`, one failing analysis does not stop the rest; the command reports the failures and exits non-zero.

**Files:**

- Create: `src/crack/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**

- Consumes: `crack.analyses.ANALYSIS_NAMES` and `load` (Task 2), `crack.core.runner.run_analysis` and `repo_name_of` (Task 4), `crack.core.index.write_index` (Task 5).
- Produces: `crack.cli.build_parser() -> argparse.ArgumentParser` and `crack.cli.main(argv=None) -> int`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_cli.py`:

```python
import os
import types
import pytest
from crack import cli

def test_parser_has_all_seven_subcommands():
    parser = cli.build_parser()
    action = next(a for a in parser._actions if a.dest == "command")
    assert set(action.choices) == {
        "backend", "architecture", "interfaces", "schema",
        "git-history", "product-intent", "all",
    }

def test_per_analysis_flags_are_wired():
    parser = cli.build_parser()
    args = parser.parse_args(["git-history", "/tmp/x", "--max-graves", "3"])
    assert args.max_graves == 3
    args = parser.parse_args(["schema", "/tmp/x", "--schema", "db/schema.rb"])
    assert args.schema == "db/schema.rb"
    args = parser.parse_args(["product-intent", "/tmp/x", "--include", "src/**"])
    assert args.include == ["src/**"]

def test_missing_repo_path_exits_before_running(tmp_path, capsys):
    code = cli.main(["backend", str(tmp_path / "nope")])
    assert code != 0
    assert "not a directory" in capsys.readouterr().err

def test_single_analysis_dispatches_to_runner(tmp_path, monkeypatch):
    repo = tmp_path / "r"
    repo.mkdir()
    calls = []
    monkeypatch.setattr(cli, "load", lambda name: types.SimpleNamespace(NAME=name))
    monkeypatch.setattr(
        cli, "run_analysis",
        lambda analysis, repo_path, out_root, args: calls.append(analysis.NAME) or "/out")
    assert cli.main(["backend", str(repo), "--out", str(tmp_path / "o")]) == 0
    assert calls == ["backend"]

def test_all_isolates_one_failing_analysis(tmp_path, monkeypatch, capsys):
    repo = tmp_path / "r"
    repo.mkdir()
    ran = []

    def fake_run(analysis, repo_path, out_root, args):
        if analysis.NAME == "schema":
            raise RuntimeError("no schema found")
        ran.append(analysis.NAME)
        return os.path.join(out_root, analysis.NAME)

    monkeypatch.setattr(cli, "load", lambda name: types.SimpleNamespace(
        NAME=name))
    monkeypatch.setattr(cli, "run_analysis", fake_run)
    monkeypatch.setattr(cli, "write_index", lambda *a, **k: "/out/index.html")

    code = cli.main(["all", str(repo), "--out", str(tmp_path / "o")])

    assert code != 0
    assert len(ran) == 5
    assert "schema" not in ran
    assert "schema" in capsys.readouterr().err
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'crack.cli'`

- [ ] **Step 3: Write `src/crack/cli.py`**

```python
"""One command that reads a codebase six ways."""
import argparse
import os
import sys

from .analyses import ANALYSIS_NAMES, load
from .core.index import write_index
from .core.runner import run_analysis, repo_name_of

DEFAULT_OUT_ROOT = "crack-output"

DESCRIPTIONS = {
    "product-intent": "reverse engineer the product story from the source",
    "git-history": "read the roadmap already written in the git log",
    "schema": "tour the data model and how it migrated",
    "interfaces": "map the API surface and trace one action",
    "architecture": "map a multi-service architecture in three passes",
    "backend": "read a backend as the six layers every request flows through",
}

def _add_common(parser):
    parser.add_argument("repo_path", help="path to the repository to read")
    parser.add_argument("--out", default=DEFAULT_OUT_ROOT,
                        help=f"output root (default: {DEFAULT_OUT_ROOT}/)")

def build_parser():
    parser = argparse.ArgumentParser(
        prog="crack", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    subs = parser.add_subparsers(dest="command", required=True)

    for name in ANALYSIS_NAMES:
        sub = subs.add_parser(name, help=DESCRIPTIONS[name])
        _add_common(sub)
        _add_analysis_arguments(sub, name)

    every = subs.add_parser("all", help="run all six analyses on one repo")
    _add_common(every)
    for name in ANALYSIS_NAMES:
        _add_analysis_arguments(every, name)
    return parser

def _add_analysis_arguments(parser, name):
    """Let an analysis add its own flags. Import failures must not break --help."""
    try:
        analysis = load(name)
    except Exception:
        return
    add = getattr(analysis, "add_arguments", None)
    if add is not None:
        add(parser)

def main(argv=None):
    args = build_parser().parse_args(argv)

    if not os.path.isdir(args.repo_path):
        print(f"crack: {args.repo_path} is not a directory", file=sys.stderr)
        return 2

    names = ANALYSIS_NAMES if args.command == "all" else (args.command,)
    written, failed = {}, []

    for name in names:
        analysis = load(name)
        print(f"\n=== {name} ===")
        try:
            written[name] = run_analysis(analysis, args.repo_path, args.out, args)
        except Exception as exc:               # one analysis must not stop the rest
            if args.command != "all":
                raise
            failed.append((name, exc))
            print(f"crack: {name} failed: {exc}", file=sys.stderr)

    if args.command == "all":
        root = os.path.join(args.out, repo_name_of(args.repo_path))
        index = write_index(root, repo_name_of(args.repo_path), written, failed)
        print(f"\nWrote {index}")

    for path in written.values():
        print(f"  Open {os.path.join(path, 'index.html')}")

    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_cli.py -v`
Expected: 5 passed.

- [ ] **Step 5: Verify the console script works**

Run: `crack --help`
Expected: usage text listing all seven subcommands.

- [ ] **Step 6: Commit**

```bash
git status --porcelain -- 'ch*'   # must be empty
git add src/crack/cli.py tests/test_cli.py
git commit -m "feat: crack CLI with six analyses and an all subcommand"
```

---

### Task 7: The backend analysis (from ch10)

The first port, and the one that proves the engine. It also establishes the parity harness every later analysis reuses: load the chapter's renderer straight off disk, feed both it and the new engine the same fixture `shared` dict, and compare after applying the named unifications.

**Files:**

- Create: `tests/conftest.py`
- Create: `src/crack/analyses/backend/__init__.py`
- Create: `src/crack/analyses/backend/nodes.py` (from `ch10-backend/workflow/nodes.py`)
- Create: `src/crack/analyses/backend/backend_crawl.py` (copy of `ch10-backend/workflow/backend_crawl.py`)
- Create: `src/crack/analyses/backend/prompts/{pipeline,layer-code,trace}.md` (copies)
- Test: `tests/test_parity_backend.py`

**Interfaces:**

- Consumes: `crack.core.render.Section`, `Theme`, `render_html`, `render_markdown` (Task 3); `crack.core.OverviewNode`, `call_llm`, `read_prompt`, `fill`, `extract_mermaid` (Task 1).
- Produces: the module `crack.analyses.backend` exposing `NAME`, `THEME`, `SECTIONS`, `ENV_DEFAULTS`, `build_flow()`, `overview_spec(shared)`, `init_shared(args, out_dir)`; and the pytest helper `chapter_render(chapter_dir)` in `conftest.py`.

- [ ] **Step 1: Write the parity harness**

Create `tests/conftest.py`:

```python
"""Shared test helpers. The parity tests load each chapter's renderer off disk."""
import importlib.util
import pathlib
import sys

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

@pytest.fixture(scope="session")
def chapter_render():
    """Load a chapter's render.py as a module, without installing the chapter."""
    def _load(chapter_dir):
        workflow = REPO_ROOT / chapter_dir / "workflow"
        path = workflow / "render.py"
        name = f"_chapter_render_{chapter_dir.replace('-', '_')}"
        if name in sys.modules:
            return sys.modules[name]
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        # The chapter renderers sys.path.insert to reach utils/; let them.
        sys.path.insert(0, str(workflow))
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.remove(str(workflow))
        return module
    return _load

def apply_unifications(html, pairs):
    """Rewrite a chapter's HTML with the deliberate unifications applied.

    Each pair is (chapter_text, unified_text). Every pair must actually match,
    so a unification that silently stops applying fails the test.
    """
    for old, new in pairs:
        if old != new:
            assert old in html, f"unification no longer applies: {old!r}"
            html = html.replace(old, new)
    return html
```

- [ ] **Step 2: Write the failing parity test**

Create `tests/test_parity_backend.py`:

````python
"""The ported backend renderer must match ch10's, modulo the named unifications."""
import pytest
from conftest import apply_unifications
from crack.analyses import backend
from crack.core import render

# Every difference between ch10's page and the engine's, stated explicitly.
UNIFICATIONS = [
    ("max-height: 74vh", "max-height: 72vh"),
    ("font-size: .95rem", "font-size: .96rem"),
    ("margin: .3em 0; color: #344054; line-height: 1.55;",
     "margin: .28em 0; color: #344054; line-height: 1.55;"),
    ("pre code { padding: 0; font-size: .73rem",
     "pre code { padding: 0; font-size: .74rem"),
]

SHARED = {
    "repo_path": "/tmp/zulip",
    "codebase": "irrelevant to rendering",
    "layer_counts": {"route": 12, "middleware": 3, "handler": 20,
                     "service": 8, "database": 15, "response": 4},
    "pipeline_diagram": "graph LR;\nroute-->handler;",
    "pipeline_md": "### Route\nWhere URLs bind.\n\n### Handler\nWhere work starts.",
    "layercode_md": "### Service (novel)\nA custom queue.\n\n```python\ndef enqueue():\n    pass\n```",
    "trace_md": "**Endpoint:** POST /messages\n\n### Step 1\nRoute matches.",
    "trace_endpoint": "POST /messages",
    "overview": {"welcome": "Zulip routes every message through six layers.",
                 "intros": {"The pipeline": "Start here.",
                            "The code": "Only the odd layers.",
                            "The trace": "One message, end to end."}},
}

def test_html_matches_chapter(chapter_render):
    chapter = chapter_render("ch10-backend")
    expected = apply_unifications(chapter.render_html("zulip", SHARED), UNIFICATIONS)
    actual = render.render_html(backend, "zulip", SHARED)
    assert actual == expected

def test_markdown_matches_chapter(chapter_render):
    chapter = chapter_render("ch10-backend")
    assert render.render_markdown(backend, "zulip", SHARED) == \
        chapter.render_markdown("zulip", SHARED)

def test_analysis_surface():
    assert backend.NAME == "backend"
    assert backend.ENV_DEFAULTS == {"LLM_MAX_OUTPUT_TOKENS": "32768"}
    assert [s.key for s in backend.SECTIONS] == [
        "pipeline_md", "layercode_md", "trace_md"]

def test_init_shared_carries_repo_path():
    import types
    args = types.SimpleNamespace(repo_path="/tmp/zulip")
    assert backend.init_shared(args, "/out")["repo_path"] == "/tmp/zulip"
````

- [ ] **Step 3: Run the test to verify it fails**

Run: `pytest tests/test_parity_backend.py -v`
Expected: FAIL with `ImportError: cannot import name 'backend' from 'crack.analyses'`

- [ ] **Step 4: Copy the crawl helper and prompts**

```bash
mkdir -p src/crack/analyses/backend/prompts
cp ch10-backend/workflow/backend_crawl.py src/crack/analyses/backend/backend_crawl.py
cp ch10-backend/prompts/pipeline.md   src/crack/analyses/backend/prompts/
cp ch10-backend/prompts/layer-code.md src/crack/analyses/backend/prompts/
cp ch10-backend/prompts/trace.md      src/crack/analyses/backend/prompts/
```

Then open `src/crack/analyses/backend/backend_crawl.py` and apply the import rewrite: delete any `sys.path.insert(...)` line and its now-unused `import sys`, and change `from utils import ...` to `from crack.core import ...`. Nothing else changes.

- [ ] **Step 5: Port the nodes**

Copy `ch10-backend/workflow/nodes.py` to `src/crack/analyses/backend/nodes.py`, then apply exactly these edits. The node class bodies are unchanged.

Replace the import block (`ch10-backend/workflow/nodes.py:11-25`) with:

```python
import os
import re

from pocketflow import Node

from crack.core import call_llm, read_prompt, fill, extract_mermaid
from . import backend_crawl as bc

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), 'prompts')

def load_prompt(name):
    return read_prompt(PROMPTS_DIR, name)
```

Delete the `overview_spec` function from the bottom of the file; it moves to `__init__.py` in the next step. Keep `BuildBundle`, `Pipeline`, `LayerCode`, and `Trace` exactly as they are.

- [ ] **Step 6: Write the analysis module**

Create `src/crack/analyses/backend/__init__.py`:

```python
"""Read a backend as the six layers every request flows through (ch10)."""
import os

from pocketflow import Flow

from crack.core import OverviewNode
from crack.core.render import Section, Theme
from .nodes import BuildBundle, Pipeline, LayerCode, Trace

NAME = "backend"

# The pipeline and layer-code passes emit a card per layer with code excerpts,
# which is more output than the default cap allows.
ENV_DEFAULTS = {"LLM_MAX_OUTPUT_TOKENS": "32768"}

SECTIONS = [
    Section("01", "The pipeline",
            "route &middot; middleware &middot; handler &middot; service &middot; database &middot; response",
            "pipe", 400, "pipeline_md"),
    Section("02", "The code",
            "only the layers the team built in a non-standard way",
            "code", 520, "layercode_md"),
    Section("03", "The trace",
            "one request, all six layers, and where state changes",
            "trace", 460, "trace_md"),
]

def _subtitle(shared):
    from crack.core.render import md
    welcome = (shared.get("overview") or {}).get("welcome", "")
    endpoint = shared.get("trace_endpoint", "")
    return md(welcome) or (
        f"Every request flows through the same six layers. Core endpoint: {md(endpoint)}"
        if endpoint else "Every backend request flows through the same six layers.")

def _hero_prefix(shared):
    diagram = shared.get("pipeline_diagram", "")
    if not diagram:
        return ""
    return ('    <section class="hero-diagram">\n'
            '      <div class="hero-diagram-cap">The request pipeline &mdash; six layers, every time</div>\n'
            f'      <div class="diagram"><pre class="mermaid">{diagram}</pre></div>\n'
            '    </section>\n')

def _footer(shared):
    c = shared.get("layer_counts", {})
    return (f"Read as six layers &middot; {c.get('route', 0)} routes &middot; "
            f"{c.get('handler', 0)} handlers &middot; {c.get('service', 0)} services "
            f"&middot; {c.get('database', 0)} models.")

def _md_preamble(shared):
    endpoint = shared.get("trace_endpoint")
    return f"_Core endpoint: {endpoint}_\n" if endpoint else ""

THEME = Theme(
    title_suffix="backend", eyebrow="Backend",
    accent="#4f46e5", accent_soft="#eef2ff",
    hero_from="#1e1b4b", hero_to="#0f0d2b",
    eyebrow_color="#a5b4fc", eyebrow_bar="#818cf8",
    sub_color="#d6d8f5", card_top_from="#fafaff",
    subtitle=_subtitle, footer=_footer, md_preamble=_md_preamble,
    hero_prefix=_hero_prefix,
)

def init_shared(args, out_dir):
    return {"repo_path": args.repo_path}

def build_flow():
    bundle, pipeline = BuildBundle(), Pipeline()
    layercode, trace = LayerCode(), Trace()
    overview = OverviewNode(overview_spec)
    bundle >> pipeline >> layercode >> trace >> overview
    return Flow(start=bundle)

def overview_spec(shared):
    name = os.path.basename(shared["repo_path"].rstrip("/")) or shared["repo_path"]
    c = shared.get("layer_counts", {})
    return {
        "name": name,
        "what": "a backend as the six layers every request flows through",
        "sections": [
            ("The pipeline", "the six layers every request flows through, with a count for each"),
            ("The code", "the one or two layers the team built in an unusual way, worth reading closely"),
            ("The trace", "one real request walked through all six layers, and where its data becomes durable"),
        ],
        "facts": (f"Core endpoint: {shared.get('trace_endpoint', '')}. "
                  f"Layer file counts — route {c.get('route', 0)}, middleware {c.get('middleware', 0)}, "
                  f"handler {c.get('handler', 0)}, service {c.get('service', 0)}, "
                  f"database {c.get('database', 0)}, response {c.get('response', 0)}."),
    }
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `pytest tests/test_parity_backend.py -v`
Expected: 4 passed.

If the HTML parity test fails, diff the two strings and decide honestly: either the engine has a bug (fix the engine) or the difference is deliberate (add it to `UNIFICATIONS` with a comment saying why). Never loosen the assertion.

- [ ] **Step 8: Run the whole suite**

Run: `pytest -v`
Expected: all green.

- [ ] **Step 9: Verify no chapter file changed**

Run: `git status --porcelain -- 'ch*'`
Expected: empty output.

- [ ] **Step 10: Commit**

```bash
git add tests/conftest.py tests/test_parity_backend.py src/crack/analyses/backend
git commit -m "feat: backend analysis ported from ch10 with parity tests"
```

---

### Task 8: The architecture analysis (from ch09)

Structurally the same shape as backend: three sections, a Mermaid hero, no custom hooks. Its unification list is shorter because ch09 already sits on most of the unified values; the table CSS it never had is now present.

**Files:**

- Create: `src/crack/analyses/architecture/__init__.py`
- Create: `src/crack/analyses/architecture/nodes.py` (from `ch09-architecture/workflow/nodes.py`)
- Create: `src/crack/analyses/architecture/arch_crawl.py` (copy of `ch09-architecture/workflow/arch_crawl.py`)
- Create: `src/crack/analyses/architecture/prompts/{inventory,tech-stack,trace-request}.md` (copies)
- Test: `tests/test_parity_architecture.py`

**Interfaces:**

- Consumes: `crack.core.render.Section`, `Theme` (Task 3); `crack.core.OverviewNode` (Task 1); the `chapter_render` fixture and `apply_unifications` (Task 7).
- Produces: the module `crack.analyses.architecture` exposing `NAME`, `THEME`, `SECTIONS`, `ENV_DEFAULTS`, `build_flow()`, `overview_spec(shared)`, `init_shared(args, out_dir)`.

- [ ] **Step 1: Write the failing parity test**

Create `tests/test_parity_architecture.py`:

```python
"""The ported architecture renderer must match ch09's, modulo the named unifications."""
from conftest import apply_unifications
from crack.analyses import architecture
from crack.core import render

# ch09 has no table CSS; the engine adds it for every card-family analysis.
TABLE_CSS = """  table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: .8rem; }
"""

UNIFICATIONS = []  # ch09 already sits on every unified value

SHARED = {
    "repo_path": "/tmp/nats",
    "arch_diagram": "graph LR;\ngateway-->auth;",
    "arch_stats": {"config_files": 9, "deps": 42, "integrations": 6},
    "shape_verdict": "A gateway in front of four services.",
    "inventory_md": "### Gateway (run)\nThe front door.\n\n### Auth (rent)\nAuth0.",
    "techstack_md": "### Gateway\nEnvoy 1.29.\n\n### Auth\nAuth0 tenant.",
    "trace_md": "### Hop 1\nClient hits the gateway.",
    "overview": {"welcome": "NATS runs four services behind one gateway.",
                 "intros": {"The inventory": "Every node.",
                            "Tech stack": "The real technology.",
                            "The trace": "One request."}},
}

def test_html_matches_chapter(chapter_render):
    chapter = chapter_render("ch09-architecture")
    expected = apply_unifications(chapter.render_html("nats", SHARED), UNIFICATIONS)
    actual = render.render_html(architecture, "nats", SHARED)
    # The only structural addition is the table CSS block ch09 lacked.
    assert actual.replace(TABLE_CSS, "") == expected

def test_markdown_matches_chapter(chapter_render):
    chapter = chapter_render("ch09-architecture")
    assert render.render_markdown(architecture, "nats", SHARED) == \
        chapter.render_markdown("nats", SHARED)

def test_analysis_surface():
    assert architecture.NAME == "architecture"
    assert architecture.ENV_DEFAULTS == {"LLM_MAX_OUTPUT_TOKENS": "32768"}
    assert [s.key for s in architecture.SECTIONS] == [
        "inventory_md", "techstack_md", "trace_md"]
    assert [s.width for s in architecture.SECTIONS] == [380, 420, 460]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_parity_architecture.py -v`
Expected: FAIL with `ImportError: cannot import name 'architecture' from 'crack.analyses'`

- [ ] **Step 3: Copy the crawl helper and prompts**

```bash
mkdir -p src/crack/analyses/architecture/prompts
cp ch09-architecture/workflow/arch_crawl.py src/crack/analyses/architecture/arch_crawl.py
cp ch09-architecture/prompts/inventory.md     src/crack/analyses/architecture/prompts/
cp ch09-architecture/prompts/tech-stack.md    src/crack/analyses/architecture/prompts/
cp ch09-architecture/prompts/trace-request.md src/crack/analyses/architecture/prompts/
```

In `arch_crawl.py`, delete any `sys.path.insert(...)` line and its now-unused `import sys`, and change `from utils import ...` to `from crack.core import ...`.

- [ ] **Step 4: Port the nodes**

Copy `ch09-architecture/workflow/nodes.py` to `src/crack/analyses/architecture/nodes.py`. Replace its import block with:

```python
import os
import re

from pocketflow import Node

from crack.core import call_llm, read_prompt, fill, extract_mermaid
from . import arch_crawl as ac

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), 'prompts')

def load_prompt(name):
    return read_prompt(PROMPTS_DIR, name)
```

Keep `BuildBundle`, `Inventory`, `TechStack`, and `TraceRequest` exactly as they are. Delete `overview_spec` from the bottom; it moves to `__init__.py`.

If the chapter file aliases the crawl module under a different name than `ac`, keep the chapter's alias so the node bodies need no edits.

- [ ] **Step 5: Write the analysis module**

Create `src/crack/analyses/architecture/__init__.py`:

```python
"""Map a multi-service architecture in three passes (ch09)."""
import os

from pocketflow import Flow

from crack.core import OverviewNode
from crack.core.render import Section, Theme, md
from .nodes import BuildBundle, Inventory, TechStack, TraceRequest

NAME = "architecture"

ENV_DEFAULTS = {"LLM_MAX_OUTPUT_TOKENS": "32768"}

SECTIONS = [
    Section("01", "The inventory",
            "every node, sorted by band: run · rent · call · client",
            "inv", 380, "inventory_md"),
    Section("02", "Tech stack",
            "open each box: the real technology inside the label",
            "tech", 420, "techstack_md"),
    Section("03", "The trace",
            "one request, hop by hop, and how each variant differs",
            "trace", 460, "trace_md"),
]

def _subtitle(shared):
    welcome = (shared.get("overview") or {}).get("welcome", "")
    return (md(welcome) or md(shared.get("shape_verdict", ""))
            or "A multi-service architecture, read three ways.")

def _hero_prefix(shared):
    diagram = shared.get("arch_diagram", "")
    if not diagram:
        return ""
    return ('    <section class="hero-diagram">\n'
            '      <div class="hero-diagram-cap">The whole system on one map</div>\n'
            f'      <div class="diagram"><pre class="mermaid">{diagram}</pre></div>\n'
            '    </section>\n')

def _footer(shared):
    stats = shared.get("arch_stats", {})
    return (f"Overlaid from {stats.get('config_files', 0)} config files, "
            f"{stats.get('deps', 0)} dependencies, "
            f"{stats.get('integrations', 0)} integrations.")

def _md_preamble(shared):
    verdict = shared.get("shape_verdict")
    return f"**Shape verdict:** {verdict}\n" if verdict else ""

THEME = Theme(
    title_suffix="architecture", eyebrow="Architecture",
    accent="#d97706", accent_soft="#fffbeb",
    hero_from="#3a2607", hero_to="#1c1203",
    eyebrow_color="#fcd34d", eyebrow_bar="#f59e0b",
    sub_color="#eee0c4", card_top_from="#fffdf7",
    subtitle=_subtitle, footer=_footer, md_preamble=_md_preamble,
    hero_prefix=_hero_prefix,
)

def init_shared(args, out_dir):
    return {"repo_path": args.repo_path}

def build_flow():
    bundle, inventory = BuildBundle(), Inventory()
    tech, trace = TechStack(), TraceRequest()
    overview = OverviewNode(overview_spec)
    bundle >> inventory >> tech >> trace >> overview
    return Flow(start=bundle)
```

Then append the `overview_spec` function you deleted from `nodes.py` in Step 4, unchanged.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `pytest tests/test_parity_architecture.py -v`
Expected: 3 passed.

- [ ] **Step 7: Run the whole suite and check the chapters**

```bash
pytest -v
git status --porcelain -- 'ch*'   # must be empty
```

- [ ] **Step 8: Commit**

```bash
git add src/crack/analyses/architecture tests/test_parity_architecture.py
git commit -m "feat: architecture analysis ported from ch09 with parity tests"
```

---

### Task 9: The interfaces analysis (from ch08)

The first analysis that exercises both hooks. Section 02 is omitted entirely when its key is empty. Section 04 hoists a Mermaid diagram above the rail through `prefix` and builds one hand-made card through `cards`. Its hero is a computed bar chart, not a diagram.

**Files:**

- Create: `src/crack/analyses/interfaces/__init__.py`
- Create: `src/crack/analyses/interfaces/nodes.py` (from `ch08-interfaces/workflow/nodes.py`)
- Create: `src/crack/analyses/interfaces/routes_find.py` (copy of `ch08-interfaces/workflow/routes_find.py`)
- Create: `src/crack/analyses/interfaces/prompts/{api-menu,trace-action,endpoint-sequence}.md` (copies)
- Test: `tests/test_parity_interfaces.py`

**Interfaces:**

- Consumes: `crack.core.render.Section`, `Theme`, `card`, `esc`, `extract_mermaid`, `strip_mermaid`, `md` (Task 3); `crack.core.OverviewNode` (Task 1).
- Produces: the module `crack.analyses.interfaces` exposing `NAME`, `THEME`, `SECTIONS`, `ENV_DEFAULTS`, `build_flow()`, `overview_spec(shared)`, `init_shared(args, out_dir)`.

- [ ] **Step 1: Write the failing parity test**

Create `tests/test_parity_interfaces.py`:

````python
"""The ported interfaces renderer must match ch08's, modulo the named unifications."""
from conftest import apply_unifications
from crack.analyses import interfaces
from crack.core import render

UNIFICATIONS = [
    ("font-size: .98rem", "font-size: .96rem"),
    ("margin: .28em 0; color: #344054; line-height: 1.5;",
     "margin: .28em 0; color: #344054; line-height: 1.55;"),
]

SHARED = {
    "repo_path": "/tmp/gitea",
    "opener": "A forge API with 90 endpoints.",
    "route_files": ["routers/api/v1/repo.go", "routers/api/v1/user.go"],
    "group_names": ["Repositories (34 endpoints)", "Users (21 endpoints)"],
    "groups_md": "### Repositories\nThe biggest group.\n\n### Users\nProfiles and keys.",
    "tour_md": "### Repositories\nWhere the product lives.",
    "flows_md": "### Open a pull request\nFour endpoints, in order.",
    "sequence_md": "```mermaid\nsequenceDiagram\nA->>B: POST\n```\n\nThe body of the sequence.",
    "sequence_endpoint": "POST /repos/{owner}/{repo}/pulls",
    "overview": {"welcome": "Gitea exposes a forge as ninety endpoints.",
                 "intros": {"Feature menu": "Grouped by feature.",
                            "The tour": "The telling groups.",
                            "Action flows": "One gesture.",
                            "Endpoint sequence": "Inside one call."}},
}

def test_html_matches_chapter(chapter_render):
    chapter = chapter_render("ch08-interfaces")
    expected = apply_unifications(chapter.render_html("gitea", SHARED), UNIFICATIONS)
    assert render.render_html(interfaces, "gitea", SHARED) == expected

def test_html_matches_chapter_when_tour_is_absent(chapter_render):
    """Section 02 is dropped entirely, so the page runs 01, 03, 04."""
    shared = dict(SHARED)
    shared.pop("tour_md")
    chapter = chapter_render("ch08-interfaces")
    expected = apply_unifications(chapter.render_html("gitea", shared), UNIFICATIONS)
    actual = render.render_html(interfaces, "gitea", shared)
    assert actual == expected
    assert "The tour" not in actual

def test_markdown_matches_chapter(chapter_render):
    chapter = chapter_render("ch08-interfaces")
    assert render.render_markdown(interfaces, "gitea", SHARED) == \
        chapter.render_markdown("gitea", SHARED)

def test_sequence_section_hoists_the_diagram():
    html = render.render_html(interfaces, "gitea", SHARED)
    assert html.index("sequenceDiagram") < html.index('class="rail seq"')
    assert html.count("sequenceDiagram") == 1   # stripped from the card body

def test_analysis_surface():
    assert interfaces.NAME == "interfaces"
    assert interfaces.ENV_DEFAULTS == {"LLM_MAX_OUTPUT_TOKENS": "32768"}
    assert [s.key for s in interfaces.SECTIONS] == [
        "groups_md", "tour_md", "flows_md", "sequence_md"]
    assert [s.width for s in interfaces.SECTIONS] == [380, 380, 440, 560]
````

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_parity_interfaces.py -v`
Expected: FAIL with `ImportError: cannot import name 'interfaces' from 'crack.analyses'`

- [ ] **Step 3: Copy the route finder and prompts**

```bash
mkdir -p src/crack/analyses/interfaces/prompts
cp ch08-interfaces/workflow/routes_find.py src/crack/analyses/interfaces/routes_find.py
cp ch08-interfaces/prompts/api-menu.md          src/crack/analyses/interfaces/prompts/
cp ch08-interfaces/prompts/trace-action.md      src/crack/analyses/interfaces/prompts/
cp ch08-interfaces/prompts/endpoint-sequence.md src/crack/analyses/interfaces/prompts/
```

In `routes_find.py`, delete any `sys.path.insert(...)` line and its now-unused `import sys`, and change `from utils import ...` to `from crack.core import ...`.

- [ ] **Step 4: Port the nodes**

Copy `ch08-interfaces/workflow/nodes.py` to `src/crack/analyses/interfaces/nodes.py`. Replace its import block with:

```python
import os
import re

from pocketflow import Node

from crack.core import call_llm, read_prompt, fill, extract_mermaid
from . import routes_find as rf

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), 'prompts')

def load_prompt(name):
    return read_prompt(PROMPTS_DIR, name)
```

Keep `FindRoutes`, `ApiMenu`, `TraceActions`, and `EndpointSequence` exactly as they are. Delete `overview_spec`; it moves to `__init__.py`. Keep the chapter's alias for the route-finder module if it differs from `rf`.

- [ ] **Step 5: Write the analysis module**

Create `src/crack/analyses/interfaces/__init__.py`:

```python
"""Map the API surface and trace one action through it (ch08)."""
import os
import re

from pocketflow import Flow

from crack.core import OverviewNode
from crack.core.render import (
    Section, Theme, card, esc, extract_mermaid, md, strip_mermaid)
from .nodes import FindRoutes, ApiMenu, TraceActions, EndpointSequence

NAME = "interfaces"

ENV_DEFAULTS = {"LLM_MAX_OUTPUT_TOKENS": "32768"}

def _sequence_prefix(shared):
    diagram = extract_mermaid(shared.get("sequence_md", ""))
    return (f'    <div class="diagram"><pre class="mermaid">{diagram}</pre></div>\n'
            if diagram else "")

def _sequence_cards(shared, body_md):
    """One hand-built card holding the sequence body, with the fence removed."""
    body = strip_mermaid(body_md)
    if not body:
        return ""
    return card(esc(shared.get("sequence_endpoint") or "Sequence"), body)

SECTIONS = [
    Section("01", "Feature menu",
            "every endpoint, grouped by feature, biggest first",
            "menu", 380, "groups_md"),
    Section("02", "The tour",
            "the groups that say the most about the product",
            "tour", 380, "tour_md", when_empty="omit"),
    Section("03", "Action flows",
            "one gesture, every lane it touches, in order",
            "flows", 440, "flows_md"),
    Section("04", "Endpoint sequence",
            "one endpoint, every message inside it",
            "seq", 560, "sequence_md",
            prefix=_sequence_prefix, cards=_sequence_cards),
]

def _subtitle(shared):
    welcome = (shared.get("overview") or {}).get("welcome", "")
    return (md(welcome) or md(shared.get("opener", ""))
            or "The API surface, read three ways.")

def _hero_prefix(shared):
    """Feature groups sized by endpoint count, parsed out of the group names."""
    groups = []
    for name in shared.get("group_names", []):
        m = re.match(r'(.+?)\s*\((\d+)', name)
        if m:
            groups.append((m.group(1).strip(), int(m.group(2))))
    if not groups:
        return ""
    biggest = max(n for _, n in groups) or 1
    rows = "".join(
        f'<div class="gc-row"><div class="gc-name">{esc(name)}</div>'
        f'<div class="gc-track"><div class="gc-bar" '
        f'style="width:{max(7, round(n / biggest * 100))}%">{n}</div></div></div>'
        for name, n in groups)
    total = sum(n for _, n in groups)
    return (
        '    <section class="hero-diagram">\n'
        f'      <div class="hero-diagram-cap">The API surface at a glance &mdash; '
        f'{total} endpoints across {len(groups)} feature groups</div>\n'
        f'      <div class="groupchart">{rows}</div>\n'
        '    </section>\n'
    )

def _footer(shared):
    return (f"Read from {len(shared.get('route_files', []))} route files &middot; "
            f"{len(shared.get('group_names', []))} feature groups.")

def _md_preamble(shared):
    opener = shared.get("opener")
    return opener.strip() + "\n" if opener else ""

THEME = Theme(
    title_suffix="interfaces", eyebrow="Interfaces",
    accent="#0d9488", accent_soft="#effcf9",
    hero_from="#0f3d38", hero_to="#06201d",
    eyebrow_color="#5eead4", eyebrow_bar="#2dd4bf",
    sub_color="#cbeee7", card_top_from="#f6fdfb",
    subtitle=_subtitle, footer=_footer, md_preamble=_md_preamble,
    hero_prefix=_hero_prefix,
)

def init_shared(args, out_dir):
    return {"repo_path": args.repo_path}

def build_flow():
    find, menu = FindRoutes(), ApiMenu()
    trace, seq = TraceActions(), EndpointSequence()
    overview = OverviewNode(overview_spec)
    find >> menu >> trace >> seq >> overview
    return Flow(start=find)
```

Then append the `overview_spec` function you deleted from `nodes.py`, unchanged.

- [ ] **Step 6: Add the bar-chart CSS to the engine**

The `.groupchart` rules live only in ch08 today, but the page template is shared, so they belong in `render.py`'s `PAGE`. Copy the block at `ch08-interfaces/workflow/render.py:120-129` verbatim into `PAGE`, immediately after the `.diagram` rules. It is inert for analyses whose hero is not a chart.

Remember the doubled braces: inside a `str.format` template every literal `{` and `}` must be written `{{` and `}}`.

- [ ] **Step 7: Run the tests to verify they pass**

Run: `pytest tests/test_parity_interfaces.py tests/test_parity_backend.py tests/test_parity_architecture.py -v`
Expected: 12 passed. The two earlier parity tests must still pass after the CSS addition; if they fail, the `.groupchart` block landed in the wrong place.

- [ ] **Step 8: Run the whole suite and check the chapters**

```bash
pytest -v
git status --porcelain -- 'ch*'   # must be empty
```

- [ ] **Step 9: Commit**

```bash
git add src/crack/analyses/interfaces src/crack/core/render.py tests/test_parity_interfaces.py
git commit -m "feat: interfaces analysis ported from ch08 with parity tests"
```

---

### Task 10: The schema analysis (from ch07)

The last card-family port. It exercises the `skip-note` mode (section 04 renders a head with no rail when there are too few migrations) and the `page_name` hook (the page is titled with the product name, not the repo directory).

**Files:**

- Create: `src/crack/analyses/schema/__init__.py`
- Create: `src/crack/analyses/schema/nodes.py` (from `ch07-schema/workflow/nodes.py`)
- Create: `src/crack/analyses/schema/schema_find.py` (copy of `ch07-schema/workflow/schema_find.py`)
- Create: `src/crack/analyses/schema/prompts/{schema-tour,trace-flows,table-deep-dive,migration-acts}.md` (copies)
- Test: `tests/test_parity_schema.py`

**Interfaces:**

- Consumes: `crack.core.render.Section`, `Theme`, `md` (Task 3); `crack.core.OverviewNode` (Task 1).
- Produces: the module `crack.analyses.schema` exposing `NAME`, `THEME`, `SECTIONS`, `ENV_DEFAULTS`, `build_flow()`, `overview_spec(shared)`, `init_shared(args, out_dir)`, `add_arguments(parser)`.

- [ ] **Step 1: Write the failing parity test**

Create `tests/test_parity_schema.py`:

```python
"""The ported schema renderer must match ch07's, modulo the named unifications."""
import argparse
from conftest import apply_unifications
from crack.analyses import schema
from crack.core import render

UNIFICATIONS = [
    ("font-size: .98rem", "font-size: .96rem"),
    ("margin: .3em 0; color: #344054; line-height: 1.55;",
     "margin: .28em 0; color: #344054; line-height: 1.55;"),
    # ch07 is the only chapter using .erd; the engine standardises on .diagram.
    ('<div class="erd">', '<div class="diagram">'),
    (".erd {", ".diagram {"),
]

SHARED = {
    "repo_path": "/tmp/discourse",
    "product_name": "Discourse",
    "one_liner": "A forum with 180 tables.",
    "schema_path": "db/structure.sql",
    "erd": "erDiagram\nUSERS ||--o{ POSTS : writes",
    "table_list": ["users", "posts", "topics"],
    "migration_names": ["20230101_add_users", "20230202_add_posts"],
    "tour_md": "### Users and posts\nThe core cluster.",
    "flows_md": "### Write a post\nThree tables, in order.",
    "deepdive_md": "### posts\nColumns are decisions.",
    "migration_md": "### Act one\nThe forum grew threads.",
    "overview": {"welcome": "Discourse stores a forum in 180 tables.",
                 "intros": {"The tour": "One cluster at a time.",
                            "The flows": "One action.",
                            "Table deep dive": "Columns are decisions.",
                            "Migration history": "The erased roadmap."}},
}

def test_html_matches_chapter(chapter_render):
    chapter = chapter_render("ch07-schema")
    expected = apply_unifications(chapter.render_html("discourse", SHARED), UNIFICATIONS)
    assert render.render_html(schema, "discourse", SHARED) == expected

def test_html_matches_chapter_when_migrations_are_skipped(chapter_render):
    """Section 04 keeps its head and note but grows no rail."""
    shared = dict(SHARED)
    shared.pop("migration_md")
    chapter = chapter_render("ch07-schema")
    expected = apply_unifications(chapter.render_html("discourse", shared), UNIFICATIONS)
    actual = render.render_html(schema, "discourse", shared)
    assert actual == expected
    assert "Migration history" in actual
    assert 'class="rail acts"' not in actual

def test_markdown_matches_chapter(chapter_render):
    chapter = chapter_render("ch07-schema")
    assert render.render_markdown(schema, "discourse", SHARED) == \
        chapter.render_markdown("discourse", SHARED)

def test_markdown_skip_branch_matches_chapter(chapter_render):
    shared = dict(SHARED)
    shared.pop("migration_md")
    chapter = chapter_render("ch07-schema")
    assert render.render_markdown(schema, "discourse", shared) == \
        chapter.render_markdown("discourse", shared)

def test_page_is_titled_with_the_product_name():
    html = render.render_html(schema, "discourse-repo-dir", SHARED)
    assert "<title>Discourse: schema</title>" in html

def test_schema_flag_reaches_shared():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path")
    schema.add_arguments(parser)
    args = parser.parse_args(["/tmp/x", "--schema", "db/structure.sql"])
    assert schema.init_shared(args, "/out")["schema_override"] == "db/structure.sql"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_parity_schema.py -v`
Expected: FAIL with `ImportError: cannot import name 'schema' from 'crack.analyses'`

- [ ] **Step 3: Copy the schema finder and prompts**

```bash
mkdir -p src/crack/analyses/schema/prompts
cp ch07-schema/workflow/schema_find.py src/crack/analyses/schema/schema_find.py
cp ch07-schema/prompts/schema-tour.md     src/crack/analyses/schema/prompts/
cp ch07-schema/prompts/trace-flows.md     src/crack/analyses/schema/prompts/
cp ch07-schema/prompts/table-deep-dive.md src/crack/analyses/schema/prompts/
cp ch07-schema/prompts/migration-acts.md  src/crack/analyses/schema/prompts/
```

In `schema_find.py`, delete any `sys.path.insert(...)` line and its now-unused `import sys`, and change `from utils import ...` to `from crack.core import ...`.

- [ ] **Step 4: Port the nodes**

Copy `ch07-schema/workflow/nodes.py` to `src/crack/analyses/schema/nodes.py`. Replace its import block with:

```python
import os
import re

from pocketflow import Node

from crack.core import call_llm, read_prompt, fill, extract_mermaid
from . import schema_find as sf

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), 'prompts')

def load_prompt(name):
    return read_prompt(PROMPTS_DIR, name)
```

Keep `FindSchema`, `SchemaTour`, `TraceFlows`, `TableDeepDive`, and `MigrationActs` exactly as they are. Delete `overview_spec`; it moves to `__init__.py`. Keep the chapter's alias for the schema-finder module if it differs from `sf`.

- [ ] **Step 5: Write the analysis module**

Create `src/crack/analyses/schema/__init__.py`:

```python
"""Tour the data model and the migrations that shaped it (ch07)."""
import os

from pocketflow import Flow

from crack.core import OverviewNode
from crack.core.render import Section, Theme, md
from .nodes import FindSchema, SchemaTour, TraceFlows, TableDeepDive, MigrationActs

NAME = "schema"

ENV_DEFAULTS = {}

def _migration_skip_note(shared):
    n = len(shared.get("migration_names", []))
    return (f"skipped &mdash; only {n} migrations found "
            "(too few, or history squashed)")

def _migration_md_skip_note(shared):
    n = len(shared.get("migration_names", []))
    return f"_Skipped: only {n} migrations found._\n"

SECTIONS = [
    Section("01", "The tour",
            "the schema as a story, one cluster at a time",
            "tour", 400, "tour_md"),
    Section("02", "The flows",
            "one user action, many tables, in order",
            "flows", 400, "flows_md"),
    Section("03", "Table deep dive",
            "columns are decisions, indexes are the hot queries",
            "deep", 480, "deepdive_md"),
    Section("04", "Migration history",
            "the roadmap the live schema erases",
            "acts", 420, "migration_md",
            when_empty="skip-note",
            skip_note=_migration_skip_note,
            md_skip_note=_migration_md_skip_note),
]

def _page_name(shared, name):
    return shared.get("product_name") or name

def _subtitle(shared):
    welcome = (shared.get("overview") or {}).get("welcome", "")
    return (md(welcome) or md(shared.get("one_liner", ""))
            or "The data model, read four ways.")

def _hero_prefix(shared):
    erd = shared.get("erd", "")
    if not erd:
        return ""
    n_tables = len(shared.get("table_list", []))
    return ('    <section class="hero-diagram">\n'
            f'      <div class="hero-diagram-cap">The whole schema at a glance &mdash; '
            f'{n_tables} core tables and how they connect</div>\n'
            f'      <div class="diagram"><pre class="mermaid">{erd}</pre></div>\n'
            '    </section>\n')

def _footer(shared):
    from crack.core.render import esc
    return (f"Read from {esc(shared.get('schema_path', ''))} &middot; "
            f"{len(shared.get('table_list', []))} core tables &middot; "
            f"{len(shared.get('migration_names', []))} migrations.")

def _md_preamble(shared):
    one_liner = shared.get("one_liner")
    return f"_{one_liner}_\n" if one_liner else ""

THEME = Theme(
    title_suffix="schema", eyebrow="Schema",
    accent="#6941c6", accent_soft="#f4f0ff",
    hero_from="#2b1c4d", hero_to="#12091f",
    eyebrow_color="#c4b5fd", eyebrow_bar="#a78bfa",
    sub_color="#d6cff0", card_top_from="#fbfaff",
    subtitle=_subtitle, footer=_footer, md_preamble=_md_preamble,
    hero_prefix=_hero_prefix, page_name=_page_name,
)

def add_arguments(parser):
    parser.add_argument("--schema", default=None,
                        help="path to the schema file, relative to the repo "
                             "(overrides autodetect)")

def init_shared(args, out_dir):
    return {"repo_path": args.repo_path,
            "schema_override": getattr(args, "schema", None)}

def build_flow():
    find, tour = FindSchema(), SchemaTour()
    flows, deep = TraceFlows(), TableDeepDive()
    migrations = MigrationActs()
    overview = OverviewNode(overview_spec)
    find >> tour >> flows >> deep >> migrations >> overview
    return Flow(start=find)
```

Then append the `overview_spec` function you deleted from `nodes.py`, unchanged.

- [ ] **Step 6: Run the tests to verify they pass**

Run: `pytest tests/test_parity_schema.py -v`
Expected: 6 passed.

- [ ] **Step 7: Run the whole suite and check the chapters**

```bash
pytest -v
git status --porcelain -- 'ch*'   # must be empty
```

- [ ] **Step 8: Commit**

```bash
git add src/crack/analyses/schema tests/test_parity_schema.py
git commit -m "feat: schema analysis ported from ch07 with parity tests"
```

---

### Task 11: The git-history analysis (from ch06)

The first bespoke port. ch06 hardcodes its three sections in its template, builds three different card types, and renders a coloured flex timeline instead of a Mermaid diagram, so it keeps its own renderer. The port is near-verbatim: only imports change. Parity is therefore byte-identical with no exceptions.

**Files:**

- Create: `src/crack/analyses/git_history/__init__.py`
- Create: `src/crack/analyses/git_history/nodes.py` (from `ch06-git-history/workflow/nodes.py`)
- Create: `src/crack/analyses/git_history/gitlog.py` (copy of `ch06-git-history/workflow/gitlog.py`)
- Create: `src/crack/analyses/git_history/render.py` (copy of `ch06-git-history/workflow/render.py`)
- Create: `src/crack/analyses/git_history/prompts/{name-eras,profile-era,graveyard-entry}.md` (copies)
- Test: `tests/test_parity_git_history.py`

**Interfaces:**

- Consumes: `crack.core.OverviewNode`, `call_llm`, `read_prompt`, `fill` (Task 1); `crack.core.render.render_html` dispatch (Task 3).
- Produces: the module `crack.analyses.git_history` exposing `NAME`, `ENV_DEFAULTS`, `build_flow()`, `overview_spec(shared)`, `init_shared(args, out_dir)`, `add_arguments(parser)`, `render_html(name, shared)`, `render_markdown(name, shared)`. It has no `THEME` or `SECTIONS`; the engine defers to its renderer.

- [ ] **Step 1: Write the failing parity test**

Create `tests/test_parity_git_history.py`:

```python
"""git-history keeps its own renderer, so parity is byte-identical."""
import argparse
from crack.analyses import git_history
from crack.core import render

SHARED = {
    "repo_path": "/tmp/redis",
    "commits": [{"hash": "abc1234", "date": "2011-01-02", "subject": "init"}] * 4,
    "eras": [
        {"name": "The cache years", "start": "2009-01", "end": "2012-06",
         "description": "It began as a cache.",
         "diagram": "graph LR;\ncache-->disk;",
         "turning_point": "Persistence landed.", "turning_point_hash": "abc1234"},
        {"name": "The data structure server", "start": "2012-07", "end": None,
         "description": "Types multiplied.", "diagram": "",
         "turning_point": "", "turning_point_hash": ""},
    ],
    "profiles": [
        {"era": {"name": "The cache years"}, "commit_count": 900,
         "profile": {"cast": [{"name": "antirez", "pct": 82, "note": "Most of it."}],
                     "mood": [{"name": "Features", "pct": 60, "note": "New types."}]}},
        {"era": {"name": "The data structure server"}, "commit_count": 2400,
         "profile": {"cast": [{"name": "core team", "pct": 55, "note": "Shared."}],
                     "mood": [{"name": "Hardening", "pct": 70, "note": "Fewer bugs."}]}},
    ],
    "graves": [
        {"entry_md": "### Diskstore\nAn on-disk backend, removed.",
         "commit": {"hash": "def5678abc", "date": "2011-08-01", "count": 22,
                    "scope": "src"},
         "era": {"name": "The cache years"}},
    ],
    "overview": {"welcome": "Redis grew from a cache into a data structure server.",
                 "intros": {"The eras": "Read oldest first.",
                            "Cast & mood": "Who drove each era.",
                            "The graveyard": "The bets they walked away from."}},
}

def test_html_is_byte_identical_to_chapter(chapter_render):
    chapter = chapter_render("ch06-git-history")
    assert render.render_html(git_history, "redis", SHARED) == \
        chapter.render_html("redis", SHARED)

def test_markdown_is_byte_identical_to_chapter(chapter_render):
    chapter = chapter_render("ch06-git-history")
    assert render.render_markdown(git_history, "redis", SHARED) == \
        chapter.render_markdown("redis", SHARED)

def test_engine_defers_to_the_custom_renderer():
    assert not hasattr(git_history, "SECTIONS")
    assert hasattr(git_history, "render_html")

def test_grave_flags_reach_shared():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path")
    git_history.add_arguments(parser)
    args = parser.parse_args(["/tmp/x", "--max-graves", "3", "--grave-min-files", "12"])
    shared = git_history.init_shared(args, "/out")
    assert shared["max_graves"] == 3
    assert shared["grave_min_files"] == 12

def test_grave_flag_defaults_match_the_chapter():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path")
    git_history.add_arguments(parser)
    args = parser.parse_args(["/tmp/x"])
    shared = git_history.init_shared(args, "/out")
    assert shared["max_graves"] == 6
    assert shared["grave_min_files"] == 8
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_parity_git_history.py -v`
Expected: FAIL with `ImportError: cannot import name 'git_history' from 'crack.analyses'`

- [ ] **Step 3: Copy the git reader, renderer, and prompts**

```bash
mkdir -p src/crack/analyses/git_history/prompts
cp ch06-git-history/workflow/gitlog.py src/crack/analyses/git_history/gitlog.py
cp ch06-git-history/workflow/render.py src/crack/analyses/git_history/render.py
cp ch06-git-history/prompts/name-eras.md       src/crack/analyses/git_history/prompts/
cp ch06-git-history/prompts/profile-era.md     src/crack/analyses/git_history/prompts/
cp ch06-git-history/prompts/graveyard-entry.md src/crack/analyses/git_history/prompts/
```

- [ ] **Step 4: Rewrite the imports in the copied files**

In `src/crack/analyses/git_history/render.py`, delete these two lines (`ch06-git-history/workflow/render.py:17` and `:20`) and the now-unused `import os`:

```python
import sys
...
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
```

Keep `import html as _html`, `import re`, and the `MarkdownIt` import. Change nothing else in the file: every helper, the template, and both render functions stay byte-for-byte as they are. The module already defines its own `md`, `_esc`, and `md_rich`, which is why parity is exact.

In `gitlog.py`, delete any `sys.path.insert(...)` line and its now-unused `import sys`, and change `from utils import ...` to `from crack.core import ...` if such an import exists.

- [ ] **Step 5: Port the nodes**

Copy `ch06-git-history/workflow/nodes.py` to `src/crack/analyses/git_history/nodes.py`. Replace its import block with:

```python
import os
import re

from pocketflow import Node

from crack.core import call_llm, read_prompt, fill, yaml_call
from . import gitlog

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), 'prompts')

def load_prompt(name):
    return read_prompt(PROMPTS_DIR, name)
```

Import from `crack.core` only the names the chapter file actually used; drop any that are unused after the move. Keep `FetchHistory`, `NameEras`, `ProfileEras`, and `Graveyard` exactly as they are. Delete `overview_spec`; it moves to `__init__.py`. Keep the chapter's alias for the gitlog module if it differs.

- [ ] **Step 6: Write the analysis module**

Create `src/crack/analyses/git_history/__init__.py`:

```python
"""Read the product roadmap already written in the git log (ch06)."""
import os

from pocketflow import Flow

from crack.core import OverviewNode
from .nodes import FetchHistory, NameEras, ProfileEras, Graveyard
# This analysis builds its page from structured data rather than markdown
# blobs, so it keeps its own renderer; crack.core.render defers to these.
from .render import render_html, render_markdown  # noqa: F401

NAME = "git-history"

ENV_DEFAULTS = {}

def add_arguments(parser):
    parser.add_argument("--max-graves", type=int, default=6,
                        help="how many killed features to dig up (default 6)")
    parser.add_argument("--grave-min-files", type=int, default=8,
                        help="a deletion counts as a killed feature at this "
                             "many files (default 8)")

def init_shared(args, out_dir):
    return {
        "repo_path": args.repo_path,
        "max_graves": getattr(args, "max_graves", 6),
        "grave_min_files": getattr(args, "grave_min_files", 8),
    }

def build_flow():
    fetch, eras = FetchHistory(), NameEras()
    profile, graves = ProfileEras(), Graveyard()
    overview = OverviewNode(overview_spec)
    fetch >> eras >> profile >> graves >> overview
    return Flow(start=fetch)
```

Then append the `overview_spec` function you deleted from `nodes.py`, unchanged.

- [ ] **Step 7: Run the tests to verify they pass**

Run: `pytest tests/test_parity_git_history.py -v`
Expected: 5 passed. Because this renderer is copied verbatim, any HTML difference means an import rewrite changed behavior; find it rather than relaxing the assertion.

- [ ] **Step 8: Run the whole suite and check the chapters**

```bash
pytest -v
git status --porcelain -- 'ch*'   # must be empty
```

- [ ] **Step 9: Commit**

```bash
git add src/crack/analyses/git_history tests/test_parity_git_history.py
git commit -m "feat: git-history analysis ported from ch06 with its own renderer"
```

---

### Task 12: The product-intent analysis (from ch05)

The second bespoke port, and the only analysis that writes a file besides the two reports. `IllustratePain` generates `pain.png` into the output directory, so `init_shared` must put that path in `shared` before the flow runs. Its renderer is copied verbatim, so parity is byte-identical.

**Files:**

- Create: `src/crack/analyses/product_intent/__init__.py`
- Create: `src/crack/analyses/product_intent/nodes.py` (from `ch05-product-intent/workflow/nodes.py`)
- Create: `src/crack/analyses/product_intent/render.py` (copy of `ch05-product-intent/workflow/render.py`)
- Create: `src/crack/analyses/product_intent/prompts/{pain-scene,variant-sentence,competitive-positioning,pain-illustration,surprises-and-absences}.md` (copies)
- Test: `tests/test_parity_product_intent.py`

**Interfaces:**

- Consumes: `crack.core.OverviewNode`, `call_llm`, `call_image`, `crawl` (Task 1); `crack.core.render.render_html` dispatch (Task 3); `crack.core.runner.run_analysis`, which passes `out_dir` into `init_shared` (Task 4).
- Produces: the module `crack.analyses.product_intent` exposing `NAME`, `ENV_DEFAULTS`, `build_flow()`, `init_shared(args, out_dir)`, `add_arguments(parser)`, `render_html(name, shared)`, `render_markdown(name, shared)`. It has no `THEME`, `SECTIONS`, or `overview_spec`: ch05 has no welcome/intros concept, so its flow ends without an `OverviewNode`.

- [ ] **Step 1: Write the failing parity test**

Create `tests/test_parity_product_intent.py`:

```python
"""product-intent keeps its own renderer, so parity is byte-identical."""
import argparse
import os
from crack.analyses import product_intent
from crack.core import render

SHARED = {
    "repo_path": "/tmp/tigerbeetle",
    "variant": "A database that only does double-entry accounting.",
    "pain": "General ledgers on general databases lose money under contention.",
    "positioning": {
        "sacrifices": ["General queries", "Ad-hoc schema"],
        "gains": ["Contention-free transfers", "Deterministic replay"],
        "why_incumbents_cannot_copy": "Postgres cannot drop general SQL.",
        "diagram": "graph TD;\ngeneral-->slow;",
        "dimensions": [
            {"name": "Throughput", "definition": "Transfers per second."},
            {"name": "Generality", "definition": "How many shapes it stores."},
        ],
        "competitors": [
            {"name": "TigerBeetle",
             "cells": [{"verdict": "Very high", "detail": "Batched."},
                       {"verdict": "Narrow", "detail": "Ledgers only."}]},
            {"name": "Postgres",
             "cells": [{"verdict": "Moderate", "detail": "Row locks."},
                       {"verdict": "Broad", "detail": "Anything."}]},
        ],
    },
    "surprises": {
        "present": [{"headline": "Deterministic simulation",
                     "where": "src/testing/", "bet": "Correctness sells."}],
        "absent": [{"headline": "No SQL parser",
                    "evidence": "No parser directory.",
                    "tradeoff": "Narrowness is the product."}],
    },
}

def test_html_is_byte_identical_to_chapter(chapter_render):
    chapter = chapter_render("ch05-product-intent")
    assert render.render_html(product_intent, "tigerbeetle", SHARED) == \
        chapter.render_html("tigerbeetle", SHARED)

def test_markdown_is_byte_identical_to_chapter(chapter_render):
    chapter = chapter_render("ch05-product-intent")
    assert render.render_markdown(product_intent, "tigerbeetle", SHARED) == \
        chapter.render_markdown("tigerbeetle", SHARED)

def test_init_shared_points_the_image_at_the_output_dir():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path")
    product_intent.add_arguments(parser)
    args = parser.parse_args(["/tmp/tb"])
    shared = product_intent.init_shared(args, "/out/tb/product-intent")
    assert shared["pain_image_path_target"] == os.path.join(
        "/out/tb/product-intent", "pain.png")

def test_include_and_exclude_reach_shared():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path")
    product_intent.add_arguments(parser)
    args = parser.parse_args(["/tmp/tb", "--include", "src/**",
                              "--exclude", "**/test/**"])
    shared = product_intent.init_shared(args, "/out")
    assert shared["include"] == ["src/**"]
    assert shared["exclude"] == ["**/test/**"]

def test_engine_defers_to_the_custom_renderer():
    assert not hasattr(product_intent, "SECTIONS")
    assert hasattr(product_intent, "render_html")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_parity_product_intent.py -v`
Expected: FAIL with `ImportError: cannot import name 'product_intent' from 'crack.analyses'`

- [ ] **Step 3: Copy the renderer and prompts**

```bash
mkdir -p src/crack/analyses/product_intent/prompts
cp ch05-product-intent/workflow/render.py src/crack/analyses/product_intent/render.py
cp ch05-product-intent/prompts/pain-scene.md               src/crack/analyses/product_intent/prompts/
cp ch05-product-intent/prompts/variant-sentence.md         src/crack/analyses/product_intent/prompts/
cp ch05-product-intent/prompts/competitive-positioning.md  src/crack/analyses/product_intent/prompts/
cp ch05-product-intent/prompts/pain-illustration.md        src/crack/analyses/product_intent/prompts/
cp ch05-product-intent/prompts/surprises-and-absences.md   src/crack/analyses/product_intent/prompts/
```

- [ ] **Step 4: Rewrite the imports in the copied renderer**

In `src/crack/analyses/product_intent/render.py`, delete the `import sys` line and the `sys.path.insert(...)` line (`ch05-product-intent/workflow/render.py:11` and `:15`). Keep `import html as _html`, `import os` (the renderer calls `os.path.basename` and `os.path.exists` when embedding `pain.png`), and the `MarkdownIt` import. Change nothing else: the template, `md`, `md_block`, `_esc`, and both render functions stay byte-for-byte as they are.

- [ ] **Step 5: Port the nodes**

Copy `ch05-product-intent/workflow/nodes.py` to `src/crack/analyses/product_intent/nodes.py`. Replace its import block with:

```python
import os

from pocketflow import Node

from crack.core import call_llm, call_image, crawl, read_prompt, fill, yaml_call

PROMPTS_DIR = os.path.join(os.path.dirname(__file__), 'prompts')
```

Import from `crack.core` only the names the chapter file actually used; drop any that are unused after the move. The chapter defines a local prompt loader reading from `PROMPTS_DIR`; keep it as it is now that `PROMPTS_DIR` points inside the package. Keep `FetchRepo`, `PainScene`, `VariantSentence`, `CompetitivePositioning`, `IllustratePain`, and `SurprisesAndAbsences` exactly as they are, including `IllustratePain.exec_fallback`, which keeps a failed image from killing the run.

- [ ] **Step 6: Write the analysis module**

Create `src/crack/analyses/product_intent/__init__.py`:

```python
"""Reverse engineer the product story from the source (ch05)."""
import os

from pocketflow import Flow

from .nodes import (FetchRepo, PainScene, VariantSentence,
                    CompetitivePositioning, IllustratePain,
                    SurprisesAndAbsences)
# This analysis hand-builds its page from structured data, so it keeps its own
# renderer; crack.core.render defers to these.
from .render import render_html, render_markdown  # noqa: F401

NAME = "product-intent"

ENV_DEFAULTS = {}

def add_arguments(parser):
    parser.add_argument("--include", action="append", default=[],
                        help=".gitignore-style pattern: keep only matching "
                             "paths. Repeatable.")
    parser.add_argument("--exclude", action="append", default=[],
                        help=".gitignore-style pattern: drop matching paths. "
                             "Repeatable.")

def init_shared(args, out_dir):
    """IllustratePain writes the generated image beside the report."""
    return {
        "repo_path": args.repo_path,
        "include": list(getattr(args, "include", []) or []),
        "exclude": list(getattr(args, "exclude", []) or []),
        "pain_image_path_target": os.path.join(out_dir, "pain.png"),
    }

def build_flow():
    fetch, pain = FetchRepo(), PainScene()
    variant, illustrate = VariantSentence(), IllustratePain()
    positioning, surprises = CompetitivePositioning(), SurprisesAndAbsences()
    fetch >> pain >> variant >> illustrate >> positioning >> surprises
    return Flow(start=fetch)
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `pytest tests/test_parity_product_intent.py -v`
Expected: 5 passed.

- [ ] **Step 8: Run the whole suite and check the chapters**

```bash
pytest -v
git status --porcelain -- 'ch*'   # must be empty
```

- [ ] **Step 9: Commit**

```bash
git add src/crack/analyses/product_intent tests/test_parity_product_intent.py
git commit -m "feat: product-intent analysis ported from ch05 with its own renderer"
```

---

### Task 13: Smoke test and README

One end-to-end test proves the wiring holds against a real provider. The fixture repo is built in a tmpdir with a real git history, so the git-history analysis is smoke-testable too. The test skips when no API key is present, so the suite stays green offline.

**Files:**

- Modify: `tests/conftest.py` (add the fixture_repo fixture)
- Create: `tests/test_smoke.py`
- Create: `src/README.md`
- Modify: `README.md` (add a "One command" section; do not touch the chapter map)

**Interfaces:**

- Consumes: `crack.cli.main` (Task 6), `crack.analyses.ANALYSIS_NAMES` (Task 2), the existing `tests/conftest.py` (Task 7).
- Produces: the pytest fixture `fixture_repo` returning a path to a small git repository with two commits.

- [ ] **Step 1: Add the repository fixture**

Append to the existing `tests/conftest.py` (created in Task 7). Keep `chapter_render` and `apply_unifications` as they are; add `import subprocess` to the imports at the top, then append:

```python
APP = '''\
from flask import Flask, jsonify, request

app = Flask(__name__)
NOTES = {}

@app.route("/notes", methods=["POST"])
def create_note():
    body = request.get_json()
    NOTES[body["id"]] = body["text"]
    return jsonify(ok=True)

@app.route("/notes/<note_id>")
def read_note(note_id):
    return jsonify(text=NOTES.get(note_id))
'''

MODELS = '''\
CREATE TABLE notes (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True,
                   capture_output=True, text=True)

@pytest.fixture(scope="session")
def fixture_repo(tmp_path_factory):
    repo = tmp_path_factory.mktemp("notes-app")
    (repo / "app.py").write_text(APP)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "feat: notes API with create and read")

    (repo / "schema.sql").write_text(MODELS)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "feat: persist notes in a table")
    return str(repo)
```

- [ ] **Step 2: Write the smoke test**

Create `tests/test_smoke.py`:

```python
"""End-to-end run against a real provider. Skipped without an API key."""
import os
import pytest
from crack import cli

HAS_KEY = any(os.environ.get(k) for k in
              ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY"))

pytestmark = pytest.mark.skipif(not HAS_KEY, reason="no LLM provider key set")

def test_backend_analysis_end_to_end(fixture_repo, tmp_path):
    code = cli.main(["backend", fixture_repo, "--out", str(tmp_path)])
    assert code == 0

    out = tmp_path / os.path.basename(fixture_repo) / "backend"
    html = (out / "index.html").read_text()
    markdown = (out / "index.md").read_text()

    assert "<!doctype html>" in html.lower()
    assert len(markdown) > 200
    assert "## The pipeline" in markdown
```

- [ ] **Step 3: Run the test**

Run: `pytest tests/test_smoke.py -v`
Expected without a key: 1 skipped. With a key set: 1 passed (this makes real LLM calls and costs money).

- [ ] **Step 4: Write `src/README.md`**

````markdown
# crack

One command that reads a codebase six ways. Same prompts as the book's
chapter workflows, collapsed into one installable package.

## Install

```bash
pip install -e ".[dev,anthropic]"
export ANTHROPIC_API_KEY=sk-ant-...   # or OPENAI_API_KEY, or GEMINI_API_KEY
```

## Use

```bash
crack backend /path/to/repo            # one read
crack all /path/to/repo                # all six, plus a landing page
```

Reports land in `crack-output/<repo-name>/<analysis>/index.html`.

| Subcommand       | What it reads                                         |
| ---------------- | ----------------------------------------------------- |
| `product-intent` | the product story, reverse engineered from the source |
| `git-history`    | the roadmap already written in the git log            |
| `schema`         | the data model and how it migrated                    |
| `interfaces`     | the API surface and one action traced through it      |
| `architecture`   | the services and how a request crosses them           |
| `backend`        | the six layers every request flows through            |

Analysis-specific flags:

```bash
crack product-intent REPO --include 'src/**' --exclude '**/test/**'
crack git-history REPO --max-graves 3 --grave-min-files 12
crack schema REPO --schema db/schema.rb
```

## Relationship to the chapters

The `ch*/` folders are the book's teaching snapshots and are never
modified. This package is the deduplicated version of the same behavior:
one render engine, one runner, six thin analysis modules.
````

- [ ] **Step 5: Add a section to the root `README.md`**

Insert this immediately above the `## Chapter map` heading. Do not change the chapter table.

````markdown
## One command

The chapter workflows are also available collapsed into a single CLI:

```bash
pip install -e ".[anthropic]"
crack all /path/to/repo
```
````

See [`src/README.md`](src/README.md). The chapter folders are unchanged;
run them directly when following along with the book.

````text

- [ ] **Step 6: Run the whole suite**

Run: `pytest -v`
Expected: all tests pass, with the smoke test skipped when no key is set.

- [ ] **Step 7: Verify no chapter file changed**

Run: `git status --porcelain -- 'ch*'`
Expected: empty output.

- [ ] **Step 8: Commit**

```bash
git add tests/conftest.py tests/test_smoke.py src/README.md README.md
git commit -m "test: end-to-end smoke test and CLI documentation"
````

---
