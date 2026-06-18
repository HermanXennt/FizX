FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

FROM base AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/base.txt /app/requirements/base.txt
RUN pip install --user -r requirements/base.txt

FROM base AS final

RUN groupadd -r fizx && useradd -r -g fizx fizx

COPY --from=builder /root/.local /usr/local
COPY . /app

RUN mkdir -p /app/staticfiles /app/mediafiles && chown -R fizx:fizx /app

USER fizx

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
