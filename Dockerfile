FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./

ENV UV_PROJECT_ENVIRONMENT="/opt/.venv"

RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim-bookworm as production

WORKDIR /app

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

COPY --from=builder --chown=appuser:appgroup /opt/.venv /opt/.venv

COPY --chown=appuser:appgroup . .

ENV PATH="/opt/.venv/bin:$PATH"

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "src.main:app", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--log-level", "info"]
