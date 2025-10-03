FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
  postgresql-client \
  build-essential \
  openssl \
  && rm -rf /var/lib/apt/lists/*

# Create private directory for JWT keys
WORKDIR /app
RUN mkdir arkad/private -p

# Create a directory for pre-generated keys
RUN mkdir /keys
# Generate JWT keys into the non-mounted directory
RUN openssl genpkey -algorithm RSA -out /keys/private.pem -pkeyopt rsa_keygen_bits:2048 && \
    openssl rsa -in /keys/private.pem -pubout -out /keys/public.pem

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Copy requirements file

COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

COPY . /app/arkad

WORKDIR /app/arkad
