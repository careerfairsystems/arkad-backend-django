# Use Python 3.11 slim image as base
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  postgresql-client \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# # Collect static files
# RUN python arkad/manage.py collectstatic --noinput

# Copy and set permissions for entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copy the custom Nginx config file into the container
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 8000 for Gunicorn and port 80 for Nginx
EXPOSE 8000 80
# Set entrypoint
CMD service nginx start
WORKDIR /app/arkad
ENTRYPOINT ["docker-entrypoint.sh"]

