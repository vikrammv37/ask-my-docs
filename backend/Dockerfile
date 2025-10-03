# Backend Dockerfile for Render
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads vector_db

# Use PORT environment variable from Render
EXPOSE $PORT

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
