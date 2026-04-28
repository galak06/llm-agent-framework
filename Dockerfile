FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ src/
COPY agents/ agents/
COPY alembic/ alembic/
COPY alembic.ini ./
COPY scripts/ scripts/
COPY widget/ widget/

RUN groupadd -r app \
 && useradd -r -g app -d /app -s /sbin/nologin app \
 && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
