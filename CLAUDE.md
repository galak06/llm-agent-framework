# LLM Agent Framework — CLAUDE.md

## PRD
Full spec is in `llm_agent_framework_prd_v4.docx` at the project root.

## What's Built (All 12 Phases Scaffolded)

### Phase 0 — Init (DONE)
- `.gitignore`, `.claudeignore`, `pyproject.toml`, `.env.example`, `README.md`
- Full directory structure with all `__init__.py` files
- `agents/nalla/` domain config: `router_config.json`, `seeds/prompts.json`, `nalla.env.example`

### Phase 1 — Core (DONE)
- `src/core/config.py` — Settings class, fully env-driven, `get_settings()` with lru_cache
- `src/core/exceptions.py` — Full exception hierarchy (10 exception classes)
- `src/core/logging.py` — structlog JSON config + Langfuse factory
- `src/core/security.py` — `sanitize_input()` strips null bytes, HTML, control chars, truncates
- `src/core/dependencies.py` — FastAPI `SettingsDep`

### Phase 2 — Domain (DONE)
- `src/domain/schemas.py` — All enums (Role, RunStatus, ServiceStatus) and models (AskRequest, AskResponse, RunStatusResponse, HealthResponse, Message, ToolResult, AgentRunResult, GuardrailResult)

### Phase 3 — Tools (DONE)
- `src/tools/base.py` — `BaseTool` Protocol with `version` field + `versioned_name` property
- `src/tools/registry.py` — `ToolRegistry` with versioned logging
- `agents/nalla/tools/ingredient_checker.py` — skeleton (NotImplementedError)
- `agents/nalla/tools/safety_lookup.py` — skeleton (NotImplementedError)

### Phase 4 — Guardrails (DONE, fully implemented)
- `src/agent/guardrails.py` — `GuardrailEngine` with `check_input()` and `check_output()`, patterns from config

### Phase 5 — Router (DONE, fully implemented)
- `src/agent/router.py` — `AgentRouter` Protocol + `ConfigRouter` (keyword match, first-wins, fallback to default)

### Phase 6 — Database (DONE)
- `src/db/models.py` — SQLAlchemy models: Conversation, ConversationMessage, AgentRun (with ARRAY tools_used), Prompt
- `src/db/engine.py` — async engine + session factory
- `src/db/repositories/base.py`, `conversation.py`, `prompt.py` — fully implemented
- `alembic/env.py` + `alembic.ini` — async migration setup (no migrations generated yet)

### Phase 7 — Memory (DONE)
- `src/memory/interfaces.py` — `MemoryReader` and `MemoryWriter` Protocols
- `src/memory/session.py` — `RedisSessionMemory` (fully implemented)
- `src/memory/vector_store.py` — `PgVectorMemory` (skeleton, NotImplementedError)

### Phase 8 — Jobs (DONE)
- `src/jobs/worker.py` — Celery app factory (`create_celery_app()`)
- `src/jobs/tasks.py` — `run_agent_task` (skeleton, NotImplementedError)
- `src/jobs/result_store.py` — `RunResultStore` (fully implemented, Redis-backed)

### Phase 9 — Agent (DONE)
- `src/agent/llm_client.py` — `LLMClient` wrapping Anthropic AsyncAnthropic SDK (fully implemented)
- `src/agent/prompt_builder.py` — `PromptBuilder` with history + memory search (fully implemented)
- `src/agent/orchestrator.py` — `AgentOrchestrator` main loop: guardrail → prompt → LLM → tool_use → repeat (fully implemented)

### Phase 10 — API (DONE)
- `src/api/app.py` — `create_app()` factory with middleware stack + route registration
- `src/api/v1/routes/chat.py` — `POST /ask` (202 + enqueue), `GET /runs/{run_id}` (poll)
- `src/api/v1/routes/health.py` — `GET /health` deep check
- `src/api/v1/routes/admin.py` — `GET/PUT /admin/prompts` (skeleton, NotImplementedError)
- `src/api/v1/middleware/request_id.py` — X-Request-ID (fully implemented)
- `src/api/v1/middleware/api_key.py` — X-API-Key widget + admin auth (fully implemented)
- `src/api/v1/middleware/rate_limit.py` — Redis sliding window (fully implemented)

