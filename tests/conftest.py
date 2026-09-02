"""Shared test helpers. The parity tests load each chapter's renderer off disk."""
import importlib
import importlib.util
import os
import pathlib
import subprocess
import sys
import time

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

@pytest.fixture(scope="session")
def chapter_render():
    """Load a chapter's render.py as a module, without installing the chapter."""
    def _load(chapter_dir):
        workflow = REPO_ROOT / chapter_dir / "workflow"
        path = workflow / "render.py"
        name = f"_chapter_render_{chapter_dir.replace('-', '_')}"
        if name in sys.modules:
            return sys.modules[name]
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        # The chapter renderers sys.path.insert to reach utils/; let them.
        sys.path.insert(0, str(workflow))
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.remove(str(workflow))
        return module
    return _load

def apply_unifications(html, pairs):
    """Rewrite a chapter's HTML with the deliberate unifications applied.

    Each pair is (chapter_text, unified_text). Every pair must actually match,
    so a unification that silently stops applying fails the test.
    """
    for old, new in pairs:
        if old != new:
            assert old in html, f"unification no longer applies: {old!r}"
            html = html.replace(old, new)
    return html


def strip_engine_additions(html, blocks):
    """Remove CSS blocks the shared engine emits that this chapter never had.

    The engine carries one page template for all four card-family analyses, so
    it always emits the table rules and the bar-chart rules. A chapter that
    lacked a block cannot match byte-for-byte until that block is subtracted.
    Each block must match exactly, so a block that drifts fails loudly instead
    of silently masking a regression.

    Each block sits between a blank line above and a blank line below in the
    engine's template, and the block text itself already ends with a newline.
    Removing the block together with its trailing blank-line newline leaves
    the single blank line a chapter without the block would have.
    """
    for block in blocks:
        assert block in html, f"engine no longer emits this block verbatim: {block[:60]!r}"
        html = html.replace(block + "\n", "", 1)
    return html


# The two blocks the engine always emits, as they appear in rendered output.
# Braces are singled here: PAGE doubles them for str.format, the output does not.
TABLE_CSS = """  table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: .78rem; }
  th, td { border: 1px solid var(--rule); padding: 6px 8px; text-align: left; vertical-align: top; }
  th { background: var(--stone-bg); font-size: .7rem; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); }
  td code { font-size: .92em; }
"""

GROUPCHART_CSS = """  .groupchart { background: var(--surface); border: 1px solid var(--rule); border-radius: var(--radius);
    box-shadow: var(--shadow); padding: 16px 20px; display: flex; flex-direction: column; gap: 7px; }
  .gc-row { display: flex; align-items: center; gap: 12px; }
  .gc-name { flex: 0 0 220px; font-size: .82rem; font-weight: 600; color: var(--text); text-align: right;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .gc-track { flex: 1; background: var(--stone-bg); border-radius: 5px; overflow: hidden; }
  .gc-bar { height: 22px; background: linear-gradient(90deg, #2dd4bf, var(--accent)); border-radius: 5px;
    color: #fff; font-size: .72rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;
    display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; min-width: 24px; }
  @media (max-width: 560px) { .gc-name { flex-basis: 110px; } }
"""


APP = '''\
from flask import Flask, jsonify, request

app = Flask(__name__)
NOTES = {}

@app.route("/notes", methods=["POST"])
def create_note():
    body = request.get_json()
    NOTES[body["id"]] = body["text"]
    return jsonify(ok=True)

@app.route("/notes/<note_id>")
def read_note(note_id):
    return jsonify(text=NOTES.get(note_id))
'''

MODELS = '''\
CREATE TABLE notes (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
'''

# One file per backend layer, laid out on the path conventions the crawlers key
# off: a route manifest at `urls.py`, `/views/` for handlers, `/services/` for
# business logic, `models.py` for the database layer, and a serializer for the
# response layer. Without these the layer counts are empty and a flow test
# proves nothing.
LAYERS = {
    "config/urls.py": '''\
from notes.views.notes import create_note, read_note

urlpatterns = [
    ("POST", "/notes", create_note),
    ("GET", "/notes/<note_id>", read_note),
]
''',
    "notes/middleware/auth.py": '''\
def require_token(handler):
    def wrapped(request, *args, **kwargs):
        if not request.headers.get("Authorization"):
            return {"error": "unauthorized"}, 401
        return handler(request, *args, **kwargs)
    return wrapped
''',
    "notes/views/notes.py": '''\
from notes.middleware.auth import require_token
from notes.serializers.note import serialize_note
from notes.services.notes import store_note, fetch_note

@require_token
def create_note(request):
    note = store_note(request.json["id"], request.json["text"])
    return serialize_note(note), 201

def read_note(request, note_id):
    return serialize_note(fetch_note(note_id)), 200
''',
    "notes/services/notes.py": '''\
from notes.models import Note

def store_note(note_id, text):
    note = Note(id=note_id, text=text)
    note.save()
    return note

def fetch_note(note_id):
    return Note.get(note_id)
''',
    "notes/models.py": '''\
class Note:
    """A single note row: id, body text, and its creation timestamp."""
    table = "notes"
    fields = ("id", "text", "created_at")

    def __init__(self, id, text, created_at=None):
        self.id, self.text, self.created_at = id, text, created_at

    def save(self):
        _ROWS[self.id] = self

    @classmethod
    def get(cls, note_id):
        return _ROWS.get(note_id)

_ROWS = {}
''',
    "notes/serializers/note.py": '''\
def serialize_note(note):
    if note is None:
        return {}
    return {"id": note.id, "text": note.text, "created_at": note.created_at}
''',
}

