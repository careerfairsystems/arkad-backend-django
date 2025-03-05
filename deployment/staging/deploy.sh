#!/bin/bash
set -e

# Configuration
# Source secrets file if it exists
SECRETS_FILE="../../../secrets.sh"
if [ -f "$SECRETS_FILE" ]; then
  source "$SECRETS_FILE"
  echo "Loaded secrets from $SECRETS_FILE"
else
  echo "Warning: Secrets file not found at $SECRETS_FILE"
  exit 1
fi
ENVIRONMENT="staging"
PROJECT_NAME="arkad-backend"

echo "Starting deployment for $PROJECT_NAME in $ENVIRONMENT environment..."

# Build and start containers
echo "Building Docker images..."
docker compose build

echo "Starting containers..."
docker compose up -d

# Get deployment status
if [ $? -eq 0 ]; then
  DEPLOY_STATUS="success"
  MESSAGE="✅ **$PROJECT_NAME** has been successfully deployed to **$ENVIRONMENT**."
else
  DEPLOY_STATUS="failure"
  MESSAGE="❌ Failed to deploy **$PROJECT_NAME** to **$ENVIRONMENT**."
fi

# Send Discord notification
echo "Sending deployment notification to Discord..."
curl -H "Content-Type: application/json" \
  -d "{\"content\": \"$MESSAGE\", \"username\": \"Deployment Bot\"}" \
  $DISCORD_WEBHOOK_URL

echo "Deployment script completed."

