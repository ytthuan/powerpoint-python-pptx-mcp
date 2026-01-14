FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies for Pillow/lxml and build tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libjpeg-dev \
        zlib1g-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libopenjp2-7-dev \
        libtiff-dev \
        libwebp-dev \
        libxml2-dev \
        libxslt1-dev \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY requirements.txt pyproject.toml README.md ./
COPY src ./src
COPY docs ./docs
COPY examples ./examples

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir -r requirements.txt \
    && python3 -m pip install --no-cache-dir .

# Default workspace/search paths inside the container
ENV MCP_WORKSPACE_DIRS=/workspace/desks
ENV MCP_RESOURCE_SEARCH_PATHS=/workspace/desks
ENV PYTHONPATH=/app/src

CMD ["python3", "-m", "mcp_server.server"]

