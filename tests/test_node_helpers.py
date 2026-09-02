"""Unit tests for the pure helpers each analysis's nodes call.

The flow tests run these through a fixture repo that happens to hit only one
branch apiece: one table, so no deep-dive batching; one grave, so no
per-area de-duplication; four commits, so no sampling. The boundaries are here.
"""
import importlib
import os

import pytest

from crack.analyses.git_history import gitlog as gl
from crack.analyses.schema import nodes as schema_nodes

# `crack.core` re-exports a function named `crawl`, which shadows the submodule
# of the same name as a package attribute, so the module is imported by path.
crawl_mod = importlib.import_module("crack.core.crawl")


# --- schema table extraction --------------------------------------------

SCHEMA_SQL = """
CREATE TABLE notes (id TEXT PRIMARY KEY);
CREATE TABLE users (id TEXT PRIMARY KEY);
CREATE TABLE "note_tags" (note_id TEXT, tag_id TEXT);
"""

PRISMA = "model Note {\n  id String @id\n}\nmodel Tag {\n  id String @id\n}\n"

DJANGO = "class Note(models.Model):\n    pass\n\nclass Tag(models.Model):\n    pass\n"


@pytest.mark.parametrize("text, expected", [
    (SCHEMA_SQL, {"notes", "users", "note_tags"}),
    (PRISMA, {"note", "tag"}),
    (DJANGO, {"note", "tag"}),
])
def test_schema_table_names_reads_every_declaration_style(text, expected):
    assert schema_nodes.schema_table_names(text) == expected


def test_schema_table_names_finds_nothing_in_prose():
    assert schema_nodes.schema_table_names("no tables here") == set()


ERD = """erDiagram
  notes ||--o{ note_tags : tagged
  users ||--o{ notes : writes
"""


def test_tables_from_erd_keeps_order_and_drops_duplicates():
    known = {"notes", "users", "note_tags"}
    assert schema_nodes.tables_from_erd(ERD, known) == ["notes", "note_tags", "users"]


def test_tables_from_erd_drops_entities_that_are_not_real_tables():
    """A model that invents an entity must not put it on the page."""
    assert schema_nodes.tables_from_erd(ERD, {"notes"}) == ["notes"]


def test_tables_from_erd_returns_nothing_without_relationship_lines():
    assert schema_nodes.tables_from_erd("erDiagram\n  notes {\n  }\n", {"notes"}) == []


def test_tables_from_headers_reads_backticked_names_in_card_headers():
    md = ("### Step 1 · `notes` and `users`\n\nprose\n"
          "### Step 2 · `notes`\n\nmore prose\n")
    assert schema_nodes.tables_from_headers(md) == ["notes", "users"]


def test_tables_from_headers_ignores_backticks_outside_headers():
    assert schema_nodes.tables_from_headers("prose about `notes`\n") == []


# --- git_history commit sampling ----------------------------------------

def _commits(n):
    return [{"hash": f"{i:07d}", "month": "2024-01", "author": "Test",
             "subject": f"commit {i}", "files": ["src/app.py"]} for i in range(n)]


def test_a_short_era_is_not_sampled():
    commits = _commits(5)
    assert gl.sample_commits(commits, 10) == (commits, False)


def test_an_era_exactly_at_the_cap_is_not_sampled():
    commits = _commits(10)
    assert gl.sample_commits(commits, 10) == (commits, False)


def test_a_long_era_is_thinned_and_flagged():
    sampled, was_sampled = gl.sample_commits(_commits(100), 10)
    assert was_sampled
    assert len(sampled) <= 11          # the stride, plus the forced last commit
    assert sampled[0]["subject"] == "commit 0"
    assert sampled[-1]["subject"] == "commit 99"


def test_sampling_keeps_the_commits_in_order():
    sampled, _ = gl.sample_commits(_commits(100), 10)
    assert [c["subject"] for c in sampled] == sorted(
        (c["subject"] for c in sampled), key=lambda s: int(s.split()[1]))


def test_a_zero_cap_disables_sampling():
    commits = _commits(50)
    assert gl.sample_commits(commits, 0) == (commits, False)


def test_commit_stream_is_one_line_per_commit():
    lines = gl.commit_stream(_commits(3)).splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("2024-01 | Test | src/")


# --- core.crawl include and exclude -------------------------------------

def _tree(root):
    # `legacy/`, not `docs/`: the latter is on DEFAULT_SKIP_DIR, so an exclude
    # pattern aimed at it would pass without the pattern doing any work.
    for rel in ("src/core/app.py", "src/web/view.py", "pkg/lib.py",
                "legacy/old/notes.py", "src/core/app_test.py"):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x = 1\n", encoding="utf-8")


def _rels(root, paths):
    return sorted(os.path.relpath(p, root).replace(os.sep, "/") for p in paths)


def test_include_keeps_only_matching_subtrees(tmp_path):
    _tree(tmp_path)
    kept = crawl_mod.list_files(str(tmp_path), include=["src/core/**", "pkg/**"])
    assert _rels(tmp_path, kept) == ["pkg/lib.py", "src/core/app.py",
                                     "src/core/app_test.py"]


def test_exclude_drops_matching_paths(tmp_path):
    _tree(tmp_path)
    kept = crawl_mod.list_files(
        str(tmp_path), exclude=["legacy/old/**", "**/*_test.py"])
    assert _rels(tmp_path, kept) == ["pkg/lib.py", "src/core/app.py",
                                     "src/web/view.py"]


def test_exclude_is_applied_after_include(tmp_path):
    _tree(tmp_path)
    kept = crawl_mod.list_files(
        str(tmp_path), include=["src/**"], exclude=["**/*_test.py"])
    assert _rels(tmp_path, kept) == ["src/core/app.py", "src/web/view.py"]


def test_no_patterns_keeps_everything_the_extension_filter_allows(tmp_path):
    _tree(tmp_path)
    assert _rels(tmp_path, crawl_mod.list_files(str(tmp_path))) == [
        "legacy/old/notes.py", "pkg/lib.py", "src/core/app.py",
        "src/core/app_test.py", "src/web/view.py"]


def test_the_default_skip_list_prunes_a_directory_before_any_pattern(tmp_path):
    _tree(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "notes.py").write_text("x = 1\n", encoding="utf-8")
    assert "docs/notes.py" not in _rels(
        tmp_path, crawl_mod.list_files(str(tmp_path)))


def test_an_include_that_matches_nothing_keeps_nothing(tmp_path):
    _tree(tmp_path)
    assert crawl_mod.list_files(str(tmp_path), include=["nowhere/**"]) == []


def test_a_file_over_the_size_cap_is_dropped(tmp_path):
    _tree(tmp_path)
    (tmp_path / "src/core/big.py").write_text("y" * 5000, encoding="utf-8")
    kept = crawl_mod.list_files(str(tmp_path), max_file_bytes=1000)
    assert "src/core/big.py" not in _rels(tmp_path, kept)


def test_safe_read_skips_a_file_it_cannot_decode(tmp_path):
    path = tmp_path / "binary.py"
    path.write_bytes(b"\xff\xfe\x00 not utf-8")
    assert crawl_mod.safe_read(str(path)) is None


def test_safe_read_returns_utf8_content(tmp_path):
    path = tmp_path / "unicode.py"
    path.write_text("# café\n", encoding="utf-8")
    assert crawl_mod.safe_read(str(path)) == "# café\n"
