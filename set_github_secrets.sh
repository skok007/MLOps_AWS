#!/bin/bash

# Exit on any error
set -e

# CONFIGURABLE VARIABLES
# Path to the .env file (adjust this if needed)
ENV_FILE_PATH="rag-app/.env" # <-- CHANGE this path if needed

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

# Check if .env file exists
if [ ! -f "$ENV_FILE_PATH" ]; then
    echo "Error: .env file not found at $ENV_FILE_PATH"
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

# Clean up the .env file for sourcing (remove spaces around '=')
CLEANED_ENV=$(mktemp)
sed 's/ *= */=/' "$ENV_FILE_PATH" > "$CLEANED_ENV"

# Load secrets from cleaned .env
echo "Loading secrets from $ENV_FILE_PATH (cleaned)..."
set -a
source "$CLEANED_ENV"
set +a
rm "$CLEANED_ENV"

# Function to set a secret if it exists
set_secret_from_env() {
    local secret_name=$1
    local secret_value=${!secret_name}

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
        echo "Warning: No value found for ${secret_name}, skipping"
        return 1
    fi
}

# List of secrets to set (add more here if needed)
SECRETS_LIST=(
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "OPIK_API_KEY"
    "OPIK_WORKSPACE"
    "OPIK_PROJECT_NAME"
    "OPENAI_API_KEY"
    "ARXIV_API_URL"
)

# Set all secrets
SECRETS_SET=0
for secret_name in "${SECRETS_LIST[@]}"; do
    set_secret_from_env "$secret_name" && SECRETS_SET=$((SECRETS_SET + 1))
done

if [ $SECRETS_SET -eq 0 ]; then
    echo "Error: No secrets were set."
    exit 1
else
    echo "Successfully set $SECRETS_SET secrets!"
fi