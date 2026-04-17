# LLM Agent Framework

[![CI](https://github.com/galak06/llm-agent-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/galak06/llm-agent-framework/actions/workflows/ci.yml)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)

**A generic, config-driven LLM agent framework with async job processing, multi-provider LLM support, guardrails, and an embeddable chat widget.**

## Architecture

```
Widget/API Client
    ↓ POST /api/v1/ask
FastAPI (middleware: rate limit, API key, request ID)
    ↓ guardrail check → enqueue
Redis Queue → Celery Worker
    ↓ build prompt (history + memory)
LLM Provider (Anthropic Claude / Google Gemini)
    ↓ response
Output Guardrail → Redis RunStore
    ↑ GET /api/v1/runs/{id}
Widget/API Client
```

## Features

- **Multi-provider LLM** — Switch between Anthropic and Gemini via `LLM_PROVIDER` env var
- **Async jobs** — POST /ask returns in <50ms with a run_id; client polls for results
- **Config-driven guardrails** — Injection and forbidden output patterns via env vars
- **Embeddable chat widget** — Single `<script>` tag, no build step
- **pgvector memory** — Semantic search over conversation history
- **SOLID architecture** — ServiceContainer with dependency injection
- **Security** — Timing-safe key comparison, Redis auth, bandit + pip-audit in CI
- **84 tests** — Unit + integration with 3-job CI pipeline (lint, test, security scan)

## Quick Start

```bash
git clone https://github.com/galak06/llm-agent-framework.git
cd llm-agent-framework
cp .env.example .env
# Edit .env — set LLM_PROVIDER, API keys, etc.
docker compose -f docker-compose.yml -f docker-compose.dev.yml build
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
# API: http://localhost:8000/api/v1/health
# Flower: http://localhost:5555
```

## LLM Provider Config

Set `LLM_PROVIDER` in `.env`:

| Provider | `LLM_PROVIDER` | `LLM_MODEL` | API Key Env |
|----------|----------------|-------------|-------------|
| Anthropic | `anthropic` | `claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |
| Google Gemini | `gemini` | `gemini-2.5-flash` | `GEMINI_API_KEY` |

## Widget Embed

The widget uses the [flowise-embed](https://github.com/FlowiseAI/FlowiseChatEmbed) web component and talks to this API's Flowise-compatible endpoint (`POST /api/v1/prediction/{chatflow_id}`).

```html
<script type="module">
  import Chatbot from 'https://cdn.jsdelivr.net/npm/flowise-embed/dist/web.js';
  Chatbot.init({
    chatflowid: 'nalla',
    apiHost: 'https://api.yourdomain.com',
    theme: {
      button: {
        backgroundColor: '#ff5f42',
        customIconSrc: '/widget/paw-white.svg',
      },
      chatWindow: {
        title: "Nalla's Dad",
        titleAvatarSrc: '/widget/paw-coral.svg',
        welcomeMessage: 'Hey! Ask me if any food is safe for your dog.',
        backgroundColor: '#FBFCFF',
        botMessage: { avatarSrc: '/widget/paw-coral.svg' },
        userMessage: { backgroundColor: '#ff5f42' },
        textInput: { sendButtonColor: '#ff5f42' },
      },
    },
  });
</script>
```

**Branding (Nalla / Dog Food & Fun):**
- Primary: `#ff5f42` (coral), Text: `#3a3a3a`, Background: `#FBFCFF`, Font: Poppins
- Paw icons served from `/widget/paw-white.svg` and `/widget/paw-coral.svg`

Preview locally: http://localhost:8000/widget/demo.html (served by the API in dev).

## Running Tests

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest tests/unit/ tests/integration/
```

## API Reference

| Method | Endpoint | Auth | Response |
|--------|----------|------|----------|
| POST | `/api/v1/ask` | `X-API-Key` | 202 `{ run_id, status_url }` |
| GET | `/api/v1/runs/{run_id}` | `X-API-Key` | 200 `RunStatusResponse` |
| POST | `/api/v1/prediction/{chatflow_id}` | None | 200 `{ text }` (Flowise-compatible, sync) |
| GET | `/api/v1/health` | None | 200 `HealthResponse` |
| GET | `/api/v1/admin/prompts` | `X-Admin-Key` | 200 `list[Prompt]` |
| PUT | `/api/v1/admin/prompts/{key}` | `X-Admin-Key` | 200 `Prompt` |
| GET | `/api/v1/admin/prompts/{key}` | `X-Admin-Key` | 200 `Prompt` |

## Adding a New Domain

1. Create `agents/{name}/seeds/prompts.json` with system prompts
2. Create `agents/{name}/router_config.json` with routing rules
3. Set domain-specific env vars (persona, guardrails, agent name)

## Environment Variables

See [`.env.example`](.env.example) for all configuration options.
