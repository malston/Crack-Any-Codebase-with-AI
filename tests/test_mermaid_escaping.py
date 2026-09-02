"""LLM-authored mermaid diagram source must be HTML-escaped before it lands
inside <pre class="mermaid">. Mermaid reads that element's textContent,
which the browser decodes back to the original characters, so escaping is
safe and reversible -- it does not change what Mermaid parses.

A prompt-injected diagram containing `</pre><script>...` would otherwise
close the <pre> early and execute in the rendered report.
"""
import html as _html

from crack.analyses import architecture, backend, git_history, interfaces, product_intent, schema
from crack.core import render
from test_parity_architecture import SHARED as ARCHITECTURE_SHARED
from test_parity_backend import SHARED as BACKEND_SHARED
from test_parity_git_history import SHARED as GIT_HISTORY_SHARED
from test_parity_interfaces import SHARED as INTERFACES_SHARED
from test_parity_product_intent import SHARED as PRODUCT_INTENT_SHARED
from test_parity_schema import SHARED as SCHEMA_SHARED

PAYLOAD = "</pre><script>alert(1)</script>"
ESCAPED_PAYLOAD = _html.escape(PAYLOAD)


def test_backend_hero_diagram_is_escaped():
    shared = dict(BACKEND_SHARED, pipeline_diagram=PAYLOAD)
    out = render.render_html(backend, "zulip", shared)
    assert "</pre><script>" not in out
    assert ESCAPED_PAYLOAD in out


def test_architecture_hero_diagram_is_escaped():
    shared = dict(ARCHITECTURE_SHARED, arch_diagram=PAYLOAD)
    out = render.render_html(architecture, "zulip", shared)
    assert "</pre><script>" not in out
    assert ESCAPED_PAYLOAD in out


def test_schema_hero_diagram_is_escaped():
    shared = dict(SCHEMA_SHARED, erd=PAYLOAD)
    out = render.render_html(schema, "discourse", shared)
    assert "</pre><script>" not in out
    assert ESCAPED_PAYLOAD in out


def test_interfaces_sequence_diagram_is_escaped():
    shared = dict(INTERFACES_SHARED,
                  sequence_md=f"```mermaid\n{PAYLOAD}\n```\n\nbody")
    out = render.render_html(interfaces, "zulip", shared)
    assert "</pre><script>" not in out
    assert ESCAPED_PAYLOAD in out


def test_md_rich_mermaid_fence_is_escaped():
    out = render.md_rich(f"```mermaid\n{PAYLOAD}\n```")
    assert "</pre><script>" not in out
    assert ESCAPED_PAYLOAD in out


def test_git_history_era_diagram_is_escaped():
    eras = [dict(GIT_HISTORY_SHARED["eras"][0], diagram=PAYLOAD)]
    shared = dict(GIT_HISTORY_SHARED, eras=eras)
    out = render.render_html(git_history, "redis", shared)
    assert "</pre><script>" not in out
    assert ESCAPED_PAYLOAD in out


def test_product_intent_trap_diagram_is_escaped():
    positioning = dict(PRODUCT_INTENT_SHARED["positioning"], diagram=PAYLOAD)
    shared = dict(PRODUCT_INTENT_SHARED, positioning=positioning)
    out = render.render_html(product_intent, "tigerbeetle", shared)
    assert "</pre><script>" not in out
    assert ESCAPED_PAYLOAD in out


def test_benign_diagram_round_trips_through_escaping():
    """Escaping must be reversible: what a browser's textContent decode
    hands back to Mermaid must equal the original diagram source."""
    diagram = "graph TD;\nA-->B;\nB-->C;"
    out = render.md_rich(f"```mermaid\n{diagram}\n```")
    start = out.index('<pre class="mermaid">') + len('<pre class="mermaid">')
    end = out.index("</pre>", start)
    # markdown-it's fenced-code-block rendering always trails the content
    # with a newline; that is unrelated to escaping, so it is stripped here.
    assert _html.unescape(out[start:end]).rstrip("\n") == diagram
