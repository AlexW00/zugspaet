# Build stage for frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

# Add build arguments for API URL and Ackee tracking
ARG API_BASE_URL=http://localhost/api
ARG ACKEE_SERVER_URL=""
ARG ACKEE_DOMAIN_ID=""
ENV VITE_API_BASE_URL=$API_BASE_URL
ENV VITE_ACKEE_SERVER_URL=$ACKEE_SERVER_URL
ENV VITE_ACKEE_DOMAIN_ID=$ACKEE_DOMAIN_ID

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
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py ./
COPY migrations/ ./migrations/
COPY *.json ./
COPY *.csv ./

# Copy frontend build from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist/ ./frontend/dist/

# Copy environment injection script
COPY --from=frontend-builder /app/frontend/scripts/inject-env.js ./scripts/

# Set environment variables
ENV FLASK_APP=server.py
ENV PYTHONUNBUFFERED=1

# Create logs directory
RUN mkdir -p logs

# Command to run the server
CMD ["sh", "-c", "node ./scripts/inject-env.js && python server.py"] 
