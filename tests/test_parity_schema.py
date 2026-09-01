"""The ported schema renderer must match ch07's, modulo the named unifications."""
import argparse
from conftest import GROUPCHART_CSS, apply_unifications, strip_engine_additions
from crack.analyses import schema
from crack.core import render

# ch07 already carries the table CSS the engine standardises on, but never had
# the bar-chart CSS.
ADDITIONS = [GROUPCHART_CSS]

UNIFICATIONS = [
    ("font-size: .98rem", "font-size: .96rem"),
    ("margin: .3em 0; color: #344054; line-height: 1.55;",
     "margin: .28em 0; color: #344054; line-height: 1.55;"),
    # ch07 is the only chapter using .erd; the engine standardises on .diagram.
    ('<div class="erd">', '<div class="diagram">'),
    (".erd {", ".diagram {"),
    (".erd pre.mermaid {", ".diagram pre.mermaid {"),
    (".erd pre.mermaid svg {", ".diagram pre.mermaid svg {"),

    # ch07 never picked up the flowchart htmlLabels option the engine standardises on.
    ("mermaid.initialize({ startOnLoad: false, theme: 'neutral', securityLevel: 'loose' });",
     "mermaid.initialize({ startOnLoad: false, theme: 'neutral', securityLevel: 'loose', "
     "flowchart: { htmlLabels: true } });"),

    # ch07 places .hero-diagram/.hero-diagram-cap (with an explanatory comment)
    # right before the diagram rules, after .sec-intro p; the engine emits the
    # same two rules right after .hero-inner, ahead of .eyebrow, and drops the
    # chapter-local comment (the shared template carries no per-chapter prose).
    # Same rules, same values, different position.
    (".hero-inner { max-width: 1120px; margin: 0 auto; }\n"
     "  .eyebrow { display: inline-flex; align-items: center; gap: 7px; color: #c4b5fd;\n"
     "    font-size: .68rem; font-weight: 700; letter-spacing: .18em; text-transform: uppercase; }\n"
     "  .eyebrow::before { content: ''; width: 16px; height: 2px; background: #a78bfa; border-radius: 2px; }\n"
     "  .hero h1 { font-size: 1.9rem; font-weight: 800; letter-spacing: -.025em; margin: 12px 0 10px; }\n"
     "  .hero .sub { font-size: .94rem; color: #d6cff0; margin: 0 auto; line-height: 1.6; }\n"
     "\n"
     "  .sec-head { display: flex; align-items: baseline; gap: 10px; margin: 42px 2px 14px; }\n"
     "  .sec-n { font-family: 'JetBrains Mono', monospace; font-size: .68rem; font-weight: 700; color: var(--accent); }\n"
     "  .sec-label { display: flex; align-items: center; gap: 9px; font-size: .68rem; font-weight: 700;\n"
     "    letter-spacing: .14em; text-transform: uppercase; color: var(--muted); }\n"
     "  .sec-label::before { content: ''; width: 3px; height: 14px; background: var(--accent); border-radius: 2px; }\n"
     "  .sec-note { font-size: .8rem; color: var(--faint); }\n"
     "  .scroll-hint { margin-left: auto; font-size: .68rem; font-weight: 600; color: var(--faint); }\n"
     "\n"
     '  /* Friendly "start here" welcome + per-section intros */\n'
     "  .intro { background: var(--surface); border: 1px solid var(--rule); border-left: 4px solid var(--accent);\n"
     "    border-radius: var(--radius); box-shadow: var(--shadow); padding: 20px 24px; margin: 30px 0 4px; }\n"
     "  .intro-label { font-size: .68rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase;\n"
     "    color: var(--accent); margin-bottom: 10px; }\n"
     "  .intro p { margin: .5em 0; font-size: .96rem; color: #344054; line-height: 1.7; }\n"
     "  .intro p:first-child { margin-top: 0; }\n"
     "  .intro strong { color: var(--text); }\n"
     "  .sec-intro { font-size: .9rem; color: #475467; line-height: 1.6; margin: -4px 2px 12px; }\n"
     "  .sec-intro p { margin: 0; }\n"
     "\n"
     "  /* Hero diagram (the big picture, right under the welcome) */\n"
     "  .hero-diagram { margin: 18px 0 4px; }\n"
     "  .hero-diagram-cap { font-size: .7rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;\n"
     "    color: var(--accent); margin: 0 2px 9px; }\n"
     "  .diagram { background: var(--surface); border: 1px solid var(--rule); border-radius: var(--radius);\n"
     "    box-shadow: var(--shadow); padding: 16px; margin-bottom: 16px; overflow-x: auto; }\n"
     "  .diagram pre.mermaid { margin: 0; text-align: center; background: transparent; }\n"
     "  .diagram pre.mermaid svg { max-width: 100%; height: auto; }\n",
     ".hero-inner { max-width: 1120px; margin: 0 auto; }\n"
     "  .hero-diagram { margin: 18px 0 4px; }\n"
     "  .hero-diagram-cap { font-size: .7rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;\n"
     "    color: var(--accent); margin: 0 2px 9px; }\n"
     "  .eyebrow { display: inline-flex; align-items: center; gap: 7px; color: #c4b5fd;\n"
     "    font-size: .68rem; font-weight: 700; letter-spacing: .18em; text-transform: uppercase; }\n"
     "  .eyebrow::before { content: ''; width: 16px; height: 2px; background: #a78bfa; border-radius: 2px; }\n"
     "  .hero h1 { font-size: 1.9rem; font-weight: 800; letter-spacing: -.025em; margin: 12px 0 10px; }\n"
     "  .hero .sub { font-size: .94rem; color: #d6cff0; margin: 0 auto; line-height: 1.6; }\n"
     "\n"
     "  .sec-head { display: flex; align-items: baseline; gap: 10px; margin: 42px 2px 14px; }\n"
     "  .sec-n { font-family: 'JetBrains Mono', monospace; font-size: .68rem; font-weight: 700; color: var(--accent); }\n"
     "  .sec-label { display: flex; align-items: center; gap: 9px; font-size: .68rem; font-weight: 700;\n"
     "    letter-spacing: .14em; text-transform: uppercase; color: var(--muted); }\n"
     "  .sec-label::before { content: ''; width: 3px; height: 14px; background: var(--accent); border-radius: 2px; }\n"
     "  .sec-note { font-size: .8rem; color: var(--faint); }\n"
     "  .scroll-hint { margin-left: auto; font-size: .68rem; font-weight: 600; color: var(--faint); }\n"
     "\n"
     '  /* Friendly "start here" welcome + per-section intros */\n'
     "  .intro { background: var(--surface); border: 1px solid var(--rule); border-left: 4px solid var(--accent);\n"
     "    border-radius: var(--radius); box-shadow: var(--shadow); padding: 20px 24px; margin: 30px 0 4px; }\n"
     "  .intro-label { font-size: .68rem; font-weight: 700; letter-spacing: .14em; text-transform: uppercase;\n"
     "    color: var(--accent); margin-bottom: 10px; }\n"
     "  .intro p { margin: .5em 0; font-size: .96rem; color: #344054; line-height: 1.7; }\n"
     "  .intro p:first-child { margin-top: 0; }\n"
     "  .intro strong { color: var(--text); }\n"
     "  .sec-intro { font-size: .9rem; color: #475467; line-height: 1.6; margin: -4px 2px 12px; }\n"
     "  .sec-intro p { margin: 0; }\n"
     "\n"
     "  .diagram { background: var(--surface); border: 1px solid var(--rule); border-radius: var(--radius);\n"
     "    box-shadow: var(--shadow); padding: 16px; margin-bottom: 16px; overflow-x: auto; }\n"
     "  .diagram pre.mermaid { margin: 0; text-align: center; background: transparent; }\n"
     "  .diagram pre.mermaid svg { max-width: 100%; height: auto; }\n"),

    # ch07 hardcoded the per-section rail-width rules after .card-body li (with a
    # "widths per section" comment) and placed `table` before `pre`/`code` (with a
    # "Natural height, capped" comment ahead of .card); the engine derives the
    # rail widths from SECTIONS right after the rail scrollbar rules, places
    # `table` after `pre`/`code` right before `footer`, and drops both
    # chapter-local comments. Same rules, same values, different position.
    (".rail::-webkit-scrollbar-thumb { background: #cbd2dc; border-radius: 5px; }\n"
     "\n"
     "  .scroll { flex: 1; overflow-y: auto; overscroll-behavior: contain; }\n"
     "  .scroll::-webkit-scrollbar { width: 9px; }\n"
     "  .scroll::-webkit-scrollbar-thumb { background: #dce0e7; border-radius: 5px; }\n"
     "\n"
     "  /* Natural height, capped: short cards (tour/flows) stay short; long cards\n"
     "     (deep dive) hit the cap and scroll inside. align-items:stretch keeps cards\n"
     "     in the same rail equal height. */\n"
     "  .card { scroll-snap-align: start; background: var(--surface); border: 1px solid var(--rule);\n"
     "    border-radius: var(--radius); box-shadow: var(--shadow); border-top: 3px solid var(--accent);\n"
     "    display: flex; flex-direction: column; overflow: hidden; max-height: 72vh; }\n"
     "  .card-top { flex-shrink: 0; padding: 14px 18px 12px; border-bottom: 1px solid var(--line);\n"
     "    background: linear-gradient(180deg, #fbfaff, #fff); font-weight: 700; font-size: .96rem;\n"
     "    line-height: 1.35; }\n"
     "  .card-top code { font-size: .82em; }\n"
     "  .card-body { padding: 13px 18px 16px; font-size: .84rem; }\n"
     "  .card-body p { margin: .5em 0; color: #344054; line-height: 1.6; }\n"
     "  .card-body p:first-child { margin-top: 0; }\n"
     "  .card-body strong { color: var(--text); }\n"
     "  .card-body em { color: var(--muted); }\n"
     "  .card-body ul, .card-body ol { margin: .5em 0; padding-left: 1.3em; }\n"
     "  .card-body li { margin: .28em 0; color: #344054; line-height: 1.55; }\n"
     "\n"
     "  /* widths per section */\n"
     "  .rail.tour .card { flex: 0 0 400px; width: 400px; }\n"
     "  .rail.flows .card { flex: 0 0 400px; width: 400px; }\n"
     "  .rail.deep .card { flex: 0 0 480px; width: 480px; }\n"
     "  .rail.acts .card { flex: 0 0 420px; width: 420px; }\n"
     "\n"
     "  table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: .78rem; }\n"
     "  th, td { border: 1px solid var(--rule); padding: 6px 8px; text-align: left; vertical-align: top; }\n"
     "  th { background: var(--stone-bg); font-size: .7rem; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }\n"
     "  td code { font-size: .92em; }\n"
     "\n"
     "  pre { background: #0f172a; color: #e2e8f0; border-radius: 8px; padding: 11px 13px; overflow-x: auto; margin: 10px 0; }\n"
     "  pre code { padding: 0; font-size: .74rem; line-height: 1.5; }\n"
     "  pre code.hljs { background: transparent; padding: 0; color: #e2e8f0; }\n"
     "  code { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: .84em;\n"
     "    background: var(--stone-bg); color: var(--text); padding: 1px 5px; border-radius: 4px; }\n"
     "\n",
     ".rail::-webkit-scrollbar-thumb { background: #cbd2dc; border-radius: 5px; }\n"
     "  .rail.tour .card { flex: 0 0 400px; width: 400px; }\n"
     "  .rail.flows .card { flex: 0 0 400px; width: 400px; }\n"
     "  .rail.deep .card { flex: 0 0 480px; width: 480px; }\n"
     "  .rail.acts .card { flex: 0 0 420px; width: 420px; }\n"
     "\n"
     "  .scroll { flex: 1; overflow-y: auto; overscroll-behavior: contain; }\n"
     "  .scroll::-webkit-scrollbar { width: 9px; }\n"
     "  .scroll::-webkit-scrollbar-thumb { background: #dce0e7; border-radius: 5px; }\n"
     "\n"
     "  .card { scroll-snap-align: start; background: var(--surface); border: 1px solid var(--rule);\n"
     "    border-radius: var(--radius); box-shadow: var(--shadow); border-top: 3px solid var(--accent);\n"
     "    display: flex; flex-direction: column; overflow: hidden; max-height: 72vh; }\n"
     "  .card-top { flex-shrink: 0; padding: 14px 18px 12px; border-bottom: 1px solid var(--line);\n"
     "    background: linear-gradient(180deg, #fbfaff, #fff); font-weight: 700; font-size: .96rem; line-height: 1.35; }\n"
     "  .card-top code { font-size: .82em; }\n"
     "  .card-body { padding: 13px 18px 16px; font-size: .84rem; }\n"
     "  .card-body p { margin: .5em 0; color: #344054; line-height: 1.6; }\n"
     "  .card-body p:first-child { margin-top: 0; }\n"
     "  .card-body strong { color: var(--text); }\n"
     "  .card-body em { color: var(--muted); }\n"
     "  .card-body ul, .card-body ol { margin: .5em 0; padding-left: 1.3em; }\n"
     "  .card-body li { margin: .28em 0; color: #344054; line-height: 1.55; }\n"
     "\n"
     "  pre { background: #0f172a; color: #e2e8f0; border-radius: 8px; padding: 11px 13px; overflow-x: auto; margin: 10px 0; }\n"
     "  pre code { padding: 0; font-size: .74rem; line-height: 1.5; }\n"
     "  pre code.hljs { background: transparent; padding: 0; color: #e2e8f0; }\n"
     "  code { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: .84em;\n"
     "    background: var(--stone-bg); color: var(--text); padding: 1px 5px; border-radius: 4px; }\n"
     "\n"
     "  table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: .78rem; }\n"
     "  th, td { border: 1px solid var(--rule); padding: 6px 8px; text-align: left; vertical-align: top; }\n"
     "  th { background: var(--stone-bg); font-size: .7rem; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }\n"
     "  td code { font-size: .92em; }\n"
     "\n"),
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
    actual = strip_engine_additions(
        render.render_html(schema, "discourse", SHARED), ADDITIONS)
    assert actual == expected

def test_html_matches_chapter_when_migrations_are_skipped(chapter_render):
    """Section 04 keeps its head and note but grows no rail."""
    shared = dict(SHARED)
    shared.pop("migration_md")
    chapter = chapter_render("ch07-schema")
    expected = apply_unifications(chapter.render_html("discourse", shared), UNIFICATIONS)
    actual = strip_engine_additions(
        render.render_html(schema, "discourse", shared), ADDITIONS)
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
