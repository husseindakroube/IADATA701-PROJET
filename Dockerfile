FROM ghcr.io/astral-sh/uv:0.12.13 AS uv
FROM python:3.12.14-slim-bookworm

COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLBACKEND=Agg \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev
COPY app ./app
COPY .streamlit ./.streamlit
COPY images ./images
COPY data ./data
COPY docs ./docs
COPY notebooks ./notebooks
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/logs && chown appuser:appuser /app/logs
USER appuser
EXPOSE 8501
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=6 \
    CMD ["/app/.venv/bin/python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4)"]
CMD ["/app/.venv/bin/streamlit", "run", "app/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
