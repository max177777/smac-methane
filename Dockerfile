FROM python:3.11-slim

# Streamlit needs these for some optional deps (fonts, etc.) but keep the image small
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render and Railway both inject a $PORT env var at runtime — Streamlit must
# bind to it, not to a hardcoded port, or the platform's health check will
# never see the app come up.
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8080

CMD streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0
