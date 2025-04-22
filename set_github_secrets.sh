#!/bin/bash

# Check if .env file exists
if [ ! -f "rag-app/.env" ]; then
    echo "Error: .env file not found in rag-app directory"
    exit 1
fi

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed"
    exit 1
fi

# Check if user is authenticated with GitHub
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub. Please run 'gh auth login' first"
    exit 1
fi

# Set repository (using origin remote)
REPO="skok007/MLOps_AWS"
echo "Setting GitHub secrets from .env file for repository: $REPO"

# Function to set secret if it exists in .env
set_secret_if_exists() {
    local secret_name=$1
    local value=$(grep "^${secret_name}=" rag-app/.env | cut -d '=' -f2- | tr -d '"' | tr -d "'")
    if [ ! -z "$value" ]; then
        echo "Setting ${secret_name}..."
        echo "$value" | gh secret set "$secret_name" -R "$REPO" -b -
    else
        echo "Warning: ${secret_name} not found in .env file"
    fi
}

# Set all required secrets
set_secret_if_exists "POSTGRES_USER"
set_secret_if_exists "POSTGRES_PASSWORD"
set_secret_if_exists "OPIK_API_KEY"
set_secret_if_exists "OPIK_WORKSPACE"
set_secret_if_exists "OPIK_PROJECT_NAME"
set_secret_if_exists "OPENAI_API_KEY"

echo "Done setting secrets!" 