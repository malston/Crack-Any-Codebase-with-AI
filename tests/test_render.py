import types
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
    assert html.count(".rail.pipe .card") == 1
    assert ".rail.code .card" not in html
    assert ".rail.trace .card" not in html

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
