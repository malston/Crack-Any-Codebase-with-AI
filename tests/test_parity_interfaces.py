"""The ported interfaces renderer must match ch08's, modulo the named unifications."""
from conftest import apply_unifications
from crack.analyses import interfaces
from crack.core import render

# ch08 already carries both the table CSS and the bar-chart CSS, so it subtracts
# nothing. Its shorter `th` rule unifies to ch07's, which the engine standardises on.
ADDITIONS = []

UNIFICATIONS = [
    # ch08 never picked up the flowchart htmlLabels option the engine standardises on.
    ("mermaid.initialize({ startOnLoad: false, theme: 'neutral', securityLevel: 'loose' });",
     "mermaid.initialize({ startOnLoad: false, theme: 'neutral', securityLevel: 'loose', "
     "flowchart: { htmlLabels: true } });"),

    ("font-size: .98rem", "font-size: .96rem"),
    ("margin: .28em 0; color: #344054; line-height: 1.5;",
     "margin: .28em 0; color: #344054; line-height: 1.55;"),
    ("  th { background: var(--stone-bg); font-size: .7rem; text-transform: uppercase; color: var(--muted); }\n",
     "  th { background: var(--stone-bg); font-size: .7rem; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }\n"
     "  td code { font-size: .92em; }\n"),

    # ch08 places the bar-chart CSS right after .hero-diagram-cap; the engine
    # emits the same block (shared with ch07's overview hero) right before
    # .rail, after the mermaid-diagram rules. Same nine rules, different spot.
    ("  .hero-diagram-cap { font-size: .7rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;\n"
     "    color: var(--accent); margin: 0 2px 9px; }\n"
     "  .groupchart { background: var(--surface); border: 1px solid var(--rule); border-radius: var(--radius);\n"
     "    box-shadow: var(--shadow); padding: 16px 20px; display: flex; flex-direction: column; gap: 7px; }\n"
     "  .gc-row { display: flex; align-items: center; gap: 12px; }\n"
     "  .gc-name { flex: 0 0 220px; font-size: .82rem; font-weight: 600; color: var(--text); text-align: right;\n"
     "    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }\n"
     "  .gc-track { flex: 1; background: var(--stone-bg); border-radius: 5px; overflow: hidden; }\n"
     "  .gc-bar { height: 22px; background: linear-gradient(90deg, #2dd4bf, var(--accent)); border-radius: 5px;\n"
     "    color: #fff; font-size: .72rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;\n"
     "    display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; min-width: 24px; }\n"
     "  @media (max-width: 560px) { .gc-name { flex-basis: 110px; } }\n"
     "  .eyebrow { display: inline-flex; align-items: center; gap: 7px; color: #5eead4;\n"
     "    font-size: .68rem; font-weight: 700; letter-spacing: .18em; text-transform: uppercase; }\n"
     "  .eyebrow::before { content: ''; width: 16px; height: 2px; background: #2dd4bf; border-radius: 2px; }\n"
     "  .hero h1 { font-size: 1.9rem; font-weight: 800; letter-spacing: -.025em; margin: 12px 0 10px; }\n"
     "  .hero .sub { font-size: .94rem; color: #cbeee7; margin: 0 auto; line-height: 1.6; }\n"
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
     "  .diagram pre.mermaid svg { max-width: 100%; height: auto; }\n"
     "\n",
     "  .hero-diagram-cap { font-size: .7rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase;\n"
     "    color: var(--accent); margin: 0 2px 9px; }\n"
     "  .eyebrow { display: inline-flex; align-items: center; gap: 7px; color: #5eead4;\n"
     "    font-size: .68rem; font-weight: 700; letter-spacing: .18em; text-transform: uppercase; }\n"
     "  .eyebrow::before { content: ''; width: 16px; height: 2px; background: #2dd4bf; border-radius: 2px; }\n"
     "  .hero h1 { font-size: 1.9rem; font-weight: 800; letter-spacing: -.025em; margin: 12px 0 10px; }\n"
     "  .hero .sub { font-size: .94rem; color: #cbeee7; margin: 0 auto; line-height: 1.6; }\n"
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
     "  .diagram pre.mermaid svg { max-width: 100%; height: auto; }\n"
     "\n"
     "  .groupchart { background: var(--surface); border: 1px solid var(--rule); border-radius: var(--radius);\n"
     "    box-shadow: var(--shadow); padding: 16px 20px; display: flex; flex-direction: column; gap: 7px; }\n"
     "  .gc-row { display: flex; align-items: center; gap: 12px; }\n"
     "  .gc-name { flex: 0 0 220px; font-size: .82rem; font-weight: 600; color: var(--text); text-align: right;\n"
     "    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }\n"
     "  .gc-track { flex: 1; background: var(--stone-bg); border-radius: 5px; overflow: hidden; }\n"
     "  .gc-bar { height: 22px; background: linear-gradient(90deg, #2dd4bf, var(--accent)); border-radius: 5px;\n"
     "    color: #fff; font-size: .72rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;\n"
     "    display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; min-width: 24px; }\n"
     "  @media (max-width: 560px) { .gc-name { flex-basis: 110px; } }\n"
     "\n"),

    # ch08 hardcoded the per-section rail-width rules after .card-body li; the
    # engine derives them from SECTIONS and places them right after the rail
    # scrollbar rules. Same four rules, same values, different position in the
    # shared page template. Quoted post the two font-size/line-height unifications
    # above, since those already ran over this same text by the time this applies.
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
     "    background: linear-gradient(180deg, #f6fdfb, #fff); font-weight: 700; font-size: .96rem; line-height: 1.35; }\n"
     "  .card-top code { font-size: .82em; }\n"
     "  .card-body { padding: 13px 18px 16px; font-size: .84rem; }\n"
     "  .card-body p { margin: .5em 0; color: #344054; line-height: 1.6; }\n"
     "  .card-body p:first-child { margin-top: 0; }\n"
     "  .card-body strong { color: var(--text); }\n"
     "  .card-body em { color: var(--muted); }\n"
     "  .card-body ul, .card-body ol { margin: .5em 0; padding-left: 1.3em; }\n"
     "  .card-body li { margin: .28em 0; color: #344054; line-height: 1.55; }\n"
     "\n"
     "  .rail.menu .card { flex: 0 0 380px; width: 380px; }\n"
     "  .rail.tour .card { flex: 0 0 380px; width: 380px; }\n"
     "  .rail.flows .card { flex: 0 0 440px; width: 440px; }\n"
     "  .rail.seq .card { flex: 0 0 560px; width: 560px; }\n"
     "\n",
     "  .rail::-webkit-scrollbar-thumb { background: #cbd2dc; border-radius: 5px; }\n"
     "  .rail.menu .card { flex: 0 0 380px; width: 380px; }\n"
     "  .rail.tour .card { flex: 0 0 380px; width: 380px; }\n"
     "  .rail.flows .card { flex: 0 0 440px; width: 440px; }\n"
     "  .rail.seq .card { flex: 0 0 560px; width: 560px; }\n"
     "\n"
     "  .scroll { flex: 1; overflow-y: auto; overscroll-behavior: contain; }\n"
     "  .scroll::-webkit-scrollbar { width: 9px; }\n"
     "  .scroll::-webkit-scrollbar-thumb { background: #dce0e7; border-radius: 5px; }\n"
     "\n"
     "  .card { scroll-snap-align: start; background: var(--surface); border: 1px solid var(--rule);\n"
     "    border-radius: var(--radius); box-shadow: var(--shadow); border-top: 3px solid var(--accent);\n"
     "    display: flex; flex-direction: column; overflow: hidden; max-height: 72vh; }\n"
     "  .card-top { flex-shrink: 0; padding: 14px 18px 12px; border-bottom: 1px solid var(--line);\n"
     "    background: linear-gradient(180deg, #f6fdfb, #fff); font-weight: 700; font-size: .96rem; line-height: 1.35; }\n"
     "  .card-top code { font-size: .82em; }\n"
     "  .card-body { padding: 13px 18px 16px; font-size: .84rem; }\n"
     "  .card-body p { margin: .5em 0; color: #344054; line-height: 1.6; }\n"
     "  .card-body p:first-child { margin-top: 0; }\n"
     "  .card-body strong { color: var(--text); }\n"
     "  .card-body em { color: var(--muted); }\n"
     "  .card-body ul, .card-body ol { margin: .5em 0; padding-left: 1.3em; }\n"
     "  .card-body li { margin: .28em 0; color: #344054; line-height: 1.55; }\n"
     "\n"),

    # ch08 places `table` right after .card-body li (moved above, before `pre`);
    # the engine places it after `pre`/`code`, right before `footer`. Same four
    # rules (already carrying the th-block unification above), different spot.
    ("  table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: .78rem; }\n"
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

    # Security fix: the engine HTML-escapes the extracted mermaid diagram
    # source before writing it into <pre class="mermaid">, closing an
    # HTML-injection hole. ch08 keeps the vulnerable unescaped form; this
    # rewrites only the benign "->>" the fixture sequence diagram contains.
    ("sequenceDiagram\nA->>B: POST", "sequenceDiagram\nA-&gt;&gt;B: POST"),
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
    actual = render.render_html(interfaces, "gitea", shared)   # ADDITIONS is empty
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
