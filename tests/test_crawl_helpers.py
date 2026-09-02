"""Unit tests for the filesystem and git helpers the flows lean on.

These decide what the model is shown and how its answer is applied: which
files count as a backend layer, which era a commit belongs to, which bulk
deletion is a killed feature rather than a deleted `node_modules`. A wrong
answer here is invisible in the rendered page.
"""
import os

import pytest

from crack.analyses.backend import backend_crawl as bc
from crack.analyses.architecture import arch_crawl as ac
from crack.analyses.interfaces import routes_find as rf
from crack.analyses.git_history.nodes import _era_for, _is_noise_deletion


# --- backend_crawl.classify ---------------------------------------------

@pytest.mark.parametrize("rel, layer", [
    ("config/urls.py", "route"),
    ("web/routes.rb", "route"),
    ("src/api/router.ts", "route"),
    ("src/api/admin_router.ts", "route"),
    ("src/pages/api/notes.ts", "route"),
    ("app/routes/notes.py", "route"),
    ("notes/middleware/auth.py", "middleware"),
    ("notes/auth_decorators.py", "middleware"),
    ("notes/views/notes.py", "handler"),
    ("app/controllers/notes.py", "handler"),
    ("app/notes_controller.rb", "handler"),
    ("notes/services/notes.py", "service"),
    ("app/actions/publish.py", "service"),
    ("core/domain/pricing.go", "service"),
    ("notes/models.py", "database"),
    ("db/schema.rb", "database"),
    ("app/repositories/notes.rb", "database"),
    ("notes/serializers/note.py", "response"),
    ("api/note_serializer.py", "response"),
    ("api/response.py", "response"),
])
def test_classify_maps_a_path_convention_to_its_layer(rel, layer):
    assert bc.classify(rel) == layer


@pytest.mark.parametrize("rel", [
    "README.md",            # not source
    "notes/styles.css",     # not source
    "notes/helpers.py",     # source, but on no layer convention
    "notes/views/notes.test.ts",
    "notes/views/notes.spec.ts",
    "notes/views/notes_test.py",
    "notes/views/Button.stories.tsx",
])
def test_classify_returns_none_for_files_on_no_layer(rel):
    assert bc.classify(rel) is None


# The framework conventions that live at a repo's root in a stock layout.
# `classify` reads only the Next.js pages tree; `is_route_file` reads all three.
ROOT_LEVEL_NEXT_PAGES = "pages/api/notes.ts"
ROOT_LEVEL_CONVENTIONS = [ROOT_LEVEL_NEXT_PAGES, "app/api/notes/route.ts",
                          "cmd/server/main.go"]


def test_classify_reads_a_root_level_next_js_pages_tree():
    assert bc.classify(ROOT_LEVEL_NEXT_PAGES) == "route"


def test_classify_reads_a_next_js_pages_tree_below_a_parent_dir():
    assert bc.classify("src/pages/api/notes.ts") == "route"


# --- routes_find.is_route_file ------------------------------------------

@pytest.mark.parametrize("rel", [
    "config/urls.py",
    "config/routes.rb",
    "src/api/routes.ts",
    "src/api/admin_router.ts",
    "src/pages/api/notes.ts",
    "src/app/notes/route.ts",
    "src/cmd/server/main.go",
    "proto/notes.proto",
    "graphql/schema.graphql",
])
def test_is_route_file_recognises_an_entry_point_convention(rel):
    assert rf.is_route_file(rel)


@pytest.mark.parametrize("rel", [
    "notes/views/notes.py",
    "src/api/routes.test.ts",
    "src/api/routes.spec.ts",
    "src/pages/api/notes.md",
])
def test_is_route_file_rejects_files_that_declare_no_entry_points(rel):
    assert not rf.is_route_file(rel)


@pytest.mark.parametrize("rel", ROOT_LEVEL_CONVENTIONS)
def test_is_route_file_reads_a_root_level_framework_convention(rel):
    assert rf.is_route_file(rel)


def test_classify_is_case_insensitive_about_the_path():
    assert bc.classify("Notes/Views/Notes.py") == "handler"


# --- arch_crawl._classify -----------------------------------------------

