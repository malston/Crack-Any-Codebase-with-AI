"""One command that reads a codebase six ways."""
import argparse
import os
import sys

from .analyses import ANALYSIS_NAMES, load
from .core.index import write_index
from .core.runner import run_analysis, repo_name_of

DEFAULT_OUT_ROOT = "crack-output"

DESCRIPTIONS = {
    "product-intent": "reverse engineer the product story from the source",
    "git-history": "read the roadmap already written in the git log",
    "schema": "tour the data model and how it migrated",
    "interfaces": "map the API surface and trace one action",
    "architecture": "map a multi-service architecture in three passes",
    "backend": "read a backend as the six layers every request flows through",
}

def _add_common(parser):
    parser.add_argument("repo_path", help="path to the repository to read")
    parser.add_argument("--out", default=DEFAULT_OUT_ROOT,
                        help=f"output root (default: {DEFAULT_OUT_ROOT}/)")

def build_parser():
    parser = argparse.ArgumentParser(
        prog="crack", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    subs = parser.add_subparsers(dest="command", required=True)

    for name in ANALYSIS_NAMES:
        sub = subs.add_parser(name, help=DESCRIPTIONS[name])
        _add_common(sub)
        _add_analysis_arguments(sub, name)

    every = subs.add_parser("all", help="run all six analyses on one repo")
    _add_common(every)
    for name in ANALYSIS_NAMES:
        _add_analysis_arguments(every, name)
    return parser

def _add_analysis_arguments(parser, name):
    """Let an analysis add its own flags. Import failures must not break --help."""
    try:
        analysis = load(name)
    except ModuleNotFoundError:
        return
    add = getattr(analysis, "add_arguments", None)
    if add is not None:
        add(parser)

def main(argv=None):
    args = build_parser().parse_args(argv)

    if not os.path.isdir(args.repo_path):
        print(f"crack: {args.repo_path} is not a directory", file=sys.stderr)
        return 2

    names = ANALYSIS_NAMES if args.command == "all" else (args.command,)
    written, failed = {}, []

    for name in names:
        analysis = load(name)
        print(f"\n=== {name} ===")
        try:
            written[name] = run_analysis(analysis, args.repo_path, args.out, args)
        except Exception as exc:               # one analysis must not stop the rest
            if args.command != "all":
                raise
            failed.append((name, exc))
            print(f"crack: {name} failed: {exc}", file=sys.stderr)

    if args.command == "all":
        root = os.path.join(args.out, repo_name_of(args.repo_path))
        index = write_index(root, repo_name_of(args.repo_path), written, failed)
        print(f"\nWrote {index}")

    for path in written.values():
        print(f"  Open {os.path.join(path, 'index.html')}")

    return 1 if failed else 0

if __name__ == "__main__":
    raise SystemExit(main())
