FROM python:3.12.11-slim

WORKDIR /app

# Install first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy only what the API needs (avoid shipping huge gallery LFS media).
COPY server.py config.js ./
COPY api ./api
COPY *.html ./
COPY styles.css app.js ./
COPY assets ./assets
COPY coaches ./coaches

ENV HOST=0.0.0.0
ENV PORT=8000
ENV DATA_DIR=./data
ENV CORS_ORIGINS=https://fitnessgurukul.co.in,https://www.fitnessgurukul.co.in,https://fitnessgurukul.in,https://www.fitnessgurukul.in

RUN mkdir -p /app/data
EXPOSE 8000
CMD ["python", "-u", "server.py"]
