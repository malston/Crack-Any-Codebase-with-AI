"""product-intent keeps its own renderer, so parity is byte-identical."""
import argparse
import os
from crack.analyses import product_intent
from crack.core import render

SHARED = {
    "repo_path": "/tmp/tigerbeetle",
    "variant": "A database that only does double-entry accounting.",
    "pain": "General ledgers on general databases lose money under contention.",
    "positioning": {
        "sacrifices": ["General queries", "Ad-hoc schema"],
        "gains": ["Contention-free transfers", "Deterministic replay"],
        "why_incumbents_cannot_copy": "Postgres cannot drop general SQL.",
        "diagram": "graph TD;\ngeneral-->slow;",
        "dimensions": [
            {"name": "Throughput", "definition": "Transfers per second."},
            {"name": "Generality", "definition": "How many shapes it stores."},
        ],
        "competitors": [
            {"name": "TigerBeetle",
             "cells": [{"verdict": "Very high", "detail": "Batched."},
                       {"verdict": "Narrow", "detail": "Ledgers only."}]},
            {"name": "Postgres",
             "cells": [{"verdict": "Moderate", "detail": "Row locks."},
                       {"verdict": "Broad", "detail": "Anything."}]},
        ],
    },
    "surprises": {
        "present": [{"headline": "Deterministic simulation",
                     "where": "src/testing/", "bet": "Correctness sells."}],
        "absent": [{"headline": "No SQL parser",
                    "evidence": "No parser directory.",
                    "tradeoff": "Narrowness is the product."}],
    },
}

# Security fix: the engine HTML-escapes the trap-diagram mermaid source
# before writing it into <pre class="mermaid">, closing an HTML-injection
# hole. ch05 keeps the vulnerable unescaped form. This rewrites only the
# benign "-->" the fixture diagram contains, not a general normalisation.
_CHAPTER_DIAGRAM = "graph TD;\ngeneral-->slow;"
_ENGINE_DIAGRAM = "graph TD;\ngeneral--&gt;slow;"

def test_html_is_byte_identical_to_chapter(chapter_render):
    chapter = chapter_render("ch05-product-intent")
    expected = chapter.render_html("tigerbeetle", SHARED).replace(_CHAPTER_DIAGRAM, _ENGINE_DIAGRAM)
    assert render.render_html(product_intent, "tigerbeetle", SHARED) == expected

def test_markdown_is_byte_identical_to_chapter(chapter_render):
    chapter = chapter_render("ch05-product-intent")
    assert render.render_markdown(product_intent, "tigerbeetle", SHARED) == \
        chapter.render_markdown("tigerbeetle", SHARED)

def test_init_shared_points_the_image_at_the_output_dir():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path")
    product_intent.add_arguments(parser)
    args = parser.parse_args(["/tmp/tb"])
    shared = product_intent.init_shared(args, "/out/tb/product-intent")
    assert shared["pain_image_path_target"] == os.path.join(
        "/out/tb/product-intent", "pain.png")

def test_include_and_exclude_reach_shared():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_path")
    product_intent.add_arguments(parser)
    args = parser.parse_args(["/tmp/tb", "--include", "src/**",
                              "--exclude", "**/test/**"])
    shared = product_intent.init_shared(args, "/out")
    assert shared["include"] == ["src/**"]
    assert shared["exclude"] == ["**/test/**"]

def test_engine_defers_to_the_custom_renderer():
    assert not hasattr(product_intent, "SECTIONS")
    assert hasattr(product_intent, "render_html")
