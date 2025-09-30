#!/bin/bash
set -e

# This is a shared deployment script
# Usage: source this script after setting ENVIRONMENT and BRANCH variables

# Configuration
PROJECT_NAME="arkad-backend"

# Source secrets file if it exists
SECRETS_FILE="../secrets.sh"
if [ -f "$SECRETS_FILE" ]; then
  source "$SECRETS_FILE"
  echo "Loaded secrets from $SECRETS_FILE"
else
  echo "Warning: Secrets file not found at $SECRETS_FILE"
  exit 1
fi

# Validate required variables
if [ -z "$ENVIRONMENT" ]; then
  echo "Error: ENVIRONMENT variable not set"
  exit 1
fi

if [ -z "$BRANCH" ]; then
  echo "Error: BRANCH variable not set"
  exit 1
fi

if [ -z "$DOMAIN" ]; then
  echo "Error: DOMAIN variable not set"
  exit 1
fi

echo "Starting deployment for $PROJECT_NAME in $ENVIRONMENT environment..."

# Checkout and pull
git checkout "$BRANCH"
git pull

# Get the last commit hash
LAST_COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_MESSAGE=$(git log -1 --pretty=%B)

# Build and start containers
echo "Building Docker images..."
docker compose build

echo "Starting containers..."
docker compose restart nginx
docker compose up -d

# Get deployment status
if [ $? -eq 0 ]; then
  DEPLOY_STATUS="success"
  MESSAGE="✅ **$PROJECT_NAME** has been successfully deployed to **$ENVIRONMENT** ($DOMAIN).\nCommit: \`$LAST_COMMIT_HASH\`\nMessage: \`$COMMIT_MESSAGE\`"
else
  DEPLOY_STATUS="failure"
  MESSAGE="❌ Failed to deploy **$PROJECT_NAME** to **$ENVIRONMENT** ($DOMAIN).\nCommit: \`$LAST_COMMIT_HASH\`\nMessage: \`$COMMIT_MESSAGE\`"
fi

# Send Discord notification
echo "Sending deployment notification to Discord..."
curl -H "Content-Type: application/json" \
  -d "{\"content\": \"$MESSAGE\", \"username\": \"Deployment Bot\"}" \
  $DISCORD_WEBHOOK_URL

echo "Deployment script completed."
