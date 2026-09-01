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