@pytest.mark.parametrize("rel, kind", [
    ("docker-compose.yml", "compose"),
    ("compose.yaml", "compose"),
    ("Procfile", "gateway"),
    (".env.example", "env"),
    ("infra/main.tf", "iac"),
    ("next.config.js", "gateway"),
    ("package.json", "package"),
    ("k8s/api.yaml", "k8s"),
    ("deploy/web.yml", "k8s"),
    ("infra/helm/values.yaml", "k8s"),
])
def test_arch_classify_maps_a_config_file_to_its_source(rel, kind):
    assert ac._classify(rel) == kind


@pytest.mark.parametrize("rel", [
    "README.md",
    "notes/models.py",
    "docs/architecture.yaml",   # a yaml on no manifest convention
])
def test_arch_classify_returns_none_for_files_on_no_source(rel):
    assert ac._classify(rel) is None


# --- git_history era lookup ---------------------------------------------

ERAS = [
    {"name": "The prototype", "start": "2019-04", "end": "2020-11"},
    {"name": "The build-out", "start": "2020-12", "end": "2023-02"},
    {"name": "The long tail", "start": "2023-03", "end": "2024-08"},
]


@pytest.mark.parametrize("month, name", [
    ("2019-04", "The prototype"),   # first month of the first era
    ("2020-11", "The prototype"),   # last month of an era
    ("2020-12", "The build-out"),   # first month of the next
    ("2021-07", "The build-out"),
    ("2024-08", "The long tail"),   # last month of the last era
])
def test_era_for_matches_an_inclusive_window(month, name):
    assert _era_for(month, ERAS)["name"] == name


def test_era_for_falls_back_to_the_last_era_outside_every_window():
    """A commit from before or after the named span still needs a home."""
    assert _era_for("2015-01", ERAS)["name"] == "The long tail"
    assert _era_for("2030-01", ERAS)["name"] == "The long tail"


def test_era_for_treats_a_missing_end_as_open_ended():
    open_ended = [{"name": "Now", "start": "2024-01"}]
    assert _era_for("2099-12", open_ended)["name"] == "Now"


def test_era_for_returns_none_when_the_model_named_no_eras():
    assert _era_for("2021-01", []) is None


# --- git_history bulk-deletion filtering --------------------------------

def _deletion(*files):
    return {"files": [f.replace("/", os.sep) for f in files]}


def test_a_deletion_of_real_source_is_not_noise():
    assert not _is_noise_deletion(_deletion(
        "legacy/exports/a.py", "legacy/exports/b.py", "legacy/exports/c.py"))


def test_a_vendored_directory_removal_is_noise():
    assert _is_noise_deletion(_deletion(
        "node_modules/left-pad/index.js", "node_modules/left-pad/package.json",
        "src/app.py"))


def test_a_build_output_removal_is_noise():
    assert _is_noise_deletion(_deletion("dist/main.js", "dist/main.js.map"))


def test_noise_needs_a_strict_majority_not_a_tie():
    """Half vendored, half real is a mixed commit — keep it as a candidate."""
    assert not _is_noise_deletion(_deletion(
        "node_modules/a/index.js", "node_modules/b/index.js",
        "src/exporter.py", "src/schedule.py"))


def test_one_extra_skipped_file_tips_a_tie_into_noise():
    assert _is_noise_deletion(_deletion(
        "node_modules/a/index.js", "node_modules/b/index.js",
        "node_modules/c/index.js", "src/exporter.py", "src/schedule.py"))


def test_a_skip_directory_counts_anywhere_in_the_path():
    assert _is_noise_deletion(_deletion(
        "packages/web/node_modules/a.js", "packages/api/vendor/b.rb"))


def test_arch_sdk_grep_reports_nothing_outside_a_git_repo(tmp_path):
    """`_sdk_grep` returns "" for a failed `git grep` and for one that matched
    nothing alike, so a missing git binary silently costs the architecture
    bundle its strongest evidence. This pins the current behaviour."""
    (tmp_path / "app.py").write_text("import stripe\n", encoding="utf-8")
    assert ac._sdk_grep(str(tmp_path)) == ""


def test_arch_sdk_grep_finds_an_sdk_import_in_a_git_repo(fixture_repo):
    lines = ac._sdk_grep(fixture_repo)
    assert "notes/billing.js" in lines
    assert "stripe" in lines
