FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && \
    uv export --no-dev --format=requirements-txt > requirements.txt && \
    pip install --no-cache-dir -r requirements.txt gunicorn

FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

COPY . .

RUN mkdir -p /app/static /app/media && \
    DJANGO_SECRET_KEY=dummy \
    DJANGO_DEBUG=False \
    DB_HOST=localhost \
    python manage.py collectstatic --noinput || true

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "codiselu.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
