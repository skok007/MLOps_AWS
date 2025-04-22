#!/bin/bash

# Exit on any error
set -e

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed"
    echo "Please install it with: brew install gh (macOS) or apt install gh (Ubuntu)"
    exit 1
fi

# Check if user is authenticated with GitHub
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub"
    echo "Please run 'gh auth login' first"
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

echo "Setting GitHub secrets for repository: $REPO"

# Function to securely set a secret
set_secret() {
    local secret_name=$1
    local prompt_text=$2
    
    # Use -s flag for secure input
    echo -n "$prompt_text: "
    read -s secret_value
    echo
    
    if [ ! -z "$secret_value" ]; then
        echo "Setting ${secret_name}..."
        printf "%s" "$secret_value" | gh secret set "$secret_name" -R "$REPO" -b -
        if [ $? -ne 0 ]; then
            echo "Error: Failed to set ${secret_name}"
            return 1
        fi
        echo "Successfully set ${secret_name}"
        return 0
    else
        echo "Warning: Empty value provided for ${secret_name}, skipping"
        return 1
    fi
}

# Set all required secrets
SECRETS_SET=0
set_secret "POSTGRES_USER" "Enter PostgreSQL username" && SECRETS_SET=$((SECRETS_SET + 1))
set_secret "POSTGRES_PASSWORD" "Enter PostgreSQL password" && SECRETS_SET=$((SECRETS_SET + 1))
set_secret "OPIK_API_KEY" "Enter Opik API key" && SECRETS_SET=$((SECRETS_SET + 1))
set_secret "OPIK_WORKSPACE" "Enter Opik workspace" && SECRETS_SET=$((SECRETS_SET + 1))
set_secret "OPIK_PROJECT_NAME" "Enter Opik project name" && SECRETS_SET=$((SECRETS_SET + 1))
set_secret "OPENAI_API_KEY" "Enter OpenAI API key" && SECRETS_SET=$((SECRETS_SET + 1))

if [ $SECRETS_SET -eq 0 ]; then
    echo "Error: No secrets were set."
    exit 1
else
    echo "Successfully set $SECRETS_SET secrets!"
fi 