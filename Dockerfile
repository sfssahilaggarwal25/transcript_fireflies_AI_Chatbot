FROM python:3.12-slim

# supervisor runs FastAPI + Streamlit as two managed processes in one container
RUN apt-get update \
    && apt-get install -y --no-install-recommends supervisor \
    && rm -rf /var/lib/apt/lists/*

# uv: fast Python dependency installer
RUN pip install uv --quiet

WORKDIR /app

# Install deps first — layer is cached until pyproject.toml/uv.lock changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code and config
COPY . .

# Active venv is on the PATH
ENV PATH="/app/.venv/bin:$PATH"

# FastAPI webhook port + Streamlit UI port
EXPOSE 8000 8501

CMD ["supervisord", "-n", "-c", "/app/supervisord.conf"]
