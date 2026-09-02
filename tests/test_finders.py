"""Unit tests for the schema and route finders.

Each analysis reaches its subject through one of these. The flow tests exercise
only the convention the fixture repo happens to use — a raw `schema.sql` and an
exactly-correct handler path — so the branches for every other framework, and
the recovery when the model names a path that is nearly right, are covered here.
"""
import os

import pytest

from crack.analyses.interfaces import routes_find as rf
from crack.analyses.schema import schema_find as sf


def _write(root, rel, text=""):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# --- schema_find.find_schema --------------------------------------------

def test_finds_a_prisma_schema(tmp_path):
    _write(tmp_path, "packages/db/schema.prisma", "model Note {\n  id String @id\n}\n")
    found = sf.find_schema(str(tmp_path))
    assert found["kind"] == "prisma"
    assert found["path"] == os.path.join("packages", "db", "schema.prisma")
    assert "model Note" in found["text"]


def test_prefers_the_largest_prisma_schema(tmp_path):
    """A package fixture schema must not win over the application's."""
    _write(tmp_path, "packages/fixtures/schema.prisma", "model A {}\n")
    _write(tmp_path, "packages/db/schema.prisma",
           "model Note {\n  id String @id\n  text String\n}\n" + "// pad\n" * 40)
    assert sf.find_schema(str(tmp_path))["path"] == os.path.join(
        "packages", "db", "schema.prisma")


def test_finds_a_rails_schema_only_under_db(tmp_path):
    _write(tmp_path, "db/schema.rb", "create_table :notes\n")
    found = sf.find_schema(str(tmp_path))
    assert found["kind"] == "rails"
    assert found["path"] == os.path.join("db", "schema.rb")


def test_a_schema_rb_outside_db_is_not_a_rails_schema(tmp_path):
    _write(tmp_path, "vendor_docs/schema.rb", "create_table :notes\n")
    assert sf.find_schema(str(tmp_path))["kind"] is None


def test_concatenates_django_model_files_when_there_is_no_single_schema(tmp_path):
    _write(tmp_path, "notes/models.py", "class Note(models.Model):\n    pass\n")
    _write(tmp_path, "users/models.py", "class User(models.Model):\n    pass\n")
    found = sf.find_schema(str(tmp_path))
    assert found["kind"] == "models"
    assert found["path"] == "2 models.py files"
    assert "class Note" in found["text"] and "class User" in found["text"]
    assert "notes/models.py" in found["text"].replace(os.sep, "/")


def test_prisma_outranks_rails_sql_and_models(tmp_path):
    _write(tmp_path, "packages/db/schema.prisma", "model Note {}\n")
    _write(tmp_path, "db/schema.rb", "create_table :notes\n")
    _write(tmp_path, "schema.sql", "CREATE TABLE notes (id TEXT);\n")
    _write(tmp_path, "notes/models.py", "class Note: pass\n")
    assert sf.find_schema(str(tmp_path))["kind"] == "prisma"


def test_sql_outranks_models(tmp_path):
    _write(tmp_path, "schema.sql", "CREATE TABLE notes (id TEXT);\n")
    _write(tmp_path, "notes/models.py", "class Note: pass\n")
    assert sf.find_schema(str(tmp_path))["kind"] == "sql"


def test_an_override_wins_over_every_convention(tmp_path):
    _write(tmp_path, "schema.sql", "CREATE TABLE notes (id TEXT);\n")
    _write(tmp_path, "odd/place.sql", "CREATE TABLE picked (id TEXT);\n")
    found = sf.find_schema(str(tmp_path), override="odd/place.sql")
    assert found["kind"] == "override"
    assert "picked" in found["text"]


def test_an_absolute_override_path_is_used_as_given(tmp_path):
    target = _write(tmp_path, "odd/place.sql", "CREATE TABLE picked (id TEXT);\n")
    found = sf.find_schema(str(tmp_path), override=str(target))
    assert found["kind"] == "override"
    assert "picked" in found["text"]


def test_a_repo_with_no_schema_reports_nothing_found(tmp_path):
    _write(tmp_path, "main.py", "print('hi')\n")
    assert sf.find_schema(str(tmp_path)) == {"kind": None, "path": None, "text": ""}


def test_a_schema_inside_a_skipped_directory_is_ignored(tmp_path):
    _write(tmp_path, "node_modules/pkg/schema.prisma", "model Vendored {}\n")
    assert sf.find_schema(str(tmp_path))["kind"] is None


# --- schema_find.find_migrations ----------------------------------------

def test_finds_rails_migrations_under_db_migrate(tmp_path):
    for name in ("20240101120000_create_notes.rb", "20240310090000_add_owner.rb"):
        _write(tmp_path, f"db/migrate/{name}")
    reldir, names = sf.find_migrations(str(tmp_path))
    assert reldir == os.path.join("db", "migrate")
    assert names == ["20240101120000_create_notes", "20240310090000_add_owner"]


def test_finds_prisma_migration_subdirectories(tmp_path):
    for name in ("20240101120000_init", "20240310090000_add_owner"):
        _write(tmp_path, f"prisma/migrations/{name}/migration.sql")
    reldir, names = sf.find_migrations(str(tmp_path))
    assert reldir == os.path.join("prisma", "migrations")
    assert names == ["20240101120000_init", "20240310090000_add_owner"]


