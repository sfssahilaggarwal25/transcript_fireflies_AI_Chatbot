FROM python:3.12-slim

# System dependencies needed by chromadb / onnxruntime
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer-cached)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full project (includes chroma_db/ with pre-built vector index)
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Health-check so Railway knows the app is ready
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the agent Streamlit app
CMD ["streamlit", "run", "app/agent/streamlit_app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