### Phase 11 — Infra (DONE)
- `Dockerfile` — Python 3.12-slim + uv
- `docker-compose.yml` — api, worker, flower, redis
- `docker-compose.dev.yml` — hot reload, volume mounts
- `.github/workflows/ci.yml` — ruff + mypy + pytest with Redis service
- `.github/workflows/deploy.yml` — SSH deploy to VPS on merge to main
- `scripts/seed_prompts.py`, `scripts/healthcheck.py`

### Phase 12 — Evals & Tests (DONE)
- `tests/evals/eval_runner.py` + `tests/evals/cases/nalla.json` (15 eval cases)
- 57 unit + integration tests — ALL PASSING
- Integration tests are placeholders (need running Redis/DB)

## What Still Needs Implementation

These files have `raise NotImplementedError` in method bodies:

| File | What's Missing |
|------|---------------|
| `agents/nalla/tools/ingredient_checker.py` | `get_schema()`, `execute()` — domain tool logic |
| `agents/nalla/tools/safety_lookup.py` | `get_schema()`, `execute()` — domain tool logic |
| `src/memory/vector_store.py` | All methods — needs pgvector/Supabase integration |
| ~~`src/jobs/tasks.py`~~ | ~~`run_agent_task()` — wire up orchestrator inside Celery task~~ DONE |
| `src/api/v1/routes/admin.py` | `list_prompts()`, `update_prompt()` — wire up PromptRepository |

## Next Steps (in order)

1. ~~**Run `uv run mypy src/` and fix all strict-mode type errors**~~ — DONE
2. ~~**Implement `src/jobs/tasks.py` → `run_agent_task()`**~~ — DONE
3. **Implement `src/api/v1/routes/admin.py`** — connect `list_prompts()` and `update_prompt()` to PromptRepository with a DB session dependency
4. **Implement `agents/nalla/tools/ingredient_checker.py`** — `get_schema()` should return Anthropic tool JSON schema, `execute()` should contain the domain logic for checking dog food ingredient safety
5. **Implement `agents/nalla/tools/safety_lookup.py`** — same pattern as ingredient_checker
6. **Implement `src/memory/vector_store.py`** — connect to pgvector/Supabase for semantic search over conversation history
7. **Generate first Alembic migration** — `uv run alembic revision --autogenerate -m "initial tables"` (requires DATABASE_URL in .env)
8. **Replace integration test placeholders** with real tests that hit Redis and the API
9. **Push to GitHub, set up branch protection, configure secrets** per PRD Section 4.3 and 5.3
10. **Run eval suite** against a live agent to validate the 15 Nalla test cases

### Phase gate rule
Before each step: `uv run ruff check . && uv run ruff format --check . && uv run mypy src/ && uv run pytest tests/unit/` must all pass.

## Verification Status
- `uv run ruff check .` — CLEAN
- `uv run ruff format --check .` — CLEAN
- `uv run pytest tests/unit/ tests/integration/` — 57/57 PASSED
- `uv run mypy src/` — CLEAN (strict mode, 44 source files)

## Tooling
- Package manager: **uv** (installed at `~/.local/bin/uv`)
- Python: 3.14 (via uv venv)
- Linter/formatter: ruff
- Type checker: mypy (strict)
- Tests: pytest + pytest-asyncio + pytest-cov

## Conventions
- Single quotes (ruff format enforced)
- snake_case functions/variables, PascalCase classes
- All config from env vars via `Settings` — zero hardcoding in `src/`
- Conventional commits: `feat(scope):`, `fix(scope):`, `test(scope):`, etc.
- Branch naming: `phase/{N}-{name}`, `feat/{desc}`, `fix/{desc}`
