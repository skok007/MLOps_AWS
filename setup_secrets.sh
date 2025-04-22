#!/bin/bash

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

# Get the repository from git remote
REPO=$(git config --get remote.origin.url | sed 's/.*github.com[:/]//' | sed 's/\.git$//')
if [ -z "$REPO" ]; then
    echo "Error: Could not determine repository from git remote"
    exit 1
fi

echo "Setting GitHub secrets for repository: $REPO"

# Function to set a secret
set_secret() {
    local secret_name=$1
    local prompt_text=$2
    
    echo -n "$prompt_text: "
    read -s secret_value
    echo
    
    if [ ! -z "$secret_value" ]; then
        echo "Setting ${secret_name}..."
        echo "$secret_value" | gh secret set "$secret_name" -R "$REPO" -b -
    else
        echo "Warning: Empty value provided for ${secret_name}, skipping"
    fi
}

# Set all required secrets
set_secret "POSTGRES_USER" "Enter PostgreSQL username"
set_secret "POSTGRES_PASSWORD" "Enter PostgreSQL password"
set_secret "OPIK_API_KEY" "Enter Opik API key"
set_secret "OPIK_WORKSPACE" "Enter Opik workspace"
set_secret "OPIK_PROJECT_NAME" "Enter Opik project name"
set_secret "OPENAI_API_KEY" "Enter OpenAI API key"

echo "Done setting secrets!" 