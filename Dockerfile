# Build stage for frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

# Add build argument for API URL
ARG API_BASE_URL=http://localhost/api
ENV VITE_API_BASE_URL=$API_BASE_URL

COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Main application stage
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p logs data frontend/dist

# Copy application files
COPY server/ ./server/
COPY migrations/ ./migrations/
COPY *.json ./
COPY *.csv ./

# Copy frontend build from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist/ ./frontend/dist/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create data directories
RUN mkdir -p data/xml data/eva

# Command to run the server
CMD ["python", "-m", "server.app"] 