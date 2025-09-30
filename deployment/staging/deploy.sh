#!/bin/bash
set -e

# Change to the script directory
cd "$(dirname "$0")/.."
echo "Changed to script directory: $(pwd)"

# Set environment-specific variables
export ENVIRONMENT="staging"
export BRANCH="staging"
export DOMAIN="staging.backend.arkadtlth.se"

# Source and run shared deployment script
source shared-deploy.sh
