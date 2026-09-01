"""The ported architecture renderer must match ch09's, modulo the named unifications."""
from conftest import (GROUPCHART_CSS, TABLE_CSS, apply_unifications,
                      strip_engine_additions)
from crack.analyses import architecture
from crack.core import render

# ch09 has neither table CSS nor the bar-chart CSS; the shared engine emits both.
ADDITIONS = [TABLE_CSS, GROUPCHART_CSS]

UNIFICATIONS = [
    # ch09 never picked up the flowchart htmlLabels option the engine standardises on.
    ("mermaid.initialize({ startOnLoad: false, theme: 'neutral', securityLevel: 'loose' });",
     "mermaid.initialize({ startOnLoad: false, theme: 'neutral', securityLevel: 'loose', "
     "flowchart: { htmlLabels: true } });"),

    # ch09 carries a vestigial `.verdict` CSS rule for a class no longer used in its
    # markup (the verdict text now flows into the hero subtitle instead of its own
    # card); the engine never emits CSS for a class it doesn't render.
    ("  .sec-intro p { margin: 0; }\n"
     "\n"
     "  .verdict { background: var(--accent-soft); border: 1px solid #fde68a; border-radius: var(--radius);\n"
     "    padding: 12px 16px; margin-bottom: 14px; font-size: .9rem; color: #713f12; }\n"
     "  .verdict strong { color: #78350f; }\n"
     "\n"
     "  .diagram {",
     "  .sec-intro p { margin: 0; }\n"
     "\n"
     "  .diagram {"),

    # ch09 hardcoded the per-section rail-width rules after .card-body li; the
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
     "    background: linear-gradient(180deg, #fffdf7, #fff); font-weight: 700; font-size: .96rem; line-height: 1.35; }\n"
     "  .card-top code { font-size: .82em; }\n"
     "  .card-body { padding: 13px 18px 16px; font-size: .84rem; }\n"
     "  .card-body p { margin: .5em 0; color: #344054; line-height: 1.6; }\n"
     "  .card-body p:first-child { margin-top: 0; }\n"
     "  .card-body strong { color: var(--text); }\n"
     "  .card-body em { color: var(--muted); }\n"
     "  .card-body ul, .card-body ol { margin: .5em 0; padding-left: 1.3em; }\n"
     "  .card-body li { margin: .28em 0; color: #344054; line-height: 1.55; }\n"
     "\n"
     "  .rail.inv .card { flex: 0 0 380px; width: 380px; }\n"
     "  .rail.tech .card { flex: 0 0 420px; width: 420px; }\n"
     "  .rail.trace .card { flex: 0 0 460px; width: 460px; }\n"
     "\n",
     "  .rail::-webkit-scrollbar-thumb { background: #cbd2dc; border-radius: 5px; }\n"
     "  .rail.inv .card { flex: 0 0 380px; width: 380px; }\n"
     "  .rail.tech .card { flex: 0 0 420px; width: 420px; }\n"
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
     "    background: linear-gradient(180deg, #fffdf7, #fff); font-weight: 700; font-size: .96rem; line-height: 1.35; }\n"
     "  .card-top code { font-size: .82em; }\n"
     "  .card-body { padding: 13px 18px 16px; font-size: .84rem; }\n"
     "  .card-body p { margin: .5em 0; color: #344054; line-height: 1.6; }\n"
     "  .card-body p:first-child { margin-top: 0; }\n"
     "  .card-body strong { color: var(--text); }\n"
     "  .card-body em { color: var(--muted); }\n"
     "  .card-body ul, .card-body ol { margin: .5em 0; padding-left: 1.3em; }\n"
     "  .card-body li { margin: .28em 0; color: #344054; line-height: 1.55; }\n"
     "\n"),
]

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
    actual = strip_engine_additions(
        render.render_html(architecture, "nats", SHARED), ADDITIONS)
    assert actual == expected

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
