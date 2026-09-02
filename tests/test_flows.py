"""Wire-level tests: run each analysis's real flow with the model stubbed out.

The parity tests call renderers directly with a hand-built `shared` dict, so
nothing else in the suite constructs a flow, runs a node's prep/exec/post, or
touches a crawl helper. Every runtime bug found while building the CLI lived in
that gap: a dropped import, a wrong helper import, a prompts directory computed
from the old chapter layout. These tests close it — they read the real prompt
files off disk, run the real crawlers over a fixture repo, and only the model's
replies are canned.
"""
import importlib
import re
from types import SimpleNamespace

import pytest

# The opening clause of `crack.core.overview._PROMPT`; that prompt is a module
# constant rather than a file, so it is routed by its text.
OVERVIEW_MARKER = "writing the overview at the top of a page"
# The opening clause of `interfaces.nodes._PICK_PROMPT`, likewise inline.
PICK_MARKER = "pick the SINGLE most"

CARD = "### {}\n\n{}\n"


def _overview_reply(prompt):
    """Answer the overview prompt using the exact headers it asked for."""
    titles, seen = [], set()
    for title in re.findall(r'^## (.+?)\s*$', prompt, re.MULTILINE):
        if title not in seen:
            seen.add(title)
            titles.append(title)
    assert "Welcome" in titles, "the overview prompt no longer asks for ## Welcome"
    return "\n".join(f"## {t}\n\nCanned copy for {t}.\n" for t in titles)


def replies(by_prompt, extra=()):
    """Route a canned reply by the prompt file it came from.

    `by_prompt` maps a prompt filename to the model's reply; `extra` holds
    (marker, reply) pairs for the two prompts built inline in Python. An
    unrouted prompt fails the test rather than falling back to something bland,
    so a new LLM call cannot slip in unnoticed.
    """
    def reply(prompt):
        if OVERVIEW_MARKER in prompt:
            return _overview_reply(prompt)
        for marker, text in extra:
            if marker in prompt:
                return text
        for name, text in by_prompt.items():
            if f"<<{name}>>" in prompt:
                return text
        raise AssertionError(f"no canned reply for this prompt:\n{prompt[:400]}")
    return reply


def run_flow(name, reply, stub_llm, repo, out_dir, **args):
    """Run one analysis's real flow end to end. Returns (shared, prompts seen)."""
    analysis = importlib.import_module(f"crack.analyses.{name}")
    prompts = stub_llm(reply)
    shared = analysis.init_shared(
        SimpleNamespace(repo_path=repo, **args), str(out_dir))
    analysis.build_flow().run(shared)
    return shared, prompts


def assert_overview(shared):
    """OverviewNode degrades silently, so a broken run still looks like a pass."""
    assert shared["overview"]["welcome"], (
        "no welcome copy — the overview node fell back after failing twice")


# --- backend (ch10) ------------------------------------------------------

BACKEND_REPLIES = {
    "pipeline.md": (
        CARD.format("Route", "Six layers, one per hop.")
        + "\n```mermaid\nflowchart LR\n  route --> handler --> database\n```\n"),
    "layer-code.md": CARD.format("Handler — novel", "The handler owns validation."),
    "trace.md": (
        CARD.format("The trace", "**Endpoint:** POST /notes\n\nOne write, one row.")),
}


def test_backend_flow_fills_every_key_the_renderer_reads(
        stub_llm, fixture_repo, tmp_path):
    shared, prompts = run_flow(
        "backend", replies(BACKEND_REPLIES), stub_llm, fixture_repo, tmp_path)

    assert shared["layer_counts"] == {
        "route": 1, "middleware": 1, "handler": 1,
        "service": 1, "database": 1, "response": 1}
    assert shared["pipeline_md"].startswith("### Route")
    assert shared["pipeline_diagram"].startswith("flowchart LR")
    assert shared["layercode_md"].startswith("### Handler")
    assert shared["trace_endpoint"] == "POST /notes"
    assert_overview(shared)
    assert len(prompts) == 4


