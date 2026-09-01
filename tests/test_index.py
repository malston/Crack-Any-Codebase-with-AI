import os
from crack.core.index import write_index

def test_links_every_written_report(tmp_path):
    written = {"backend": (str(tmp_path / "backend"), ""),
               "schema": (str(tmp_path / "schema"), "")}
    path = write_index(str(tmp_path), "zulip", written, [])
    html = open(path).read()
    assert path == os.path.join(str(tmp_path), "index.html")
    assert 'href="backend/index.html"' in html
    assert 'href="schema/index.html"' in html
    assert "zulip" in html

def test_names_failed_analyses(tmp_path):
    path = write_index(str(tmp_path), "zulip",
                       {"backend": (str(tmp_path / "backend"), "")},
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

def test_card_shows_welcome_when_present(tmp_path):
    written = {"backend": (str(tmp_path / "backend"), "A sharp read on this backend.")}
    path = write_index(str(tmp_path), "zulip", written, [])
    html = open(path).read()
    assert "A sharp read on this backend." in html

def test_card_falls_back_to_static_note_when_welcome_empty(tmp_path):
    written = {"backend": (str(tmp_path / "backend"), "")}
    path = write_index(str(tmp_path), "zulip", written, [])
    html = open(path).read()
    from crack.core.index import NOTES
    assert NOTES["backend"] in html
