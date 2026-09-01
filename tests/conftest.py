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


def strip_engine_additions(html, blocks):
    """Remove CSS blocks the shared engine emits that this chapter never had.

    The engine carries one page template for all four card-family analyses, so
    it always emits the table rules and the bar-chart rules. A chapter that
    lacked a block cannot match byte-for-byte until that block is subtracted.
    Each block must match exactly, so a block that drifts fails loudly instead
    of silently masking a regression.
    """
    for block in blocks:
        assert block in html, f"engine no longer emits this block verbatim: {block[:60]!r}"
        html = html.replace(block, "", 1)
    return html


# The two blocks the engine always emits, as they appear in rendered output.
# Braces are singled here: PAGE doubles them for str.format, the output does not.
TABLE_CSS = """  table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: .78rem; }
  th, td { border: 1px solid var(--rule); padding: 6px 8px; text-align: left; vertical-align: top; }
  th { background: var(--stone-bg); font-size: .7rem; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }
  td code { font-size: .92em; }
"""

GROUPCHART_CSS = """  .groupchart { background: var(--surface); border: 1px solid var(--rule); border-radius: var(--radius);
    box-shadow: var(--shadow); padding: 16px 20px; display: flex; flex-direction: column; gap: 7px; }
  .gc-row { display: flex; align-items: center; gap: 12px; }
  .gc-name { flex: 0 0 220px; font-size: .82rem; font-weight: 600; color: var(--text); text-align: right;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .gc-track { flex: 1; background: var(--stone-bg); border-radius: 5px; overflow: hidden; }
  .gc-bar { height: 22px; background: linear-gradient(90deg, #2dd4bf, var(--accent)); border-radius: 5px;
    color: #fff; font-size: .72rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;
    display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; min-width: 24px; }
  @media (max-width: 560px) { .gc-name { flex-basis: 110px; } }
"""