@pytest.mark.xfail(strict=True, reason=(
    "backend_crawl.build_bundle emits its section headers even when it found "
    "no files, so `assert bundle.strip()` never fires and the model is asked "
    "to describe an empty bundle. Inherited from ch10."))
def test_backend_refuses_a_repo_with_no_backend(stub_llm, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(AssertionError, match="No backend source found"):
        run_flow("backend", replies(BACKEND_REPLIES), stub_llm, str(empty), tmp_path)


# --- architecture (ch09) -------------------------------------------------

ARCHITECTURE_REPLIES = {
    "inventory.md": (
        CARD.format("1 · api", "**Shape verdict:** a monolith with two datastores")
        + "\n```mermaid\nflowchart LR\n  api --> db\n  api --> cache\n```\n"),
    "tech-stack.md": CARD.format("1 · api", "Flask on Postgres."),
    "trace-request.md": CARD.format("Create a note", "api → db, one round trip."),
}


def test_architecture_flow_fills_every_key_the_renderer_reads(
        stub_llm, fixture_repo, tmp_path):
    shared, prompts = run_flow(
        "architecture", replies(ARCHITECTURE_REPLIES), stub_llm, fixture_repo, tmp_path)

    stats = shared["arch_stats"]
    assert stats["config_files"] >= 1 and stats["env_vars"] >= 1 and stats["deps"] >= 1
    assert shared["shape_verdict"] == "a monolith with two datastores"
    assert shared["arch_diagram"].startswith("flowchart LR")
    assert shared["techstack_md"].startswith("### 1 · api")
    assert shared["trace_md"].startswith("### Create a note")
    assert_overview(shared)
    assert len(prompts) == 4


def test_architecture_refuses_a_repo_with_no_service_config(stub_llm, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(AssertionError, match="No architecture sources found"):
        run_flow("architecture", replies(ARCHITECTURE_REPLIES), stub_llm,
                 str(empty), tmp_path)


# --- interfaces (ch08) ---------------------------------------------------

INTERFACES_REPLIES = {
    "api-menu.md": (
        "The surface is one resource wide.\n\n"
        + CARD.format("Notes", "Create and read a note.")
        + "\n## The tour\n\n" + CARD.format("Step 1", "Start at POST /notes.")),
    "trace-action.md": CARD.format("Create a note", "One gesture, one write."),
    "endpoint-sequence.md": (
        CARD.format("POST /notes", "The write path.")
        + "\n```mermaid\nsequenceDiagram\n  client->>api: POST /notes\n```\n"),
}
PICK_REPLY = '```yaml\nendpoint: "POST /notes"\nfiles:\n  - notes/views/notes.py\n```'


def test_interfaces_flow_fills_every_key_the_renderer_reads(
        stub_llm, fixture_repo, tmp_path):
    shared, prompts = run_flow(
        "interfaces", replies(INTERFACES_REPLIES, [(PICK_MARKER, PICK_REPLY)]),
        stub_llm, fixture_repo, tmp_path)

    assert shared["route_files"] == ["config/urls.py"]
    assert shared["group_names"] == ["Notes"]
    assert shared["opener"] == "The surface is one resource wide."
    assert shared["tour_md"].startswith("### Step 1")
    assert shared["flows_md"].startswith("### Create a note")
    assert shared["sequence_endpoint"] == "POST /notes"
    assert shared["sequence_files"] == ["notes/views/notes.py"]
    assert "sequenceDiagram" in shared["sequence_md"]
    assert_overview(shared)
    assert len(prompts) == 5


def test_interfaces_still_draws_a_sequence_when_the_pick_is_unusable(
        stub_llm, fixture_repo, tmp_path):
    """The endpoint pick is wrapped in a bare `except Exception: pass`, so a
    junk reply leaves the diagram to be drawn from route names alone."""
    shared, _ = run_flow(
        "interfaces", replies(INTERFACES_REPLIES, [(PICK_MARKER, "not yaml at all")]),
        stub_llm, fixture_repo, tmp_path)

    assert shared["sequence_endpoint"] == ""
    assert shared["sequence_files"] == []
    assert "sequenceDiagram" in shared["sequence_md"]


def test_interfaces_refuses_a_repo_with_no_route_files(stub_llm, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    (empty / "main.py").write_text("print('hi')\n")
    with pytest.raises(AssertionError, match="No route/surface files found"):
        run_flow("interfaces", replies(INTERFACES_REPLIES), stub_llm,
                 str(empty), tmp_path)


# --- schema (ch07) -------------------------------------------------------

SCHEMA_REPLIES = {
    "schema-tour.md": (
        "**Product:** Notes\n\n**Schema one-liner:** one table, three columns\n\n"
        + CARD.format("Step 1 · `notes`", "Everything hangs off one table.")
        + "\n```mermaid\nerDiagram\n  notes ||--o{ notes : supersedes\n```\n"),
    "trace-flows.md": CARD.format("Create a note", "One insert into `notes`."),
    "table-deep-dive.md": CARD.format("`notes`", "id, text, created_at."),
    "migration-acts.md": CARD.format("Act 1 · first tables", "Four migrations, one act."),
}


def test_schema_flow_fills_every_key_the_renderer_reads(
        stub_llm, fixture_repo, tmp_path):
    shared, prompts = run_flow(
        "schema", replies(SCHEMA_REPLIES), stub_llm, fixture_repo, tmp_path,
        schema=None)

    assert shared["schema_kind"] == "sql"
    assert shared["schema_path"] == "schema.sql"
    assert shared["migration_names"] == [
        "20240101120000_create_notes", "20240310090000_add_created_at",
        "20240612093000_add_notes_owner", "20241104150000_index_notes_owner"]
    assert shared["product_name"] == "Notes"
    assert shared["one_liner"] == "one table, three columns"
    assert shared["erd"].startswith("erDiagram")
    assert shared["table_list"] == ["notes"]
    assert shared["deepdive_md"].startswith("### `notes`")
    assert shared["migration_md"].startswith("### Act 1")
    assert_overview(shared)
    assert len(prompts) == 5


def test_schema_declines_to_cluster_too_few_migrations(
        stub_llm, fixture_repo, tmp_path, monkeypatch):
    """Under four migrations there is no roadmap to reconstruct, so the node
    skips the call rather than asking the model to invent one."""
    from crack.analyses.schema import schema_find
    monkeypatch.setattr(schema_find, "find_migrations",
                        lambda repo: ("notes/migrations", ["0001_a", "0002_b"]))
    shared, prompts = run_flow(
        "schema", replies(SCHEMA_REPLIES), stub_llm, fixture_repo, tmp_path,
        schema=None)

    assert shared["migration_md"] is None
    assert not any("<<migration-acts.md>>" in p for p in prompts)


def test_schema_refuses_a_repo_with_no_schema(stub_llm, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(AssertionError, match="No schema file found"):
        run_flow("schema", replies(SCHEMA_REPLIES), stub_llm, str(empty),
                 tmp_path, schema=None)


# --- git_history (ch06) --------------------------------------------------

GIT_HISTORY_REPLIES = {
    "name-eras.md": (
        '```json\n{"eras": [{"name": "The build-out", "start": "2000-01", '
        '"end": "9999-12", "description": "One team, one API.", '
        '"turning_point": "the CSV exporter was cut"}]}\n```'),
    "profile-era.md": (
        '```json\n{"cast": {"narrative": "One author, start to finish."}, '
        '"mood": {"narrative": "Steady, unhurried."}}\n```'),
    "graveyard-entry.md": CARD.format(
        "The CSV exporter", "Ten files, shipped and cut in the same era."),
}


def test_git_history_flow_fills_every_key_the_renderer_reads(
        stub_llm, fixture_repo, tmp_path):
    shared, prompts = run_flow(
        "git_history", replies(GIT_HISTORY_REPLIES), stub_llm, fixture_repo, tmp_path)

    assert len(shared["commits"]) == 4
    assert shared["commits_asc"][0]["subject"].startswith("feat: notes API")
    assert [e["name"] for e in shared["eras"]] == ["The build-out"]
    assert len(shared["profiles"]) == 1
    assert shared["profiles"][0]["commit_count"] == 4
    assert shared["profiles"][0]["profile"]["mood"]["narrative"] == "Steady, unhurried."

    assert len(shared["graves"]) == 1
    grave = shared["graves"][0]
    assert grave["commit"]["count"] == 10
    assert grave["commit"]["scope"] == "legacy/exports"
    assert grave["era"]["name"] == "The build-out"
    assert grave["entry_md"].startswith("### The CSV exporter")
    assert_overview(shared)
    assert len(prompts) == 4


def test_git_history_leaves_the_graveyard_empty_without_a_bulk_deletion(
        stub_llm, tmp_path):
    from tests.conftest import _git
    repo = tmp_path / "thin"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "main.py").write_text("print('hi')\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "feat: the whole thing")

    shared, _ = run_flow("git_history", replies(GIT_HISTORY_REPLIES), stub_llm,
                         str(repo), tmp_path)
    assert shared["bulk_dels"] == []
    assert shared["graves"] == []


# --- product_intent (ch05) -----------------------------------------------

PRODUCT_INTENT_REPLIES = {
    "pain-scene.md": "Someone re-reads the same handler for the third time.",
    "variant-sentence.md": "Notes, but the schema explains itself.",
    "competitive-positioning.md": '''```yaml
competitors:
  - name: "A wiki"
    cells:
      - verdict: "no"
        detail: "Prose only, no schema."
      - verdict: "partial"
        detail: "Search, but no structure."
      - verdict: "yes"
        detail: "Anyone can edit."
  - name: "A notebook"
    cells:
      - verdict: "yes"
        detail: "Structured cells."
      - verdict: "no"
        detail: "No shared surface."
      - verdict: "partial"
        detail: "Export only."
dimensions:
  - "Structured storage"
  - "Shared access"
  - "Portability"
sacrifices: "Rich text formatting."
gains: "One table anyone can query."
why_incumbents_cannot_copy: "Their format is the product."
```''',
    "surprises-and-absences.md": '''```yaml
present:
  - headline: "Auth is a decorator"
    where: "notes/middleware/auth.py"
    bet: "Every route is protected by default."
absent:
  - headline: "No pagination"
    evidence: "read_note returns one row, no list endpoint."
    tradeoff: "Simplicity now, a rewrite when lists arrive."
```''',
}


def test_product_intent_flow_fills_every_key_the_renderer_reads(
        stub_llm, fixture_repo, tmp_path):
    shared, prompts = run_flow(
        "product_intent", replies(PRODUCT_INTENT_REPLIES), stub_llm,
        fixture_repo, tmp_path, include=[], exclude=[])

    assert shared["codebase"], "the crawler returned nothing"
    assert shared["pain"].startswith("Someone re-reads")
    assert shared["variant"] == "Notes, but the schema explains itself."
    assert [c["name"] for c in shared["positioning"]["competitors"]] == [
        "A wiki", "A notebook"]
    assert len(shared["positioning"]["dimensions"]) == 3
    assert shared["surprises"]["present"][0]["headline"] == "Auth is a decorator"
    assert shared["surprises"]["absent"][0]["headline"] == "No pagination"
    # This analysis has no overview node; the image needs Gemini, which the
    # stub fixture removes from the environment.
    assert "overview" not in shared
    assert shared["pain_image_path"] is None
    assert len(prompts) == 4
