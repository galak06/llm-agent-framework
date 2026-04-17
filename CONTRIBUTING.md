# Contributing

Thanks for your interest in contributing! This project is a config-driven LLM agent framework — the goal is that new domains can be added without changing anything under `src/`.

## Quick Start

```bash
git clone https://github.com/galak06/llm-agent-framework.git
cd llm-agent-framework
cp .env.example .env   # edit API keys, passwords
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
curl http://localhost:8000/api/v1/health
```

## Development Environment

- **Package manager**: [`uv`](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Python**: 3.12+
- **Runtime**: Docker Compose (`docker-compose.dev.yml` hot-reloads `src/`, `agents/`, `widget/`)

Install deps and activate the virtualenv:
```bash
uv sync --all-extras
```

## Phase Gate (run before every push)

All four must pass:
```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest tests/unit/
```

CI runs the same commands plus security scans (`bandit`, `pip-audit`) and integration tests against Redis.

## Branch Naming

- `feat/<short-desc>` — new features
- `fix/<short-desc>` — bug fixes
- `refactor/<short-desc>` — internal restructure, no behavior change
- `chore/<short-desc>` — tooling, docs, CI, licensing
- `test/<short-desc>` — test-only changes

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(widget): add image upload button
fix(prediction): isolate session memory per visitor
test(integration): cover pgvector embeddings round-trip
docs(readme): add multi-agent deployment section
```

Scope should match the area of code (e.g. `widget`, `api`, `db`, `memory`, `jobs`, `agent`, `core`).

## Pull Requests

`main` is protected — PRs need **1 approving review** and **CI green** (`lint-and-typecheck`, `security-scan`, `test`) before merge.

Include in the PR body:
1. **Summary** — 1-3 bullets on what changed and why
2. **Test plan** — a checklist of what you verified (the phase gate plus any E2E steps)
3. **Out of scope** if applicable — especially for large milestones

Keep PRs focused: one concern per PR, split when a reviewer would reasonably ask you to.

## Code Style

- **Formatting**: single quotes (`ruff format` enforced), line length 99
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Type hints**: required on all exported functions; `mypy --strict` must pass
- **File size**: aim for under 300 lines per file. Split proactively as a file approaches 250 lines rather than reactively at 400.
- **Comments**: avoid. Let names and types carry the meaning. Only comment to explain *why* something non-obvious is so — never what code does.
- **No backwards-compat shims** for removed features. If something is dead, delete it.

## Adding a New Domain Agent

You can add a new subject (e.g., recipes, travel, legal Q&A) without touching `src/`:

1. Create `agents/<name>/seeds/prompts.json` with your system prompt
2. Create `agents/<name>/router_config.json` with routing rules
3. Create `agents/<name>/<name>.env.example` with domain-specific env vars (persona, guardrail patterns)
4. Set `AGENT_NAME=<name>` and `REDIS_KEY_PREFIX=<name>` in the deployment `.env`
5. Copy `widget/demo.html` and rebrand for the new domain

See the `agents/nalla/` folder for a full working example.

## Reporting Issues

Open a GitHub issue with:
- What you expected
- What happened instead
- Steps to reproduce
- Relevant logs / error messages (trim secrets!)

## Security

If you find a security issue, **do not open a public issue**. Email the maintainer directly at gilcohen06@gmail.com.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
