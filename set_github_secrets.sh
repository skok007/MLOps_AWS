#!/bin/bash

# Check if .env file exists
if [ ! -f "rag-app/.env" ]; then
    echo "Error: .env file not found in rag-app directory"
    echo "Please create a .env file in the rag-app directory with the required secrets"
    echo "Or use the setup_secrets.sh script to set secrets directly"
    exit 1
fi

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed"
    echo "Please install it with: brew install gh (macOS) or apt install gh (Ubuntu)"
    exit 1
fi

# Check if user is authenticated with GitHub
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub. Please run 'gh auth login' first"
    exit 1
fi

# Get the repository from git remote
REPO=$(git config --get remote.origin.url | sed 's/.*github.com[:/]//' | sed 's/\.git$//')
if [ -z "$REPO" ]; then
    echo "Error: Could not determine repository from git remote"
    echo "Please set the repository manually:"
    read -p "Enter repository (format: owner/repo): " REPO
    if [ -z "$REPO" ]; then
        echo "Error: No repository provided"
        exit 1
    fi
fi

echo "Setting GitHub secrets from .env file for repository: $REPO"

# Function to set secret if it exists in .env
set_secret_if_exists() {
    local secret_name=$1
    local value=$(grep "^${secret_name}=" rag-app/.env | cut -d '=' -f2- | tr -d '"' | tr -d "'")
    if [ ! -z "$value" ]; then
        echo "Setting ${secret_name}..."
        echo "$value" | gh secret set "$secret_name" -R "$REPO" -b -
        if [ $? -ne 0 ]; then
            echo "Error: Failed to set ${secret_name}"
            return 1
        fi
        echo "Successfully set ${secret_name}"
    else
        echo "Warning: ${secret_name} not found in .env file"
        return 1
    fi
}

# Set all required secrets
SECRETS_SET=0
set_secret_if_exists "POSTGRES_USER" && SECRETS_SET=$((SECRETS_SET + 1))
set_secret_if_exists "POSTGRES_PASSWORD" && SECRETS_SET=$((SECRETS_SET + 1))
set_secret_if_exists "OPIK_API_KEY" && SECRETS_SET=$((SECRETS_SET + 1))
set_secret_if_exists "OPIK_WORKSPACE" && SECRETS_SET=$((SECRETS_SET + 1))
set_secret_if_exists "OPIK_PROJECT_NAME" && SECRETS_SET=$((SECRETS_SET + 1))
set_secret_if_exists "OPENAI_API_KEY" && SECRETS_SET=$((SECRETS_SET + 1))

if [ $SECRETS_SET -eq 0 ]; then
    echo "Error: No secrets were set. Please check your .env file or use setup_secrets.sh"
    exit 1
else
    echo "Successfully set $SECRETS_SET secrets!"
fi 