def test_picks_the_migration_directory_with_the_most_entries(tmp_path):
    _write(tmp_path, "old/migrations/20200101000000_one.sql")
    for i in range(3):
        _write(tmp_path, f"notes/migrations/2024010112000{i}_step.sql")
    reldir, names = sf.find_migrations(str(tmp_path))
    assert reldir == os.path.join("notes", "migrations")
    assert len(names) == 3


def test_untimestamped_entries_are_not_migrations(tmp_path):
    _write(tmp_path, "notes/migrations/__init__.py")
    _write(tmp_path, "notes/migrations/README.md")
    assert sf.find_migrations(str(tmp_path)) == (None, [])


def test_a_repo_with_no_migration_directory_reports_nothing(tmp_path):
    _write(tmp_path, "schema.sql", "CREATE TABLE notes (id TEXT);\n")
    assert sf.find_migrations(str(tmp_path)) == (None, [])


# --- routes_find.read_files ---------------------------------------------

HANDLER = "export default function handler(req, res) { res.json({ok: true}); }\n"


def test_reads_a_path_the_model_gave_exactly(tmp_path):
    _write(tmp_path, "src/pages/api/notes.ts", HANDLER)
    source, resolved = rf.read_files(str(tmp_path), ["src/pages/api/notes.ts"])
    assert resolved == ["src/pages/api/notes.ts"]
    assert "handler" in source


def test_resolves_a_path_missing_its_leading_directory(tmp_path):
    """The model often names a path that is right except for a leading dir."""
    _write(tmp_path, "apps/web/src/pages/api/notes.ts", HANDLER)
    source, resolved = rf.read_files(str(tmp_path), ["src/pages/api/notes.ts"])
    assert resolved == [os.path.join("apps", "web", "src", "pages", "api", "notes.ts")]
    assert "handler" in source


def test_resolves_a_bare_filename_by_suffix(tmp_path):
    _write(tmp_path, "src/api/notes.ts", HANDLER)
    _source, resolved = rf.read_files(str(tmp_path), ["notes.ts"])
    assert resolved == [os.path.join("src", "api", "notes.ts")]


def test_strips_backticks_and_a_leading_slash_from_a_picked_path(tmp_path):
    _write(tmp_path, "src/api/notes.ts", HANDLER)
    _source, resolved = rf.read_files(str(tmp_path), ["`/src/api/notes.ts`"])
    assert resolved == [os.path.join("src", "api", "notes.ts")]


def test_a_path_that_matches_nothing_is_dropped(tmp_path):
    _write(tmp_path, "src/api/notes.ts", HANDLER)
    source, resolved = rf.read_files(
        str(tmp_path), ["src/api/invented.ts", "src/api/notes.ts"])
    assert resolved == [os.path.join("src", "api", "notes.ts")]
    assert "invented" not in source


def test_an_empty_file_contributes_nothing(tmp_path):
    _write(tmp_path, "src/api/blank.ts", "\n\n")
    source, resolved = rf.read_files(str(tmp_path), ["src/api/blank.ts"])
    assert resolved == []
    assert source == ""


def test_reads_at_most_max_files(tmp_path):
    for i in range(5):
        _write(tmp_path, f"src/api/h{i}.ts", HANDLER)
    _source, resolved = rf.read_files(
        str(tmp_path), [f"src/api/h{i}.ts" for i in range(5)], max_files=2)
    assert len(resolved) == 2


def test_stops_before_exceeding_the_character_budget(tmp_path):
    """Each block carries two 60-char rules and a path header on top of the
    file, so the budget is sized from a real block rather than the file size."""
    for name in ("a.ts", "b.ts"):
        _write(tmp_path, f"src/api/{name}", "x" * 100)
    one_block = len(rf.read_files(str(tmp_path), ["src/api/a.ts"])[0])
    _source, resolved = rf.read_files(
        str(tmp_path), ["src/api/a.ts", "src/api/b.ts"], max_chars=one_block + 10)
    assert resolved == [os.path.join("src", "api", "a.ts")]


def test_no_paths_at_all_reads_nothing(tmp_path):
    assert rf.read_files(str(tmp_path), []) == ("", [])


# --- routes_find.crawl_routes -------------------------------------------

def test_crawl_routes_puts_manifests_before_single_handlers(tmp_path):
    _write(tmp_path, "src/pages/api/notes.ts", HANDLER)
    _write(tmp_path, "config/urls.py", "urlpatterns = []\n")
    routes, files, kept = rf.crawl_routes(str(tmp_path))
    assert kept == 2
    assert set(files) == {os.path.join("config", "urls.py"),
                          os.path.join("src", "pages", "api", "notes.ts")}
    assert routes.index("urls.py") < routes.index("notes.ts")


def test_crawl_routes_finds_nothing_in_a_repo_with_no_surface(tmp_path):
    _write(tmp_path, "main.py", "print('hi')\n")
    routes, files, kept = rf.crawl_routes(str(tmp_path))
    assert (routes, files, kept) == ("", [], 0)


@pytest.mark.parametrize("skipped", ["node_modules", "tests", "dist"])
def test_crawl_routes_skips_vendored_and_test_directories(tmp_path, skipped):
    _write(tmp_path, f"{skipped}/pkg/urls.py", "urlpatterns = []\n")
    assert rf.crawl_routes(str(tmp_path))[2] == 0
