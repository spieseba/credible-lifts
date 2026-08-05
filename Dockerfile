# Get Debian 13 (trixie) image with uv preinstalled
FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim

# Setup workspace
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --locked

# Launch API server
CMD ["uv", "run", "fastapi", "run", "src/credible_lifts/api.py", "--port", "8000"]