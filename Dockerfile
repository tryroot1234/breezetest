# BreezeTest Docker Image
# Usage:
#   docker build -t breezetest .
#   docker run -v ./tests:/app/tests breezetest run /app/tests
#
# Or with docker-compose:
#   docker compose run breezetest run /app/tests

FROM python:3.12-slim AS base

# System dependencies for Playwright/Chromium on Debian Bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libwayland-client0 \
    fonts-liberation \
    fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install BreezeTest
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/
RUN pip install --no-cache-dir . && \
    rm -rf /root/.cache /tmp/*

# Install Playwright Chromium
RUN playwright install --with-deps chromium && \
    playwright install-deps chromium && \
    rm -rf /root/.cache /tmp/*

# Create non-root user (Chromium warns when run as root)
RUN groupadd -r breezetest && \
    useradd -r -g breezetest -d /app -s /bin/bash breezetest && \
    chown -R breezetest:breezetest /app

USER breezetest

HEALTHCHECK --interval=30s --timeout=10s --retries=2 \
    CMD breeze --version || exit 1

ENTRYPOINT ["breeze"]
CMD ["--help"]
