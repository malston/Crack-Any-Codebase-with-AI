# crack

One command that reads a codebase six ways. Same prompts as the book's
chapter workflows, collapsed into one installable package.

## Install

```bash
pip install -e ".[dev,anthropic]"
export ANTHROPIC_API_KEY=sk-ant-...   # or OPENAI_API_KEY, or GEMINI_API_KEY
```

## Use

```bash
crack backend /path/to/repo            # one read
crack all /path/to/repo                # all six, plus a landing page
```

Reports land in `crack-output/<repo-name>/<analysis>/index.html`.

| Subcommand       | What it reads                                         |
| ---------------- | ----------------------------------------------------- |
| `product-intent` | the product story, reverse engineered from the source |
| `git-history`    | the roadmap already written in the git log            |
| `schema`         | the data model and how it migrated                    |
| `interfaces`     | the API surface and one action traced through it      |
| `architecture`   | the services and how a request crosses them           |
| `backend`        | the six layers every request flows through            |

Analysis-specific flags:

```bash
crack product-intent REPO --include 'src/**' --exclude '**/test/**'
crack git-history REPO --max-graves 3 --grave-min-files 12
crack schema REPO --schema db/schema.rb
```

## Relationship to the chapters

The `ch*/` folders are the book's teaching snapshots and are never
modified. This package is the deduplicated version of the same behavior:
one render engine, one runner, six thin analysis modules.
