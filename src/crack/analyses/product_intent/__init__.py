"""Reverse engineer the product story from the source (ch05)."""
import os

from pocketflow import Flow

from .nodes import (FetchRepo, PainScene, VariantSentence,
                    CompetitivePositioning, IllustratePain,
                    SurprisesAndAbsences)
# This analysis hand-builds its page from structured data, so it keeps its own
# renderer; crack.core.render defers to these.
from .render import render_html, render_markdown  # noqa: F401

NAME = "product-intent"

ENV_DEFAULTS = {}

def add_arguments(parser):
    parser.add_argument("--include", action="append", default=[],
                        help=".gitignore-style pattern: keep only matching "
                             "paths. Repeatable.")
    parser.add_argument("--exclude", action="append", default=[],
                        help=".gitignore-style pattern: drop matching paths. "
                             "Repeatable.")

def init_shared(args, out_dir):
    """IllustratePain writes the generated image beside the report."""
    return {
        "repo_path": args.repo_path,
        "include": list(getattr(args, "include", []) or []),
        "exclude": list(getattr(args, "exclude", []) or []),
        "pain_image_path_target": os.path.join(out_dir, "pain.png"),
    }

def build_flow():
    fetch, pain = FetchRepo(), PainScene()
    variant, illustrate = VariantSentence(), IllustratePain()
    positioning, surprises = CompetitivePositioning(), SurprisesAndAbsences()
    fetch >> pain >> variant >> illustrate >> positioning >> surprises
    return Flow(start=fetch)
