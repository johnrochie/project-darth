# Django Backend Dockerfile

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    libcairo2 \
    libpango-1.0-0 \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p media/reports

# Run migrations
RUN python manage.py migrate || echo "Migrations skipped"

# Collect static files
RUN python manage.py collectstatic --noinput || echo "Static files collection skipped"

# Expose ports
EXPOSE 8000

# Run with Daphne for ASGI (Channels)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "gaastats.asgi:application"]
