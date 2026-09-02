"""git-history keeps its own renderer, so parity is byte-identical."""
import argparse
from crack.analyses import git_history
from crack.core import render

SHARED = {
    "repo_path": "/tmp/redis",
    "commits": [{"hash": "abc1234", "date": "2011-01-02", "month": "2011-01", "subject": "init"}] * 4,
    "eras": [
        {"name": "The cache years", "start": "2009-01", "end": "2012-06",
         "description": "It began as a cache.",
         "diagram": "graph LR;\ncache-->disk;",
         "turning_point": "Persistence landed.", "turning_point_hash": "abc1234"},
        {"name": "The data structure server", "start": "2012-07", "end": None,
         "description": "Types multiplied.", "diagram": "",
         "turning_point": "", "turning_point_hash": ""},
    ],
    "profiles": [
        {"era": {"name": "The cache years"}, "commit_count": 900,
         "profile": {"cast": {"contributors": [{"name": "antirez", "pct": 82, "note": "Most of it."}]},
                     "mood": {"patterns": [{"label": "Features", "pct": 60, "note": "New types."}]}}},
        {"era": {"name": "The data structure server"}, "commit_count": 2400,
         "profile": {"cast": {"contributors": [{"name": "core team", "pct": 55, "note": "Shared."}]},
                     "mood": {"patterns": [{"label": "Hardening", "pct": 70, "note": "Fewer bugs."}]}}},
    ],
    "graves": [
        {"entry_md": "### Diskstore\nAn on-disk backend, removed.",
         "commit": {"hash": "def5678abc", "date": "2011-08-01", "count": 22,
                    "scope": "src", "subject": "Remove diskstore backend"},
         "era": {"name": "The cache years"}},
    ],
    "overview": {"welcome": "Redis grew from a cache into a data structure server.",
                 "intros": {"The eras": "Read oldest first.",
                            "Cast & mood": "Who drove each era.",
                            "The graveyard": "The bets they walked away from."}},
}

# Security fix: the engine HTML-escapes mermaid diagram source before writing
# it into <pre class="mermaid">, closing an HTML-injection hole. ch06 keeps
# the vulnerable unescaped form. This rewrites only the benign "-->" the
# fixture diagram contains, not a general whitespace/HTML normalisation.
_CHAPTER_DIAGRAM = "graph LR;\ncache-->disk;"
_ENGINE_DIAGRAM = "graph LR;\ncache--&gt;disk;"

def test_html_is_byte_identical_to_chapter(chapter_render):
    chapter = chapter_render("ch06-git-history")
    expected = chapter.render_html("redis", SHARED).replace(_CHAPTER_DIAGRAM, _ENGINE_DIAGRAM)
    assert render.render_html(git_history, "redis", SHARED) == expected

def test_markdown_is_byte_identical_to_chapter(chapter_render):
    chapter = chapter_render("ch06-git-history")
    assert render.render_markdown(git_history, "redis", SHARED) == \
        chapter.render_markdown("redis", SHARED)

def test_engine_defers_to_the_custom_renderer():
    assert not hasattr(git_history, "SECTIONS")
    assert hasattr(git_history, "render_html")

def test_grave_flags_reach_shared():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path")
    git_history.add_arguments(parser)
    args = parser.parse_args(["/tmp/x", "--max-graves", "3", "--grave-min-files", "12"])
    shared = git_history.init_shared(args, "/out")
    assert shared["max_graves"] == 3
    assert shared["grave_min_files"] == 12

def test_grave_flag_defaults_match_the_chapter():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path")
    git_history.add_arguments(parser)
    args = parser.parse_args(["/tmp/x"])
    shared = git_history.init_shared(args, "/out")
    assert shared["max_graves"] == 6
    assert shared["grave_min_files"] == 8
