# Dockerfile — Dana Application
FROM --platform=linux/amd64 python:3.12-slim

# Build arguments for versioning
ARG VERSION=latest
ARG BRANCH=main

# Build arguments for API keys (removed - will be set at runtime)

# Install system dependencies including Node.js 20 and OpenCV dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        gnupg \
        tini \
        git \
        build-essential \
        # OpenCV and graphics dependencies for aicapture
        libgl1 \
        libgl1-mesa-dri \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libgomp1 \
        libgthread-2.0-0 \
        libgtk-3-0 \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libv4l-dev \
        libxvidcore-dev \
        libx264-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libopenblas-dev \
        python3-dev \
        python3-numpy \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install uv for Python package management
RUN pip install --no-cache-dir uv

# Copy application code
COPY . /app/

# Install Python dependencies
RUN uv sync

# Set environment variables for frontend API URL and version info
ENV VITE_API_BASE_URL=/api
ENV VITE_WS_BASE_URL=/ws
ENV DANA_VERSION=${VERSION}
ENV DANA_BRANCH=${BRANCH}

# API keys will be set at runtime via environment variables or .env files

# Expose application port
EXPOSE 8201

# No default command - will be specified in docker-compose