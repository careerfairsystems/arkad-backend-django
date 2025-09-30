#!/bin/bash
set -e
# Change to the script directory
cd "$(dirname "$0")"
echo "Changed to script directory: $(pwd)"

# Configuration
# Source secrets file if it exists
SECRETS_FILE="../../secrets.sh"
if [ -f "$SECRETS_FILE" ]; then
  source "$SECRETS_FILE"
  echo "Loaded secrets from $SECRETS_FILE"
else
  echo "Warning: Secrets file not found at $SECRETS_FILE"
  exit 1
fi
ENVIRONMENT="production"
PROJECT_NAME="arkad-backend"
git checkout master

echo "Starting deployment for $PROJECT_NAME in $ENVIRONMENT environment..."
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
  MESSAGE="✅ **$PROJECT_NAME** has been successfully deployed to **$ENVIRONMENT** (backend.arkadtlth.se).\nCommit: \`$LAST_COMMIT_HASH\`\nMessage: \`$COMMIT_MESSAGE\`"
else
  DEPLOY_STATUS="failure"
  MESSAGE="❌ Failed to deploy **$PROJECT_NAME** to **$ENVIRONMENT** (backend.arkadtlth.se).\nCommit: \`$LAST_COMMIT_HASH\`\nMessage: \`$COMMIT_MESSAGE\`"
fi

# Send Discord notification
echo "Sending deployment notification to Discord..."
curl -H "Content-Type: application/json" \
  -d "{\"content\": \"$MESSAGE\", \"username\": \"Deployment Bot\"}" \
  $DISCORD_WEBHOOK_URL

echo "Deployment script completed."

