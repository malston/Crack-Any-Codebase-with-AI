"""The ported backend renderer must match ch10's, modulo the named unifications."""
from conftest import (GROUPCHART_CSS, TABLE_CSS, apply_unifications,
                      strip_engine_additions)
from crack.analyses import backend
from crack.core import render

# ch10 has neither table CSS nor the bar-chart CSS; the shared engine emits both.
ADDITIONS = [TABLE_CSS, GROUPCHART_CSS]

# Every remaining difference between ch10's page and the engine's, stated explicitly.
UNIFICATIONS = [
    ("max-height: 74vh", "max-height: 72vh"),
    ("font-size: .95rem", "font-size: .96rem"),
    ("margin: .3em 0; color: #344054; line-height: 1.55;",
     "margin: .28em 0; color: #344054; line-height: 1.55;"),
    ("pre code { padding: 0; font-size: .73rem",
     "pre code { padding: 0; font-size: .74rem"),

    # ch10 hardcoded the per-section rail-width rules after .card-body li; the
    # engine derives them from SECTIONS and places them right after the rail
    # scrollbar rules. Same three rules, same values, different position in
    # the shared page template.
    ("  .rail::-webkit-scrollbar-thumb { background: #cbd2dc; border-radius: 5px; }\n"
     "\n"
     "  .scroll { flex: 1; overflow-y: auto; overscroll-behavior: contain; }\n"
     "  .scroll::-webkit-scrollbar { width: 9px; }\n"
     "  .scroll::-webkit-scrollbar-thumb { background: #dce0e7; border-radius: 5px; }\n"
     "\n"
     "  .card { scroll-snap-align: start; background: var(--surface); border: 1px solid var(--rule);\n"
     "    border-radius: var(--radius); box-shadow: var(--shadow); border-top: 3px solid var(--accent);\n"
     "    display: flex; flex-direction: column; overflow: hidden; max-height: 72vh; }\n"
     "  .card-top { flex-shrink: 0; padding: 14px 18px 12px; border-bottom: 1px solid var(--line);\n"
     "    background: linear-gradient(180deg, #fafaff, #fff); font-weight: 700; font-size: .96rem; line-height: 1.35; }\n"
     "  .card-top code { font-size: .82em; }\n"
     "  .card-body { padding: 13px 18px 16px; font-size: .84rem; }\n"
     "  .card-body p { margin: .5em 0; color: #344054; line-height: 1.6; }\n"
     "  .card-body p:first-child { margin-top: 0; }\n"
     "  .card-body strong { color: var(--text); }\n"
     "  .card-body em { color: var(--muted); }\n"
     "  .card-body ul, .card-body ol { margin: .5em 0; padding-left: 1.3em; }\n"
     "  .card-body li { margin: .28em 0; color: #344054; line-height: 1.55; }\n"
     "\n"
     "  .rail.pipe .card { flex: 0 0 400px; width: 400px; }\n"
     "  .rail.code .card { flex: 0 0 520px; width: 520px; }\n"
     "  .rail.trace .card { flex: 0 0 460px; width: 460px; }\n"
     "\n",
     "  .rail::-webkit-scrollbar-thumb { background: #cbd2dc; border-radius: 5px; }\n"
     "  .rail.pipe .card { flex: 0 0 400px; width: 400px; }\n"
     "  .rail.code .card { flex: 0 0 520px; width: 520px; }\n"
     "  .rail.trace .card { flex: 0 0 460px; width: 460px; }\n"
     "\n"
     "  .scroll { flex: 1; overflow-y: auto; overscroll-behavior: contain; }\n"
     "  .scroll::-webkit-scrollbar { width: 9px; }\n"
     "  .scroll::-webkit-scrollbar-thumb { background: #dce0e7; border-radius: 5px; }\n"
     "\n"
     "  .card { scroll-snap-align: start; background: var(--surface); border: 1px solid var(--rule);\n"
     "    border-radius: var(--radius); box-shadow: var(--shadow); border-top: 3px solid var(--accent);\n"
     "    display: flex; flex-direction: column; overflow: hidden; max-height: 72vh; }\n"
     "  .card-top { flex-shrink: 0; padding: 14px 18px 12px; border-bottom: 1px solid var(--line);\n"
     "    background: linear-gradient(180deg, #fafaff, #fff); font-weight: 700; font-size: .96rem; line-height: 1.35; }\n"
     "  .card-top code { font-size: .82em; }\n"
     "  .card-body { padding: 13px 18px 16px; font-size: .84rem; }\n"
     "  .card-body p { margin: .5em 0; color: #344054; line-height: 1.6; }\n"
     "  .card-body p:first-child { margin-top: 0; }\n"
     "  .card-body strong { color: var(--text); }\n"
     "  .card-body em { color: var(--muted); }\n"
     "  .card-body ul, .card-body ol { margin: .5em 0; padding-left: 1.3em; }\n"
     "  .card-body li { margin: .28em 0; color: #344054; line-height: 1.55; }\n"
     "\n"),

    # Security fix: the engine HTML-escapes the mermaid diagram source before
    # writing it into <pre class="mermaid">, closing an HTML-injection hole.
    # ch10 keeps the vulnerable unescaped form; this rewrites only the
    # benign "-->" the fixture diagram happens to contain.
    ("graph LR;\nroute-->handler;", "graph LR;\nroute--&gt;handler;"),
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
    actual = strip_engine_additions(render.render_html(backend, "zulip", SHARED), ADDITIONS)
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
