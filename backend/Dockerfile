FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml alembic.ini ./
COPY app ./app
COPY pangaea_ai ./pangaea_ai
COPY migrations ./migrations
COPY scripts ./scripts
RUN pip install --no-cache-dir --editable ".[dev]"

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python -m scripts.seed_demo && exec python -m app.server"]