# Prisma-style timestamped names, the shape `schema_find.TIMESTAMP_RE` matches.
# Four of them, because MigrationActs declines to cluster fewer than four.
MIGRATIONS = {
    "notes/migrations/20240101120000_create_notes.sql": MODELS,
    "notes/migrations/20240310090000_add_created_at.sql":
        "ALTER TABLE notes ADD COLUMN created_at TIMESTAMP;\n",
    "notes/migrations/20240612093000_add_notes_owner.sql":
        "ALTER TABLE notes ADD COLUMN owner_id TEXT;\n",
    "notes/migrations/20241104150000_index_notes_owner.sql":
        "CREATE INDEX notes_owner_idx ON notes (owner_id);\n",
}

# The four sources the architecture bundle overlays: what the team runs, what it
# is configured to call, what it depends on, and the SDK import that proves the
# call is live.
INFRA = {
    "docker-compose.yml": '''\
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment: [DATABASE_URL, STRIPE_SECRET_KEY]
  db:
    image: postgres:16
  cache:
    image: redis:7
''',
    ".env.example": '''\
DATABASE_URL=
REDIS_URL=
STRIPE_SECRET_KEY=
''',
    "package.json": '''\
{
  "name": "notes-app",
  "dependencies": {"stripe": "^14.0.0", "ioredis": "^5.3.2"}
}
''',
    "notes/billing.js": '''\
import Stripe from 'stripe';

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
''',
}

# A feature that gets built and then killed, so the git-history graveyard pass
# has a real bulk deletion to read. `legacy` is not on the crawler's skip list,
# so it counts as a killed bet rather than vendored noise.
GRAVEYARD_FILES = [f"legacy/exports/report_{i}.py" for i in range(10)]


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True,
                   capture_output=True, text=True)


# Every module that holds its own `call_llm` name. `from crack.core import
# call_llm` binds the function into each importer, so patching one site is not
# enough — the fixture imports the whole set and patches each in turn.
LLM_MODULES = (
    "crack.core.llm",
    "crack.core.overview",
    "crack.analyses.architecture.nodes",
    "crack.analyses.backend.nodes",
    "crack.analyses.git_history.nodes",
    "crack.analyses.interfaces.nodes",
    "crack.analyses.product_intent.nodes",
    "crack.analyses.schema.nodes",
)

PROMPT_TAG = "<<{}>>\n"


@pytest.fixture
def stub_llm(monkeypatch):
    """Install a canned-reply stand-in for `call_llm` across every calling module.

    `reply(prompt) -> str` chooses what the model "said". Each analysis's
    `load_prompt` is wrapped to stamp the prompt's filename at the top of the
    text it returns, so a reply function can route on the file it came from
    while the file itself is still read off disk — a stale prompts directory
    still raises FileNotFoundError before any canned reply is reached.

    The provider keys are removed from the environment, so a call site this
    fixture failed to patch raises instead of quietly billing a real request.
    """
    def _install(reply):
        for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY",
                    "LLM_PROVIDER"):
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setattr(time, "sleep", lambda *_a, **_kw: None)

        prompts = []

        def fake_call_llm(prompt):
            prompts.append(prompt)
            return reply(prompt)

        def fake_call_image(prompt, output_path):
            raise AssertionError("the image model must not be called without a key")

        for name in LLM_MODULES:
            module = importlib.import_module(name)
            assert hasattr(module, "call_llm"), f"{name} no longer imports call_llm"
            monkeypatch.setattr(module, "call_llm", fake_call_llm)
            if hasattr(module, "call_image"):
                monkeypatch.setattr(module, "call_image", fake_call_image)
            if hasattr(module, "load_prompt"):
                original = module.load_prompt
                monkeypatch.setattr(
                    module, "load_prompt",
                    lambda name, _orig=original: PROMPT_TAG.format(name) + _orig(name))
        return prompts
    return _install


def _write(repo, rel, text):
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


@pytest.fixture(scope="session")
def fixture_repo(tmp_path_factory):
    """A small git repo shaped so every analysis's crawler finds something."""
    repo = tmp_path_factory.mktemp("notes-app")
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")

    (repo / "app.py").write_text(APP)
    for source in (LAYERS, INFRA):
        for rel, text in source.items():
            _write(repo, rel, text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "feat: notes API with create and read")

    (repo / "schema.sql").write_text(MODELS)
    for rel, text in MIGRATIONS.items():
        _write(repo, rel, text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "feat: persist notes in a table")

    for rel in GRAVEYARD_FILES:
        _write(repo, rel, f"def build_{os.path.basename(rel)[:-3]}():\n    return []\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "feat: scheduled CSV exports")

    for rel in GRAVEYARD_FILES:
        (repo / rel).unlink()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "chore: drop the CSV export pipeline, nobody used it")
    return str(repo)
